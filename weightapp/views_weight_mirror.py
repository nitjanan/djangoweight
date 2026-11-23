# -*- coding: utf-8 -*-
"""API สำเนาข้อมูลชั่ง (ตาราง weight_mirror) ไว้กู้ local DB ของตาชั่งที่เสีย

ตาชั่ง (WeightMirrorSync.cs) ส่งคิว sync_outbox ขึ้นมาทุก 3 นาที เป็นชุดละไม่เกิน 200 แถว บีบอัด gzip
ตอบ 2xx = ตาชั่ง mark ว่าส่งแล้ว ; ตอบอย่างอื่น = ตาชั่งส่งทั้งชุดซ้ำรอบหน้า
ดังนั้นแถวที่ผิดรูปแบบต้องข้ามแล้วตอบ 200 ไม่งั้นทั้งชุดจะค้างส่งซ้ำไม่จบ

ไม่ใช่ข้อมูลจริง ข้อมูลจริงยังมาจาก weight/api/create/ ตอนเย็น ; สเปกดู docs/weight-mirror-api.md
"""
import json
import logging
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, Max, Min
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from weightapp.models import Weight, WeightMirror
from weightapp.serializers import WeightSerializer

logger = logging.getLogger(__name__)

MAX_ITEMS = 500
LIST_PAGE_SIZE = 500
ACTIONS = {'I', 'U', 'D'}
# column วันที่ของตาราง weight ฝั่ง local (ชื่อภาษาไทย)
RECORD_DATE_KEYS = ('วันที่', 'date', 'delivery_date')

_UPDATE_FIELDS = ['mine_code', 'station_code', 'action', 'rev', 'payload', 'is_deleted', 'record_date', 'queued_at',
                  'received_at']


def _naiveDatetime(raw):
    # ตาชั่งส่งแบบ "2026-11-23T08:38:48+07" ; โปรเจกต์ USE_TZ = False MySQL รับ aware datetime ไม่ได้
    if not raw:
        return None
    dt = parse_datetime(str(raw))
    if dt is None:
        return None
    if timezone.is_aware(dt):
        dt = timezone.make_naive(dt, timezone.get_default_timezone())
    return dt


def _recordDate(payload):
    if not isinstance(payload, dict):
        return None
    for key in RECORD_DATE_KEYS:
        raw = payload.get(key)
        if raw:
            d = parse_date(str(raw)[:10])
            if d:
                return d
    return None


def _clip(value, length):
    return ('' if value is None else str(value).strip())[:length]


class DecimalJSONParser(JSONParser):
    """อ่านตัวเลขทศนิยมเป็น Decimal ไม่ใช่ float : น้ำหนัก 12.340 ต้องกู้กลับเป็น 12.340 ไม่ใช่ 12.34"""

    def parse(self, stream, media_type=None, parser_context=None):
        encoding = (parser_context or {}).get('encoding', settings.DEFAULT_CHARSET)
        try:
            return json.loads(stream.read().decode(encoding), parse_float=Decimal)
        except ValueError as exc:
            raise ParseError('JSON parse error - %s' % exc)


