# -*- coding: utf-8 -*-
"""เสนอข้อมูลที่ "คล้าย" กับชื่อที่กำลังคีย์ ในหน้าเพิ่มข้อมูลพื้นฐาน (createBase*)

ให้ user เห็นรหัส/ชื่อที่มีอยู่แล้วในระบบก่อนกดบันทึก กันการเพิ่มข้อมูลซ้ำ
เช่น "บจก. ศิลาชัย" กับ "บริษัท ศิลาชัย จำกัด" ซึ่ง unique constraint จับไม่ได้

ความคล้ายคิดฝั่ง Python (difflib) ทำงานได้ทั้ง MySQL / SQLite ไม่ต้องพึ่ง extension ของ DB
ตารางพื้นฐานมีไม่กี่พันแถว ดึงมาเทียบทั้งหมดต่อการค้นหาหนึ่งครั้งจึงยังเร็วพอ
"""
import re
from difflib import SequenceMatcher

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from weightapp import forms as base_forms
from weightapp.base_view_mode import viewOnlyUrl
from weightapp.views_base_usage import weightUsageByCompany

from weightapp.models import (BaseCar, BaseCarRegistration, BaseCarTeam, BaseCustomer, BaseDriver,
                              BaseJobType, BaseMill, BaseScoop, BaseSite, BaseStoneType)

# key = ชื่อที่หน้าเว็บส่งมา (whitelist) -> (model, ฟิลด์รหัส, ฟิลด์ชื่อ, url หน้าแก้ไข, ฟิลด์ปิดการใช้งาน)
SIMILAR_BASE_MODELS = {
    'BaseMill': (BaseMill, 'mill_id', 'mill_name', 'editBaseMill', None),
    'BaseJobType': (BaseJobType, 'base_job_type_id', 'base_job_type_name', 'editBaseJobType', None),
    'BaseStoneType': (BaseStoneType, 'base_stone_type_id', 'base_stone_type_name', 'editBaseStoneType', 'inactive'),
    'BaseScoop': (BaseScoop, 'scoop_id', 'scoop_name', 'editBaseScoop', None),
    'BaseCarTeam': (BaseCarTeam, 'car_team_id', 'car_team_name', 'editBaseCarTeam', None),
    'BaseCar': (BaseCar, 'car_id', 'car_name', 'editBaseCar', None),
    'BaseSite': (BaseSite, 'base_site_id', 'base_site_name', 'editBaseSite', None),
    'BaseCustomer': (BaseCustomer, 'customer_id', 'customer_name', 'editBaseCustomer', 'is_disable'),
    'BaseDriver': (BaseDriver, 'driver_id', 'driver_name', 'editBaseDriver', None),
    'BaseCarRegistration': (BaseCarRegistration, 'car_registration_id', 'car_registration_name',
                            'editBaseCarRegistration', None),
}

# ช่องบังคับกรอกของแต่ละฟอร์ม (นอกจากรหัส/ชื่อ) แสดงในกล่องเสนอ ให้ user แยกได้ว่าชื่อซ้ำแต่คนละประเภท/บริษัทหรือไม่
# (ฟิลด์, ป้ายชื่อ)  ถ้าเพิ่มช่องบังคับในฟอร์ม ให้เพิ่มที่นี่ด้วย (tests_similar_base เช็คไว้)
SIMILAR_BASE_DETAILS = {
    'BaseMill': [('weight_type', 'ประเภทเครื่องชั่ง')],
    'BaseScoop': [('company', 'บริษัท')],
    'BaseCar': [('base_car_team', 'ทีม')],
    'BaseSite': [('weight_type', 'ประเภทเครื่องชั่ง')],
    # ประเภทงาน : ฟอร์มบังคับกรอกเมื่อชนิดเครื่องชั่งเป็น "ขาย" (ตั้ง required ด้วย JS)
    'BaseCustomer': [('weight_type', 'ชนิดเครื่องชั่ง'), ('base_job_type', 'ประเภทงานของลูกค้า')],
    'BaseDriver': [('company', 'บริษัท')],
    'BaseCarRegistration': [('car_type', 'ประเภทรถ'), ('company', 'บริษัท')],
}

