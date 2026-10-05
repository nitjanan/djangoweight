# -*- coding: utf-8 -*-
"""หน้า จัดการต้นทาง / ปลายทาง : CRUD ตาราง base_company_map_base_customer + รหัสลูกค้าสำรอง

เข้าจากปุ่มในหน้า /internationalFreightRate/
แถวในตารางนี้คือตัวเลือกต้นทาง/ปลายทางของใบราคาค่าขนส่ง และธง "ใช้เป็นปลายทางส่งออก"
เป็นตัวกำหนดว่าเที่ยวไหนเข้าหน้า /exportDocument/ แก้ผิดทีเดียวเที่ยวหายทั้งก้อน
จึงให้เข้าได้เฉพาะคนที่มีสิทธิ์แก้ตารางนี้ (ตั้งในหน้า admin) ไม่ใช่ทุกคนที่ล็อกอิน
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from weightapp.forms import CompanyMapAliasFormSet, CompanyMapForm, customerChoiceLabel
from weightapp.models import (EXPORT_DOC_OWN_PORT_CUSTOMERS_CACHE_KEY, BaseCompanyMapBaseCustomer,
                              BaseCompanyMapCustomerAlias, BaseCustomer, InternationalFreightRate)

PERM_CHANGE = 'weightapp.change_basecompanymapbasecustomer'
PERM_DELETE = 'weightapp.delete_basecompanymapbasecustomer'

COMPANY_MAP_FILTERS = (
    ('', 'ทั้งหมด'),
    ('export', 'ใช้เป็นปลายทางส่งออก'),
    ('domestic', 'ใช้เป็นปลายทางในประเทศ'),
    ('none', 'ไม่ได้ติ๊กปลายทาง'),
    ('incomplete', 'ติ๊กปลายทางแต่ไม่มีรหัสลูกค้า'),
)
CUSTOMER_SEARCH_LIMIT = 30


def _activeCompany(request):
    """แท็ปบริษัทที่เลือกอยู่ (base.html ใช้ไฮไลต์) ไม่มี = session หลุด ให้ล็อกอินใหม่"""
    return request.session.get('company_code')


def _clearOwnPortCache():
    # หน้า /exportDocument/ cache "รหัสลูกค้าที่เป็นท่าเรือเรา" ไว้ 1 ชั่วโมง
    # แก้แถว map / รหัสสำรองแล้วต้องล้าง ไม่งั้นต้องรอชั่วโมงกว่าจะเห็นผล
    cache.delete(EXPORT_DOC_OWN_PORT_CUSTOMERS_CACHE_KEY)


def _ratesUsing(row):
    """ใบราคาค่าขนส่ง (ทุกเวอร์ชัน) ที่ใช้แถวนี้เป็นต้นทางหรือปลายทาง ใบเหล่านี้ทำให้ลบแถวไม่ได้"""
    return (InternationalFreightRate.objects
            .filter(Q(origin=row) | Q(destination=row))
            .select_related('origin', 'destination')
            .order_by('origin_id', 'destination_id', 'version'))


@login_required(login_url='login')
@permission_required(PERM_CHANGE, raise_exception=True)
def settingCompanyMap(request):
    active = _activeCompany(request)
    if not active:
        return redirect('logout')

    rows = (BaseCompanyMapBaseCustomer.objects
            .select_related('base_company', 'base_customer')
            .prefetch_related('customer_aliases')
            .annotate(rate_count=Count('freight_rate_origins', distinct=True)
                      + Count('freight_rate_destinations', distinct=True))
            .order_by('id'))

    query = (request.GET.get('q') or '').strip()
    if query:
        rows = rows.filter(Q(name__icontains=query)
                           | Q(base_company__name__icontains=query)
                           | Q(base_customer__customer_id__icontains=query)
                           | Q(base_customer__customer_name__icontains=query)
                           | Q(customer_aliases__base_customer__customer_id__icontains=query)).distinct()

    kind = request.GET.get('kind') or ''
    flagged = Q(is_export_destination=True) | Q(is_domestic_destination=True)
    if kind == 'export':
        rows = rows.filter(is_export_destination=True)
    elif kind == 'domestic':
        rows = rows.filter(is_domestic_destination=True)
    elif kind == 'none':
        rows = rows.exclude(flagged)
    elif kind == 'incomplete':
        rows = rows.filter(flagged, base_customer__isnull=True)

    rows = list(rows)
    for row in rows:
        row.alias_codes = [alias.base_customer_id for alias in row.customer_aliases.all()]
        # ติ๊กปลายทางแต่ไม่มีรหัสลูกค้า = แถวนี้ไม่มีเที่ยวเข้าเลย ไฮไลต์ให้เห็น
        row.is_incomplete = ((row.is_export_destination or row.is_domestic_destination)
                             and not row.base_customer_id)

    context = {
        'ifr_page': 'active',
        'rows': rows,
        'query': query,
        'kind': kind,
        'kind_options': COMPANY_MAP_FILTERS,
        'can_delete': request.user.has_perm(PERM_DELETE),
        active: 'active',
    }
    return render(request, 'internationalFreightRate/companyMap/companyMapList.html', context)


def _companyMapForm(request, row=None):
    active = _activeCompany(request)
    if not active:
        return redirect('logout')

    instance = row or BaseCompanyMapBaseCustomer()
    form = CompanyMapForm(request.POST or None, instance=row)
    formset = CompanyMapAliasFormSet(request.POST or None, instance=instance, prefix='alias')

    # เรียกทั้งคู่ก่อน ไม่ใช้ and ตรง ๆ ไม่งั้นฟอร์มหลักผิดแล้ว error ของรหัสสำรองจะไม่ขึ้นมาพร้อมกัน
    form_ok = request.method == 'POST' and form.is_valid()
    formset_ok = request.method == 'POST' and formset.is_valid()
    if form_ok and formset_ok:
        # รหัสหลักกับรหัสสำรองของแถวเดียวกันห้ามซ้ำกัน ต้องเช็คหลังรู้ค่าทั้งคู่
        primary = form.cleaned_data.get('base_customer')
        if primary is not None and primary.pk in formset.keptCustomerIds():
            form.add_error('base_customer', 'รหัสนี้อยู่ในรายการรหัสสำรองของแถวนี้ด้วย '
                                            'ให้เลือกเป็นรหัสหลักหรือรหัสสำรองอย่างใดอย่างหนึ่ง')
        else:
            with transaction.atomic():
                saved = form.save()
                formset.instance = saved
                formset.save()
            _clearOwnPortCache()
            messages.success(request, 'บันทึก "%s" แล้ว' % saved.name)
            return redirect('settingCompanyMap')

    context = {
        'ifr_page': 'active',
        'form': form,
        'formset': formset,
        'row': row,
        'text_mode': 'แก้ไข' if row else 'เพิ่ม',
        'rate_count': _ratesUsing(row).count() if row else 0,
        active: 'active',
    }
    return render(request, 'internationalFreightRate/companyMap/companyMapForm.html', context)


@login_required(login_url='login')
@permission_required(PERM_CHANGE, raise_exception=True)
def createCompanyMap(request):
    return _companyMapForm(request)


@login_required(login_url='login')
@permission_required(PERM_CHANGE, raise_exception=True)
def editCompanyMap(request, id):
    return _companyMapForm(request, get_object_or_404(BaseCompanyMapBaseCustomer, id=id))


@login_required(login_url='login')
@permission_required(PERM_DELETE, raise_exception=True)
def deleteCompanyMap(request, id):
    """GET = หน้ายืนยัน บอกว่าจะลบอะไรไปบ้าง / POST = ลบจริง

    ลบไม่ได้ถ้ามีใบราคาค่าขนส่งใช้แถวนี้อยู่ (FK ของใบราคาเป็น PROTECT)
    รหัสสำรองของแถวนี้ลบตามไปด้วย (CASCADE)
    """
    active = _activeCompany(request)
    if not active:
        return redirect('logout')

    row = get_object_or_404(BaseCompanyMapBaseCustomer.objects.select_related('base_company', 'base_customer'),
                            id=id)
    rates = list(_ratesUsing(row))

    if request.method == 'POST' and not rates:
        name = row.name
        try:
            with transaction.atomic():
                row.delete()
        except ProtectedError:
            # มีคนเพิ่มใบราคาที่ใช้แถวนี้ระหว่างที่เปิดหน้ายืนยันค้างไว้
            messages.error(request, 'ลบ "%s" ไม่ได้ มีใบราคาค่าขนส่งใช้แถวนี้อยู่' % name)
            return redirect('deleteCompanyMap', id=id)
        _clearOwnPortCache()
        messages.success(request, 'ลบ "%s" แล้ว' % name)
        return redirect('settingCompanyMap')

    context = {
        'ifr_page': 'active',
        'row': row,
        'aliases': list(row.customer_aliases.select_related('base_customer')),
        'rates': rates,
        active: 'active',
    }
    return render(request, 'internationalFreightRate/companyMap/companyMapDelete.html', context)


@login_required(login_url='login')
@permission_required(PERM_CHANGE, raise_exception=True)
def companyMapCustomerSearch(request):
    """ค้นลูกค้าให้ช่อง select2 ในฟอร์ม
    คืน {"results": [{"id": ..., "text": ...}], "pagination": {"more": true/false}}

    ส่งทีละหน้า (CUSTOMER_SEARCH_LIMIT ราย) เลื่อนถึงท้ายรายการ select2 จะขอหน้าถัดไปเอง (?page=2, 3, ...)
    บอกด้วยว่ารหัสไหนถูกใช้ไปแล้วที่แถวไหน คนกรอกจะได้ไม่ต้องรอกดบันทึกแล้วค่อยเจอ error
    """
    term = (request.GET.get('term') or '').strip()
    try:
        page = max(int(request.GET.get('page') or 1), 1)
    except ValueError:
        page = 1
    customers = BaseCustomer.objects.order_by('customer_id')
    if term:
        customers = customers.filter(Q(customer_id__icontains=term) | Q(customer_name__icontains=term))
    start = (page - 1) * CUSTOMER_SEARCH_LIMIT
    # ดึงเกินมา 1 ราย ไว้รู้ว่ายังมีหน้าถัดไปไหม ไม่ต้อง count ทั้งตาราง
    customers = list(customers[start:start + CUSTOMER_SEARCH_LIMIT + 1])
    more = len(customers) > CUSTOMER_SEARCH_LIMIT
    customers = customers[:CUSTOMER_SEARCH_LIMIT]

    ids = [customer.pk for customer in customers]
    used = {customer_id: name for customer_id, name in BaseCompanyMapBaseCustomer.objects
            .filter(base_customer_id__in=ids).values_list('base_customer_id', 'name')}
    used.update({customer_id: name for customer_id, name in BaseCompanyMapCustomerAlias.objects
                 .filter(base_customer_id__in=ids).values_list('base_customer_id', 'map_row__name')})

    results = []
    for customer in customers:
        text = customerChoiceLabel(customer)
        if customer.pk in used:
            text += '  (ใช้อยู่ที่ "%s")' % used[customer.pk]
        results.append({'id': customer.pk, 'text': text})
    return JsonResponse({'results': results, 'pagination': {'more': more}})
