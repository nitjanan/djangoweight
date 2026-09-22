# -*- coding: utf-8 -*-
"""สำเนาบิลเติมน้ำมันจาก Express (ExpressFuelBillLine / ExpressFuelBillSync)

ไม่ต่อ Express จริง : แทนที่ _exportDocumentFetchExpressFuel ด้วยของปลอม
ให้คืนบิลตัวอย่างหรือโยน error ตามเคส แล้วดูว่า _exportDocumentFuelRefillsUncached
เขียนสำเนา / หยิบสำเนามาใช้ / ไม่แตะสำเนา ถูกต้องไหม
"""
from datetime import date
from decimal import Decimal
from unittest import mock

from django.test import TestCase

from weightapp import views
from weightapp.models import (BaseCarTeam, BaseCompany, BaseCompanyMapBaseCustomer,
                              ExpressFuelBillLine, ExpressFuelBillSync)

FETCH = 'weightapp.views._exportDocumentFetchExpressFuel'
JULY = date(2026, 7, 1)
JUNE = date(2026, 6, 1)


def raw_line(docnum, seqnum=1, day=21, litre='300.00', amount='10578.00'):
    return {
        'docnum': docnum, 'seqnum': seqnum, 'docdate': date(2026, 7, day),
        'cuscod': '92-V-001', 'comcod': 'SLC', 'stkdes': 'น้ำมันดีเซล',
        'ordqty': Decimal(litre), 'unitpr': Decimal('35.26'), 'trnval': Decimal(amount),
    }


COUNTS = {'bills': 5, 'no_team': 2, 'no_branch': 0, 'duplicate': 1}


def express_down(*args, **kwargs):
    raise views._ExpressFuelFetchError('ต่อฐานข้อมูล Express ไม่ได้ : ทดสอบ')


class ExpressFuelSnapshotTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.company = BaseCompany.objects.create(name='ศิลาชัย', code='SLC')
        BaseCompanyMapBaseCustomer.objects.create(
            name='สาขาทดสอบ', oi_soc_code='IO', base_company=cls.company)
        cls.team = BaseCarTeam.objects.create(
            car_team_id='TSNAP', car_team_name='ทีมสำเนา', oil_customer_id='92-V-001')

    def refills(self, month='2026-07'):
        return views._exportDocumentFuelRefillsUncached(month)

    def test_success_uses_express_and_saves_snapshot(self):
        with mock.patch(FETCH, return_value=([raw_line('IO1'), raw_line('IO2')], COUNTS)):
            lines, stats = self.refills()

        self.assertEqual(stats['source'], 'express')
        self.assertIsNone(stats['error'])
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]['team'], 'ทีมสำเนา')
        self.assertEqual(lines[0]['branch'], 'สาขาทดสอบ')
        self.assertEqual(lines[0]['company_id'], self.company.id)
        self.assertEqual(ExpressFuelBillLine.objects.filter(month=JULY).count(), 2)
        sync = ExpressFuelBillSync.objects.get(month=JULY)
        self.assertEqual((sync.lines, sync.bills, sync.no_team), (2, 5, 2))

    def test_failure_uses_latest_snapshot(self):
        with mock.patch(FETCH, return_value=([raw_line('IO1'), raw_line('IO2', day=22)], COUNTS)):
            online, _ = self.refills()
        with mock.patch(FETCH, side_effect=express_down):
            offline, stats = self.refills()

        self.assertEqual(stats['source'], 'snapshot')
        self.assertIn('ต่อฐานข้อมูล Express ไม่ได้', stats['error'])
        self.assertIsNotNone(stats['snapshot_at'])
        self.assertIn('2569', stats['snapshot_at_th'])
        # ตัวนับตอนทำสำเนายังอยู่ หัว sheet express จะได้บอกได้ว่าตอนนั้นเจอบิลกี่ใบ
        self.assertEqual(stats['bills'], 5)
        # สำเนาต้องให้ผลเหมือนตอนอ่านจาก Express ทุกช่อง
        self.assertEqual(offline, online)

    def test_failure_without_snapshot_returns_empty(self):
        with mock.patch(FETCH, side_effect=express_down):
            lines, stats = self.refills()

        self.assertEqual(lines, [])
        self.assertIsNone(stats['source'])
        self.assertIn('ต่อฐานข้อมูล Express ไม่ได้', stats['error'])

    def test_failure_does_not_touch_snapshot(self):
        with mock.patch(FETCH, return_value=([raw_line('IO1'), raw_line('IO2')], COUNTS)):
            self.refills()
        synced_at = ExpressFuelBillSync.objects.get(month=JULY).synced_at
        with mock.patch(FETCH, side_effect=express_down):
            self.refills()

        self.assertEqual(ExpressFuelBillLine.objects.filter(month=JULY).count(), 2)
        self.assertEqual(ExpressFuelBillSync.objects.get(month=JULY).synced_at, synced_at)

    def test_success_replaces_only_that_month(self):
        june = dict(raw_line('IO9'), docdate=date(2026, 6, 10))
        with mock.patch(FETCH, return_value=([raw_line('IO1'), raw_line('IO2')], COUNTS)):
            self.refills('2026-07')
        with mock.patch(FETCH, return_value=([june], COUNTS)):
            self.refills('2026-06')
        with mock.patch(FETCH, return_value=([raw_line('IO3')], COUNTS)):
            self.refills('2026-07')

        self.assertEqual(list(ExpressFuelBillLine.objects.filter(month=JULY)
                              .values_list('docnum', flat=True)), ['IO3'])
        self.assertEqual(ExpressFuelBillLine.objects.filter(month=JUNE).count(), 1)
        self.assertEqual(ExpressFuelBillSync.objects.get(month=JULY).lines, 1)

    def test_snapshot_is_resolved_with_current_team_mapping(self):
        """สำเนาเก็บรหัสดิบ ถ้าหลังทำสำเนาไปเปลี่ยนรหัสลูกค้าของทีม บรรทัดนั้นต้องไม่ถูกนับให้ทีมเดิม"""
        with mock.patch(FETCH, return_value=([raw_line('IO1')], COUNTS)):
            self.refills()
        BaseCarTeam.objects.filter(pk=self.team.pk).update(oil_customer_id='92-V-999')
        with mock.patch(FETCH, side_effect=express_down):
            lines, stats = self.refills()

        self.assertEqual(stats['source'], 'snapshot')
        self.assertEqual(lines, [])

    def test_month_with_no_bills_is_remembered(self):
        """อ่านสำเร็จแต่ไม่มีบิลเลย ต่างจากยังไม่เคยทำสำเนา ตอนต่อไม่ได้ต้องบอกว่าใช้สำเนา (ว่าง)"""
        with mock.patch(FETCH, return_value=([], COUNTS)):
            self.refills()
        with mock.patch(FETCH, side_effect=express_down):
            lines, stats = self.refills()

        self.assertEqual(lines, [])
        self.assertEqual(stats['source'], 'snapshot')
        self.assertEqual(ExpressFuelBillSync.objects.get(month=JULY).lines, 0)