SIMILAR_MIN_SCORE = 0.6
SIMILAR_LIMIT = 10

# คำนำหน้า/ต่อท้ายชื่อนิติบุคคลที่ไม่ช่วยแยกว่าเป็นคนละราย (เรียงยาวก่อน ให้ตัดคำยาวได้ก่อนคำสั้น)
_NAME_NOISE = sorted([
    'ห้างหุ้นส่วนจำกัด', 'ห้างหุ้นส่วนสามัญ', 'บริษัท', 'บจก', 'หจก', 'จำกัด', 'มหาชน', 'บมจ',
    'ltd', 'limited',
], key=len, reverse=True)
_PUNCT_RE = re.compile(r'[\s\.\,\-\(\)\/\\\'"&_:;]+')


def normalizeBaseName(text):
    """ตัดช่องว่าง เครื่องหมาย และคำนำหน้านิติบุคคลออก เหลือแก่นของชื่อไว้เทียบ"""
    text = _PUNCT_RE.sub('', (text or '').lower())
    stripped = text
    for word in _NAME_NOISE:
        stripped = stripped.replace(word, '')
    # ถ้าชื่อมีแต่คำนำหน้า (เช่น "บริษัท") อย่าให้เหลือว่าง
    return stripped or text


def similarScore(query_norm, name_norm):
    if not query_norm or not name_norm:
        return 0.0
    if query_norm == name_norm:
        return 1.0
    if len(query_norm) >= 2 and (query_norm in name_norm or name_norm in query_norm):
        return 0.9
    return SequenceMatcher(None, query_norm, name_norm).ratio()


def findSimilarBase(model_key, query, limit=SIMILAR_LIMIT, exclude=None):
    """exclude = รหัสของรายการที่กำลังแก้ไขอยู่ (หน้า editBase*) ไม่ต้องเสนอตัวเอง"""
    model, id_field, name_field, edit_url, disable_field = SIMILAR_BASE_MODELS[model_key]
    query_norm = normalizeBaseName(query)
    if len(query_norm) < 2:
        return []

    fields = [id_field, name_field] + ([disable_field] if disable_field else [])
    results = []
    for row in model.objects.values(*fields):
        if exclude is not None and str(row[id_field]) == str(exclude):
            continue
        name = row[name_field] or ''
        score = similarScore(query_norm, normalizeBaseName(name))
        if score < SIMILAR_MIN_SCORE:
            continue
        results.append({
            'id': row[id_field],
            'name': name,
            'score': round(score, 2),
            'exact': score == 1.0,
            'disabled': bool(row[disable_field]) if disable_field else False,
            # ปุ่ม "ดูข้อมูล" เปิด popup (similarBaseDetail) ลิงก์ "เปิดหน้าเต็ม" ใน popup = หน้าแก้ไขโหมดดูอย่างเดียว
        })
    results.sort(key=lambda r: (-r['score'], r['name']))
    results = results[:limit]
    _attachDetails(model_key, model, id_field, results)
    return results


def _detailText(value):
    """ค่าที่จะแสดง : บริษัทแสดง "รหัส ชื่อ", FK อื่นใช้ __str__ ของ model, ว่าง = '-'"""
    if value is None or value == '':
        return '-'
    if hasattr(value, 'code') and hasattr(value, 'name'):  # BaseCompany
        return ' '.join(str(v) for v in (value.code, value.name) if v)
    return str(value)


def _attachDetails(model_key, model, id_field, results):
    """เติมค่าช่องบังคับกรอกให้เฉพาะแถวที่ผ่านเกณฑ์ (ไม่กี่แถว) จะได้ไม่ต้อง join ทั้งตาราง"""
    details = SIMILAR_BASE_DETAILS.get(model_key, [])
    for r in results:
        r['details'] = []
    if not details or not results:
        return
    fk_fields = [f for f, _ in details if model._meta.get_field(f).is_relation]
    objs = model.objects.select_related(*fk_fields).in_bulk([r['id'] for r in results], field_name=id_field)
    for r in results:
        obj = objs.get(r['id'])
        r['details'] = [{'label': label, 'value': _detailText(getattr(obj, field, None))} for field, label in details]


