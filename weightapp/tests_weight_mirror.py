# -*- coding: utf-8 -*-
"""API สำเนาข้อมูลชั่ง (views_weight_mirror.py) + GzipRequestMiddleware"""
import gzip
import json
from datetime import date, datetime, timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from weightapp.models import BaseWeightStation, Weight, WeightMirror


def item(row_id, action='I', rev=0, note='a', day='2026-11-23', queued='2026-11-23T08:38:48+07'):
    return {'table_name': 'weight', 'row_id': str(row_id), 'action': action, 'rev': rev, 'queued_at': queued,
            'payload': {'weight_id': row_id, 'วันที่': day, 'หมายเหตุ': note}}


class WeightMirrorBulkTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('scale', 'scale@t.com', 'pw12345!')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = reverse('weightMirrorBulk')

    def post(self, items, comp_code='SLC', mine_code='M1', use_gzip=False):
        body = json.dumps({'comp_code': comp_code, 'mine_code': mine_code, 'items': items}).encode('utf-8')
        extra = {}
        if use_gzip:
            body = gzip.compress(body)
            extra['HTTP_CONTENT_ENCODING'] = 'gzip'
        return self.client.generic('POST', self.url, body, content_type='application/json; charset=utf-8',
                                   **extra)

    def test_requires_auth(self):
        response = APIClient().post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_gzip_body_is_saved(self):
        response = self.post([item(1), item(2)], use_gzip=True)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['saved'], 2)
        m = WeightMirror.objects.get(row_id='1')
        self.assertEqual(m.comp_code, 'SLC')
        self.assertEqual(m.mine_code, 'M1')
        self.assertEqual(m.payload['หมายเหตุ'], 'a')
        self.assertEqual(m.record_date, date(2026, 11, 23))
        self.assertEqual(m.queued_at, datetime(2026, 11, 23, 8, 38, 48))

    def test_broken_gzip_is_400(self):
        response = self.client.generic('POST', self.url, b'not gzip', content_type='application/json',
                                       HTTP_CONTENT_ENCODING='gzip')
        self.assertEqual(response.status_code, 400)

    def test_resend_upserts_without_duplicates(self):
        self.post([item(1, note='a')])
        self.post([item(1, action='U', rev=1, note='b')])
        self.post([item(1, action='U', rev=1, note='b')])
        self.assertEqual(WeightMirror.objects.count(), 1)
        m = WeightMirror.objects.get()
        self.assertEqual((m.action, m.rev, m.payload['หมายเหตุ']), ('U', 1, 'b'))

    def test_same_row_id_other_company_is_separate(self):
        self.post([item(1)], comp_code='SLC')
        self.post([item(1)], comp_code='KP')
        self.assertEqual(WeightMirror.objects.count(), 2)

    def test_delete_marks_is_deleted(self):
        self.post([item(1)])
        self.post([item(1, action='D')])
        self.assertTrue(WeightMirror.objects.get().is_deleted)

    def test_bad_items_are_skipped_but_batch_succeeds(self):
        # ถ้าตอบ error ทั้งชุด ตาชั่งจะส่งชุดเดิมซ้ำไม่จบ
        response = self.post([item(1), {'table_name': 'weight', 'action': 'X'}, 'oops'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['saved'], 1)
        self.assertEqual(len(response.json()['skipped']), 2)

    def test_duplicate_key_in_one_batch_keeps_last(self):
        response = self.post([item(1, note='a'), item(1, action='U', rev=1, note='b')])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WeightMirror.objects.get().payload['หมายเหตุ'], 'b')

    def test_decimal_scale_is_kept(self):
        # json.dumps ทำ 12.340 ไม่ได้ จึงเขียน body เอง
        body = ('{"comp_code": "SLC", "items": [{"table_name": "weight", "row_id": "9", "action": "I",'
                ' "payload": {"weight_id": 9, "w": 12.340, "n": 5}}]}').encode('utf-8')
        response = self.client.generic('POST', self.url, body, content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        payload = WeightMirror.objects.get(row_id='9').payload
        self.assertEqual(payload['w'], '12.340')
        self.assertEqual(payload['n'], 5)

    def test_missing_comp_code_is_400(self):
        self.assertEqual(self.post([item(1)], comp_code='').status_code, 400)


class WeightMirrorListTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user('scale', 'scale@t.com', 'pw12345!'))
        WeightMirror.objects.create(comp_code='SLC', mine_code='M1', station_code='W1', table_name='weight',
                                    row_id='1', action='I', payload={'weight_id': 1}, record_date=date(2026, 11, 20))
        WeightMirror.objects.create(comp_code='SLC', mine_code='M1', station_code='W1', table_name='weight',
                                    row_id='2', action='I', payload={'weight_id': 2}, record_date=date(2026, 11, 23))
        WeightMirror.objects.create(comp_code='SLC', station_code='W2', table_name='weight', row_id='3', action='I',
                                    record_date=date(2026, 11, 23))

    def test_filters_by_station_and_date(self):
        response = self.client.get(reverse('weightMirrorList'), {'station_code': 'W1', 'date_from': '2026-11-21'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([r['row_id'] for r in data['results']], ['2'])
        self.assertIsNone(data['next'])

    def test_requires_station_code(self):
        # comp_code อย่างเดียวไม่พอ ตาชั่งหลายตัวใช้ comp_code เดียวกัน
        self.assertEqual(self.client.get(reverse('weightMirrorList'), {'comp_code': 'SLC'}).status_code, 400)


class CleanupWeightMirrorTests(TestCase):

    def test_deletes_only_old_rows(self):
        old = WeightMirror.objects.create(comp_code='SLC', table_name='weight', row_id='1', action='I')
        WeightMirror.objects.create(comp_code='SLC', table_name='weight', row_id='2', action='I')
        WeightMirror.objects.filter(pk=old.pk).update(received_at=datetime.now() - timedelta(days=90))
        call_command('cleanup_weight_mirror', '--days', '60', stdout=StringIO())
        self.assertEqual(list(WeightMirror.objects.values_list('row_id', flat=True)), ['2'])


class WeightMirrorStationTests(TestCase):
    """ตาชั่งหลายตัวใช้ comp_code เดียวกัน ตอนกู้ต้องแยกตาม station_code"""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user('scale', 'scale@t.com', 'pw12345!'))
        for station, row_id in (('W1', '1'), ('W1', '2'), ('W2', '3')):
            body = {'comp_code': 'SLC', 'mine_code': 'M1', 'station_code': station, 'items': [item(row_id)]}
            self.client.post(reverse('weightMirrorBulk'), body, format='json')

    def test_bulk_saves_station_code(self):
        self.assertEqual(WeightMirror.objects.get(row_id='3').station_code, 'W2')

    def test_list_filters_by_station(self):
        data = self.client.get(reverse('weightMirrorList'), {'station_code': 'W1'}).json()
        self.assertEqual(sorted(r['row_id'] for r in data['results']), ['1', '2'])

    def test_stations_summary_by_station_code(self):
        data = self.client.get(reverse('weightMirrorStations'), {'station_code': 'W1'}).json()
        self.assertEqual([(r['comp_code'], r['station_code'], r['count']) for r in data['results']],
                         [('SLC', 'W1', 2)])
        self.assertEqual(data['results'][0]['last_record_date'], '2026-11-23')

    def test_stations_requires_station_code(self):
        self.assertEqual(self.client.get(reverse('weightMirrorStations'), {'comp_code': 'SLC'}).status_code, 400)

    def test_stations_returns_first_weight_date(self):
        BaseWeightStation.objects.create(id='W1', des='W1')
        for weight_id, day in ((1, date(2025, 3, 1)), (2, date(2026, 1, 5))):
            Weight.objects.create(weight_id=weight_id, date=day, bws_id='W1')
        Weight.objects.create(weight_id=3, date=date(2024, 1, 1))  # ตาชั่งอื่น/ไม่มี bws ไม่นับ
        data = self.client.get(reverse('weightMirrorStations'), {'station_code': 'W1'}).json()
        self.assertEqual(data['weight_first_date'], '2025-03-01')
        self.assertIsNone(self.client.get(reverse('weightMirrorStations'), {'station_code': 'W9'}).json()['weight_first_date'])


class WeightMirrorWeightByIdsTests(TestCase):
    """ตาชั่งเช็คว่า weight_id ของสำเนามีบน server แล้วหรือยัง"""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user('scale', 'scale@t.com', 'pw12345!'))
        BaseWeightStation.objects.create(id='W1', des='W1')
        BaseWeightStation.objects.create(id='W2', des='W2')
        Weight.objects.create(weight_id=1, date=date(2026, 1, 1), bws_id='W1', note='server')
        Weight.objects.create(weight_id=2, date=date(2026, 1, 1), bws_id='W2')

    def test_returns_only_found_rows_of_this_station(self):
        data = self.client.get(reverse('weightMirrorWeightByIds'), {'station_code': 'W1', 'ids': '1,2,3'}).json()
        self.assertEqual([(r['weight_id'], r['note']) for r in data['results']], [(1, 'server')])

    def test_bad_input_is_400(self):
        url = reverse('weightMirrorWeightByIds')
        self.assertEqual(self.client.get(url, {'ids': '1'}).status_code, 400)
        self.assertEqual(self.client.get(url, {'station_code': 'W1', 'ids': '1,x'}).status_code, 400)
        many = ','.join(str(i) for i in range(501))
        self.assertEqual(self.client.get(url, {'station_code': 'W1', 'ids': many}).status_code, 400)
