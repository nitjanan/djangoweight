# -*- coding: utf-8 -*-
"""หน้า /admin/weightapp/weight/ : ตัวกรองช่วงวันที่ (DateRangeListFilter ใน admin.py)"""
import csv
import io
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from weightapp.models import Weight

URL = '/admin/weightapp/weight/'


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class WeightAdminDateFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        for weight_id, day in ((1, date(2026, 8, 31)), (2, date(2026, 9, 1)), (3, date(2026, 9, 2)),
                               (4, date(2026, 9, 3)), (5, date(2026, 9, 4))):
            Weight.objects.create(weight_id=weight_id, date=day, doc_id='D%d' % weight_id)

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('admin', 'a@t.com', 'pw12345!'))

    def ids(self, response):
        return {w.weight_id for w in response.context['cl'].result_list}

    def test_filter_shows_on_the_page(self):
        html = self.client.get(URL).content.decode('utf-8')
        self.assertIn('name="date__gte"', html)
        self.assertIn('name="date__lte"', html)

    def test_range_is_inclusive(self):
        response = self.client.get(URL, {'date__gte': '2026-09-01', 'date__lte': '2026-09-03'})
        self.assertEqual(self.ids(response), {2, 3, 4})

    def test_only_one_side(self):
        self.assertEqual(self.ids(self.client.get(URL, {'date__gte': '2026-09-03'})), {4, 5})
        self.assertEqual(self.ids(self.client.get(URL, {'date__lte': '2026-08-31'})), {1})

    def test_form_keeps_values_and_other_params(self):
        """กดกรองวันที่แล้วคำค้นเดิมต้องไม่หาย และช่องวันที่ต้องโชว์ค่าที่เลือกอยู่"""
        html = self.client.get(URL, {'date__gte': '2026-09-01', 'q': 'D'}).content.decode('utf-8')
        self.assertIn('value="2026-09-01"', html)
        self.assertIn('name="q" value="D"', html)
        self.assertIn('ล้าง</a>', html)

    def test_export_uses_the_same_range(self):
        response = self.client.post(URL + 'export/?date__gte=2026-09-01&date__lte=2026-09-03',
                                    {'file_format': '0'})
        self.assertEqual(response.status_code, 200)
        body = (b''.join(response.streaming_content) if response.streaming
                else response.content).decode('utf-8-sig')
        rows = list(csv.DictReader(io.StringIO(body)))
        self.assertEqual({int(r['weight_id']) for r in rows}, {2, 3, 4})