@login_required(login_url='login')
def searchSimilarBase(request):
    model_key = request.GET.get('model', '')
    if model_key not in SIMILAR_BASE_MODELS:
        return JsonResponse({'results': []}, status=400)
    query = (request.GET.get('q') or '')[:255]
    exclude = request.GET.get('exclude') or None
    return JsonResponse({'results': findSimilarBase(model_key, query, exclude=exclude)})


def similarBaseContext(model_key, exclude_id=None):
    """context สำหรับหน้า createBase* / editBase* : บอก template ว่าจะเปิดกล่องเสนอชื่อคล้ายที่ช่องไหน
    หน้าแก้ไขส่ง exclude_id = รหัสของรายการนั้น จะได้ไม่เสนอตัวเองว่าชื่อตรงกัน"""
    name_field = SIMILAR_BASE_MODELS[model_key][2]
    context = {'similar_model': model_key, 'similar_input': '#id_' + name_field}
    if exclude_id is not None:
        context['similar_exclude'] = str(exclude_id)
    return context


# ช่องที่ไม่แสดงใน popup ดูข้อมูล (ซ่อนไว้ในหน้าฟอร์มด้วย)
SIMILAR_DETAIL_HIDE = {
    'BaseCustomer': {'base_vat_type'},
}


def _formFieldText(bound_field):
    """ค่าของช่องในฟอร์มเป็นข้อความเหมือนที่หน้าฟอร์มแสดง (ตัวเลือกใช้ป้ายเดียวกับ dropdown)"""
    field, value = bound_field.field, bound_field.value()
    if value in (None, '', []):
        return '-'
    if isinstance(value, bool):
        return 'ใช่' if value else 'ไม่ใช่'
    queryset = getattr(field, 'queryset', None)
    if queryset is not None:
        obj = queryset.model._default_manager.filter(pk=value).first()
        return field.label_from_instance(obj) if obj else str(value)
    choices = getattr(field, 'choices', None)
    if choices:
        return str(dict(choices).get(value, value))
    return str(value)


def baseRecordDetail(model_key, pk):
    """ข้อมูลหนึ่งรายการสำหรับ popup : ทุกช่องที่หน้าฟอร์มแสดง + บริษัทที่ใช้ข้อมูลนี้ในตาชั่ง"""
    model, id_field, name_field, edit_url, disable_field = SIMILAR_BASE_MODELS[model_key]
    obj = get_object_or_404(model, **{id_field: pk})
    form = getattr(base_forms, model_key + 'Form')(instance=obj)
    hide = SIMILAR_DETAIL_HIDE.get(model_key, set())
    fields = [{'label': str(bf.label), 'value': _formFieldText(bf), 'required': bf.field.required}
              for bf in form.visible_fields() if bf.name not in hide]
    usage = [{'code': u['code'] or '-', 'name': u['name'], 'count': u['count']}
             for u in weightUsageByCompany(model_key, pk)]
    return {
        'id': getattr(obj, id_field),
        'name': getattr(obj, name_field) or '',
        'disabled': bool(getattr(obj, disable_field)) if disable_field else False,
        'fields': fields,
        'usage': usage,
        'view_url': viewOnlyUrl(reverse(edit_url, args=[pk])),
    }


@login_required(login_url='login')
def similarBaseDetail(request):
    """popup "ดูข้อมูล" ในกล่องเสนอชื่อคล้าย : อ่านอย่างเดียว (GET) ไม่มีทางบันทึก"""
    model_key = request.GET.get('model', '')
    if model_key not in SIMILAR_BASE_MODELS:
        return JsonResponse({'error': 'unknown model'}, status=400)
    return JsonResponse(baseRecordDetail(model_key, request.GET.get('id', '')))