@api_view(['POST'])
@parser_classes([DecimalJSONParser])
@permission_classes([IsAuthenticated])
def weightMirrorBulk(request):
    data = request.data if isinstance(request.data, dict) else {}
    comp_code = _clip(data.get('comp_code'), 20)
    mine_code = _clip(data.get('mine_code'), 20)
    station_code = _clip(data.get('station_code'), 30)
    items = data.get('items')

    if not comp_code or not isinstance(items, list):
        return Response({'error': 'ต้องมี comp_code และ items'}, status=status.HTTP_400_BAD_REQUEST)
    if len(items) > MAX_ITEMS:
        return Response({'error': 'items เกิน %d แถวต่อครั้ง' % MAX_ITEMS},
                        status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    now = datetime.now()
    # คีย์ซ้ำในชุดเดียวกัน เก็บตัวท้ายสุด (ใหม่สุด) ไม่งั้น bulk_create ชนกันเอง
    objs = {}
    skipped = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            skipped.append({'index': index, 'error': 'ไม่ใช่ object'})
            continue
        table_name = _clip(item.get('table_name'), 50)
        row_id = _clip(item.get('row_id'), 50)
        action = _clip(item.get('action'), 1).upper()
        if not table_name or not row_id or action not in ACTIONS:
            skipped.append({'index': index, 'row_id': row_id, 'error': 'table_name/row_id/action ไม่ถูกต้อง'})
            continue
        try:
            rev = int(item.get('rev') or 0)
        except (TypeError, ValueError):
            rev = 0

        payload = item.get('payload')
        objs[(table_name, row_id)] = WeightMirror(
            comp_code=comp_code,
            mine_code=mine_code,
            station_code=station_code,
            table_name=table_name,
            row_id=row_id,
            action=action,
            rev=rev,
            payload=payload,
            is_deleted=(action == 'D'),
            record_date=_recordDate(payload),
            queued_at=_naiveDatetime(item.get('queued_at')),
            received_at=now,
        )

    if skipped:
        logger.warning('weightMirrorBulk comp_code=%s skipped %d item(s): %s', comp_code, len(skipped), skipped[:5])

    if objs:
        # MySQL/MariaDB = INSERT ... ON DUPLICATE KEY UPDATE ด้วย query เดียว (ห้ามใส่ unique_fields บน MySQL)
        WeightMirror.objects.bulk_create(list(objs.values()), update_conflicts=True,
                                         update_fields=_UPDATE_FIELDS)

    return Response({'saved': len(objs), 'skipped': skipped}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightMirrorList(request):
    """ดึงสำเนากลับไปกู้ตาชั่ง : ?station_code=&comp_code=&mine_code=&table_name=weight&date_from=YYYY-MM-DD&page=1

    station_code (= base_weight_station.code ของตาชั่ง) บังคับ ; comp_code/mine_code เป็นตัวกรองเสริม
    ตอบรูปแบบ {results, next} แบบเดียวกับ API อื่นที่ตาชั่งไล่ดึงทีละหน้า (FetchAllPagesAsync)
    """
    station_code = request.GET.get('station_code', '').strip()
    if not station_code:
        return Response({'error': 'ต้องมี station_code'}, status=status.HTTP_400_BAD_REQUEST)

    qs = WeightMirror.objects.filter(station_code=station_code)
    comp_code = request.GET.get('comp_code', '').strip()
    if comp_code:
        qs = qs.filter(comp_code=comp_code)
    mine_code = request.GET.get('mine_code', '').strip()
    if mine_code:
        qs = qs.filter(mine_code=mine_code)
    qs = qs.filter(table_name=request.GET.get('table_name', 'weight').strip() or 'weight')

    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        d = parse_date(date_from)
        if d is None:
            return Response({'error': 'date_from ต้องเป็น YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        qs = qs.filter(record_date__gte=d)

    paginator = Paginator(qs.order_by('id'), LIST_PAGE_SIZE)
    try:
        page_number = int(request.GET.get('page', 1))
        page = paginator.page(page_number)
    except (ValueError, EmptyPage):
        return Response({'results': [], 'next': None, 'count': paginator.count})

    next_url = None
    if page.has_next():
        params = request.GET.copy()
        params['page'] = page.next_page_number()
        next_url = request.build_absolute_uri(request.path + '?' + params.urlencode())

    results = [{
        'table_name': m.table_name,
        'row_id': m.row_id,
        'action': m.action,
        'rev': m.rev,
        'is_deleted': m.is_deleted,
        'record_date': m.record_date.isoformat() if isinstance(m.record_date, date) else None,
        'queued_at': m.queued_at.isoformat() if m.queued_at else None,
        'payload': m.payload,
    } for m in page.object_list]

    return Response({'results': results, 'next': next_url, 'count': paginator.count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightMirrorStations(request):
    """สรุปสำเนาของตาชั่งนี้ (แยกตาม comp_code/mine_code) ให้ผู้ใช้ดูก่อนกู้ : ?station_code=&table_name=weight

    station_code = base_weight_station.code ของตาชั่ง ; ตาชั่งหลายตัวใช้ comp_code เดียวกันจึงค้นด้วยรหัสตาชั่ง
    """
    station_code = request.GET.get('station_code', '').strip()
    if not station_code:
        return Response({'error': 'ต้องมี station_code'}, status=status.HTTP_400_BAD_REQUEST)

    rows = (WeightMirror.objects
            .filter(station_code=station_code,
                    table_name=request.GET.get('table_name', 'weight').strip() or 'weight',
                    is_deleted=False)
            .values('comp_code', 'station_code', 'mine_code')
            .annotate(count=Count('id'), last_record_date=Max('record_date'), last_received_at=Max('received_at'))
            .order_by('comp_code', 'mine_code'))

    # วันแรกที่มีรายการชั่ง (อัพโหลดแล้ว) ของตาชั่งนี้ ใช้ตั้งวันที่เริ่มต้นเมื่อกู้โดยไม่ใช้สำเนา
    weight_first_date = Weight.objects.filter(bws=station_code).aggregate(d=Min('date'))['d']

    return Response({'weight_first_date': weight_first_date.isoformat() if weight_first_date else None,
                     'results': [{
        'comp_code': r['comp_code'],
        'station_code': r['station_code'],
        'mine_code': r['mine_code'],
        'count': r['count'],
        'last_record_date': r['last_record_date'].isoformat() if r['last_record_date'] else None,
        'last_received_at': r['last_received_at'].isoformat() if r['last_received_at'] else None,
    } for r in rows]})


MAX_WEIGHT_IDS = 500


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightMirrorWeightByIds(request):
    """weight ที่อัพโหลดแล้วของตาชั่งนี้ตาม weight_id : ?station_code=&ids=1,2,3

    ตอนกู้ ตาชั่งใช้เช็คสำเนาก่อนเติม : weight_id ไหนมีบน server แล้วต้องใช้ข้อมูลจาก server
    (เช่นวันที่ถูกแก้บนเว็บจนอยู่นอกช่วงวันที่ที่ดึง) ไม่มี = ตอบเฉพาะที่พบ ไม่ error
    """
    station_code = request.GET.get('station_code', '').strip()
    if not station_code:
        return Response({'error': 'ต้องมี station_code'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ids = sorted({int(x) for x in request.GET.get('ids', '').split(',') if x.strip()})
    except ValueError:
        return Response({'error': 'ids ต้องเป็นตัวเลขคั่นด้วย ,'}, status=status.HTTP_400_BAD_REQUEST)
    if len(ids) > MAX_WEIGHT_IDS:
        return Response({'error': f'ids ได้ไม่เกิน {MAX_WEIGHT_IDS} ตัวต่อครั้ง'}, status=status.HTTP_400_BAD_REQUEST)

    rows = Weight.objects.filter(bws=station_code, weight_id__in=ids).order_by('weight_id')
    return Response({'results': WeightSerializer(rows, many=True).data})
