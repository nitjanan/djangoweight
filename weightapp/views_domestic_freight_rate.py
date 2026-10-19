# -*- coding: utf-8 -*-
"""ตารางราคา ค่าขนส่งในประเทศ (issue #118) : หน้ารายการ / เพิ่ม / ลบ เส้นทาง

ตาราง DomesticFreightRate / DomesticFreightRateTeam แยกจากส่งออก แต่ใช้หลักเดียวกัน
ยังไม่ผูกเมนู navbar เข้าด้วย URL ตรง ๆ (/domesticFreightRate/)
ยังไม่มีหน้าแก้ไข/ประวัติเวอร์ชัน และหน้ารายงานคิดเงินรายเดือน
"""
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from weightapp import views as core_views
from weightapp.models import (BaseCarTeam, BaseCompanyMapBaseCustomer, DomesticFreightRate,
                              DomesticFreightRateTeam, DomesticFreightWeightBand)
from weightapp.serializers import DomesticFreightRateSerializer

NO_NAME = '(ไม่พบชื่อ)'
BAND_ORDER = {DomesticFreightWeightBand.ALL: 0, DomesticFreightWeightBand.UNDER_31: 1,
              DomesticFreightWeightBand.FROM_31: 2}


def _sortedTeams(teams):
    """ทีมที่ระบุชื่อขึ้นก่อน (เรียงตามรหัส) แถว "ทุกทีม" ไว้ท้าย ในทีมเดียวกันเรียงตามช่วงน้ำหนัก"""
    return sorted(teams, key=lambda t: (t.team_id is None, t.team_id or '', BAND_ORDER.get(t.weight_band, 9)))


def _currentRates():
    """ใบที่ใช้อยู่ตอนนี้ เส้นทางละใบ พร้อมทีม"""
    return DomesticFreightRate.effectiveOn(
        date.today(),
        DomesticFreightRate.objects
        .select_related('origin', 'destination')
        .prefetch_related(Prefetch('teams', queryset=DomesticFreightRateTeam.objects.select_related('team'))))


@login_required(login_url='login')
def viewDomesticFreightRate(request):
    active = request.session.get('company_code')
    if not active:
        return redirect('logout')

    map_names = core_views._baseCompanyMapDisplayNameById()
    rows = _currentRates()
    for row in rows:
        row.sorted_teams = _sortedTeams(row.teams.all())
        row.has_specific_team = any(t.team_id for t in row.sorted_teams)
        row.team_group_count = len({t.team_id for t in row.sorted_teams})
        row.origin_display = map_names.get(row.origin_id) or NO_NAME
        row.destination_display = map_names.get(row.destination_id) or NO_NAME

    route_count = {}
    for row in rows:
        route_count[row.origin_id] = route_count.get(row.origin_id, 0) + 1
    origin_options = sorted(
        ({'id': oid, 'name': map_names.get(oid) or NO_NAME, 'count': n} for oid, n in route_count.items()),
        key=lambda o: core_views._thaiSortKey(o['name']))
    try:
        selected_origin = int(request.GET.get('origin') or '')
    except ValueError:
        selected_origin = None
    shown = rows if selected_origin is None else [r for r in rows if r.origin_id == selected_origin]

    groups = {}
    for row in shown:
        groups.setdefault(row.origin_id, []).append(row)
    groups = sorted(
        ({'origin_name': map_names.get(oid) or NO_NAME,
          'rows': sorted(g, key=lambda r: core_views._thaiSortKey(r.destination_display))}
         for oid, g in groups.items()),
        key=lambda g: core_views._thaiSortKey(g['origin_name']))

    context = {
        'dfr_page': 'active',
        'dfr_groups': groups,
        'dfr_origin_options': origin_options,
        'dfr_selected_origin': selected_origin,
        'dfr_route_total': len(rows),
        active: 'active',
    }
    return render(request, 'domesticFreightRate/viewDomesticFreightRate.html', context)


def _mapOptions():
    """ตัวเลือกต้นทาง (แถวที่ผูกบริษัท) และปลายทาง (แถวที่ติ๊ก "ใช้เป็นปลายทางในประเทศ")"""
    rows = core_views._baseCompanyMapRows()
    domestic_ids = set(BaseCompanyMapBaseCustomer.objects
                       .filter(is_domestic_destination=True).values_list('id', flat=True))
    origins = [{'id': r['id'], 'name': r['display']} for r in rows if r['base_company_id']]
    destinations = [{'id': r['id'], 'name': r['display']} for r in rows if r['id'] in domestic_ids]
    key = lambda o: core_views._thaiSortKey(o['name'] or '')
    return sorted(origins, key=key), sorted(destinations, key=key)


@login_required(login_url='login')
def createDomesticFreightRate(request):
    active = request.session.get('company_code')
    if not active:
        return redirect('logout')
    origins, destinations = _mapOptions()
    teams = [{'id': t['car_team_id'], 'name': t['car_team_name'] or t['car_team_id']}
             for t in BaseCarTeam.objects.order_by('car_team_id').values('car_team_id', 'car_team_name')]
    context = {
        'dfr_page': 'active',
        'dfr_origins': origins,
        'dfr_destinations': destinations,
        'dfr_teams': teams,
        'dfr_bands': [[value, label] for value, label in DomesticFreightWeightBand.choices],
        active: 'active',
    }
    return render(request, 'domesticFreightRate/createDomesticFreightRate.html', context)


# ระบุสิทธิ์เองทุกตัว : DEFAULT_PERMISSION_CLASSES ใน settings เขียนเป็น string ไม่ใช่ tuple ใช้ค่า default ไม่ได้
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def domesticFreightRateCreate(request):
    serializer = DomesticFreightRateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        rate = serializer.save()
        return Response({'id': rate.id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def domesticFreightRateDelete(request, id):
    """ลบเส้นทาง = ลบทุกเวอร์ชันของเส้นทางนั้น (ลำดับเดียวกับ internationalFreightRateDelete)"""
    obj = DomesticFreightRate.objects.filter(id=id).first()
    if obj is None:
        return Response({'error': 'ไม่พบข้อมูล'}, status=status.HTTP_404_NOT_FOUND)
    root_id = obj.root_id or obj.id
    with transaction.atomic():
        family = DomesticFreightRate.objects.filter(root_id=root_id)
        removed = family.count()
        family.exclude(id=root_id).delete()
        # ใบแรกชี้ตัวเอง ต้องตัดออกก่อน ไม่งั้น PROTECT จะกันการลบตัวเอง
        DomesticFreightRate.objects.filter(id=root_id).update(root=None)
        DomesticFreightRate.objects.filter(id=root_id).delete()
    return Response({'message': 'ลบสำเร็จ (ลบไป %s รายการ)' % removed}, status=status.HTTP_200_OK)
