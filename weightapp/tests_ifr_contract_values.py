# -*- coding: utf-8 -*-
"""ค่าที่ตกลงกันตอนทำสัญญาในแถวทีม : ค่าขนส่งตามสัญญา / ราคาน้ำมันฐานวันทำสัญญา / วันทำสัญญา

ตอนนี้เก็บไว้อ้างอิงอย่างเดียว ยังไม่มีสูตรไหนเอาไปคิดเงิน เทสต์จึงคุมแค่
การเก็บค่า (รายแถว ทีมเดียวกันต่างกันได้) และการออกเวอร์ชันใหม่
ไฟล์รายงานรายเที่ยวโชว์ค่าสัญญาในชีตอัตรา (G/H) ให้บัญชีเห็นเฉย ๆ สูตรในไฟล์คิดจากค่าขนส่ง (J)
"""
from datetime import date
from decimal import Decimal

import openpyxl
from django.test import SimpleTestCase, TestCase

from weightapp import views, xlsx_template

from weightapp.serializers import InternationalFreightRateSerializer
from weightapp.tests_ifr_fuel_adjustment import IfrRateFixtureMixin


class IfrContractValueTests(IfrRateFixtureMixin, TestCase):

    def test_contract_values_are_saved(self):
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75'},
        ])
        row = rate.teams.get()
        self.assertEqual(row.contract_freight_rate, Decimal('1150.00'))
        self.assertEqual(row.contract_base_fuel_price, Decimal('29.75'))

    def test_contract_values_are_optional(self):
        """ใบเก่าไม่เคยกรอก ปล่อยว่างต้องบันทึกได้ และต้องเป็น NULL ไม่ใช่ 0"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00'},
        ])
        row = rate.teams.get()
        self.assertIsNone(row.contract_freight_rate)
        self.assertIsNone(row.contract_base_fuel_price)

    def test_contract_freight_rate_may_differ_per_weight_band(self):
        """สัญญาระบุราคาแยกตามช่วงแบก นน. อยู่แล้ว ช่องนี้จึงต่างกันได้ในทีมเดียวกัน"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75'},
            {'team_id': self.team.pk, 'weight_carried': self.band_high.id,
             'freight_rate': '1350.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1300.00', 'contract_base_fuel_price': '29.75'},
        ])
        by_band = {t.weight_carried_id: t.contract_freight_rate for t in rate.teams.all()}
        self.assertEqual(by_band[self.band_low.id], Decimal('1150.00'))
        self.assertEqual(by_band[self.band_high.id], Decimal('1300.00'))

    def test_same_team_may_sign_each_band_on_a_different_day(self):
        """ทีมเดียวกันคนละช่วงแบก นน. ทำสัญญาคนละวัน ราคาน้ำมันวันนั้นจึงต่างกันได้"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_base_fuel_price': '29.75', 'contract_date': '2026-03-01'},
            {'team_id': self.team.pk, 'weight_carried': self.band_high.id,
             'freight_rate': '1350.00', 'fuel_freight_adjustment': '1.00',
             'contract_base_fuel_price': '31.20', 'contract_date': '2026-06-15'},
        ])
        by_band = {t.weight_carried_id: t for t in rate.teams.all()}
        self.assertEqual(by_band[self.band_low.id].contract_base_fuel_price, Decimal('29.75'))
        self.assertEqual(by_band[self.band_high.id].contract_base_fuel_price, Decimal('31.20'))
        self.assertEqual(by_band[self.band_low.id].contract_date, date(2026, 3, 1))
        self.assertEqual(by_band[self.band_high.id].contract_date, date(2026, 6, 15))

    def test_contract_date_is_optional(self):
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00'},
        ])
        self.assertIsNone(rate.teams.get().contract_date)

    def test_changing_contract_date_issues_new_version(self):
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_date': '2026-03-01'},
        ])
        serializer = InternationalFreightRateSerializer(rate, data=self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_date': '2026-04-01'},
        ]), partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertNotEqual(updated.id, rate.id)
        self.assertEqual(updated.teams.get().contract_date, date(2026, 4, 1))
        rate.refresh_from_db()
        self.assertEqual(rate.teams.get().contract_date, date(2026, 3, 1))

    def test_negative_contract_value_is_rejected(self):
        for field in ('contract_freight_rate', 'contract_base_fuel_price'):
            row = {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
                   'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
                   field: '-1.00'}
            serializer = InternationalFreightRateSerializer(data=self.basePayload([row]))
            self.assertFalse(serializer.is_valid(), '%s ติดลบไม่ควรผ่าน' % field)

    def test_changing_contract_value_issues_new_version(self):
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75'},
        ])
        payload = self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1180.00', 'contract_base_fuel_price': '29.75'},
        ])
        serializer = InternationalFreightRateSerializer(rate, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertNotEqual(updated.id, rate.id)
        self.assertEqual(updated.version, rate.version + 1)
        self.assertEqual(updated.teams.get().contract_freight_rate, Decimal('1180.00'))
        # ใบเดิมต้องไม่ถูกแตะ เดือนที่ปิดไปแล้วจะได้ตัวเลขเดิม
        rate.refresh_from_db()
        self.assertEqual(rate.teams.get().contract_freight_rate, Decimal('1150.00'))

    def test_saving_without_changes_does_not_create_version(self):
        teams = [
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75'},
        ]
        rate = self.createRate(teams)
        serializer = InternationalFreightRateSerializer(
            rate, data=self.basePayload(teams), partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().id, rate.id)

    def test_new_version_carries_contract_values_when_teams_not_sent(self):
        """แก้แค่ช่องของใบ (ไม่ส่ง teams มา) ค่าสัญญาของทุกแถวต้องยกตามไปใบใหม่"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75',
             'contract_date': '2026-03-01'},
        ])
        payload = self.basePayload([])
        payload.pop('teams')
        payload['distance'] = '480.00'
        serializer = InternationalFreightRateSerializer(rate, data=payload, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        row = updated.teams.get()
        self.assertEqual(row.contract_freight_rate, Decimal('1150.00'))
        self.assertEqual(row.contract_base_fuel_price, Decimal('29.75'))
        self.assertEqual(row.contract_date, date(2026, 3, 1))

    def test_approval_memo_writes_contract_values_into_their_band(self):
        """ไฟล์บันทึกขออนุมัติ : 3 ช่องสัญญาอยู่หน้าสุดของกลุ่มช่วงน้ำหนัก ตามด้วยเดิม/ใหม่"""
        import openpyxl
        from weightapp import views
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75',
             'contract_date': '2026-03-01'},
        ])
        worksheet = openpyxl.Workbook().active
        start = 7
        views._ifrExportWriteTeamRow(worksheet, 10, list(rate.teams.all()), {self.band_low: start},
                                     payment_col=40, note_col=41, rate=rate)
        cell = lambda offset: worksheet.cell(row=10, column=start + offset).value
        self.assertEqual(cell(0), 1150.0)          # ตามสัญญา
        self.assertEqual(cell(1), 29.75)           # น้ำมันฐานวันทำสัญญา
        self.assertEqual(cell(2), '01/03/2569')    # วันทำสัญญา (พ.ศ.)
        self.assertIsNone(cell(3))                 # เดิม : ใบแรก ไม่มีฉบับก่อนหน้า
        self.assertEqual(cell(4), 1200.0)          # ใหม่
        self.assertEqual(cell(5), '± 1.00')        # น้ำมัน ± 1


class TripReportRateSheetColumnTests(SimpleTestCase):
    """ชีต อัตราค่าขนส่ง ของไฟล์รายงานรายเที่ยว (template v15)

    G ค่าขนส่งตามสัญญา / H น้ำมันฐานวันทำสัญญา = โชว์เฉย ๆ
    J ค่าขนส่งในใบราคา = ตัวตั้งของสูตรอัตราสุทธิ N = ROUND(J + ส่วนปรับ M, 2)
    """

    def rateRow(self, **extra):
        row = {
            'team': 'ทีมทดสอบ', 'origin': 'เหมืองทดสอบ', 'destination': 'ท่าเรือทดสอบ',
            'weight_carried': 'แบก นน.', 'stone': 'หินทดสอบ', 'distance': Decimal('450'),
            'contract_freight_rate': Decimal('1150.00'), 'contract_base_fuel_price': Decimal('29.75'),
            'base_fuel_range': '30.00 - 35.00', 'freight_rate': Decimal('1153.75'),
            'average_fuel_price': Decimal('36.50'), 'fuel_freight_adjustment': Decimal('15.00'),
            'base_fuel_price': Decimal('30.00'), 'base_fuel_price_max': Decimal('35.00'),
            'fuel_note': 'หมายเหตุทดสอบ',
        }
        row.update(extra)
        return row

    def writeSheet(self, rows):
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        views._exportDocumentWriteRateSheet(workbook, rows)
        return workbook

    def test_values_land_in_their_columns(self):
        ws = self.writeSheet([self.rateRow()])[views.EXPORT_DOC_RATE_SHEET]
        self.assertEqual(ws['F5'].value, 450.0)
        self.assertEqual(ws['G5'].value, 1150.0)        # ตามสัญญา
        self.assertEqual(ws['H5'].value, 29.75)         # น้ำมันฐานวันทำสัญญา
        self.assertEqual(ws['I5'].value, '30.00 - 35.00')
        self.assertEqual(ws['J5'].value, 1153.75)       # ค่าขนส่ง ตัวตั้งที่ใช้คิด
        self.assertEqual(ws['K5'].value, 36.5)          # ราคาน้ำมันเฉลี่ย
        self.assertEqual(ws['L5'].value, 15.0)          # ปรับค่าขนส่ง
        self.assertEqual(ws['P5'].value, 'หมายเหตุทดสอบ')
        self.assertEqual(ws['V5'].value, 35.0)          # ขอบบน
        self.assertEqual(ws['X5'].value, 30.0)          # ขอบล่าง

    def test_formulas_are_not_overwritten(self):
        ws = self.writeSheet([self.rateRow()])[views.EXPORT_DOC_RATE_SHEET]
        self.assertEqual(ws['N5'].value, '=IF($J5="","",ROUND(N($J5)+N($M5),2))')
        self.assertEqual(ws['M5'].value, '=IF(OR($X5="",$K5="",$L5="",$W5=""),0,ROUND($W5*$L5,2))')
        self.assertTrue(ws['O5'].value.startswith('=IF(OR($A5="",$B5="",$C5="",$D5="",$E5="")'))
        self.assertTrue(ws['W5'].value.startswith('=IF(OR($X5="",$K5=""),"",IF($K5<$X5,$K5-$X5,'))

    def test_missing_contract_values_stay_blank(self):
        """ใบที่ยังไม่ได้กรอกค่าสัญญา ต้องเว้นว่าง ไม่ใช่ 0 และค่าขนส่งยังลงตามปกติ"""
        ws = self.writeSheet([self.rateRow(contract_freight_rate=None,
                                           contract_base_fuel_price=None)])[views.EXPORT_DOC_RATE_SHEET]
        self.assertIsNone(ws['G5'].value)
        self.assertIsNone(ws['H5'].value)
        self.assertEqual(ws['J5'].value, 1153.75)

    def test_sample_rows_are_cleared(self):
        """แถวตัวอย่างสีเหลืองของ template (แถว 5) ต้องหายหมด รวม 2 คอลัมน์ใหม่"""
        ws = self.writeSheet([])[views.EXPORT_DOC_RATE_SHEET]
        for col in 'ABCDEFGHIJKLP':
            self.assertIsNone(ws['%s5' % col].value, col)

    def test_template_headers_match_column_numbers(self):
        """ตัวเลขคอลัมน์ใน views กับหัวตารางในไฟล์ template ต้องเดินตรงกัน"""
        ws = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)[views.EXPORT_DOC_RATE_SHEET]

        def header(col):
            return (ws.cell(row=4, column=col).value or '').replace('\n', ' ')

        expected = (
            (views.EXPORT_DOC_RATE_CONTRACT_RATE_COL, 'อัตราค่าขนส่ง ตามสัญญา'),
            (views.EXPORT_DOC_RATE_CONTRACT_FUEL_COL, 'น้ำมันฐานวันทำสัญญา'),
            (views.EXPORT_DOC_RATE_BASE_RANGE_COL, 'ราคาน้ำมันฐาน (บาท/ลิตร)'),
            (views.EXPORT_DOC_RATE_FREIGHT_COL, 'ค่าขนส่ง ณ ราคาน้ำมันฐาน (บาท/ตัน)'),
            (views.EXPORT_DOC_RATE_AVG_FUEL_COL, 'ราคาน้ำมันเฉลี่ย'),
            (views.EXPORT_DOC_RATE_ADJUST_COL, 'ปรับค่าขนส่ง'),
            (views.EXPORT_DOC_RATE_BASE_MAX_COL, 'ราคาน้ำมันฐาน ขอบบน'),
            (views.EXPORT_DOC_RATE_BASE_MIN_COL, 'ราคาน้ำมันฐาน ขอบล่าง'),
        )
        for col, text in expected:
            self.assertTrue(header(col).startswith(text), '%s : %r' % (col, header(col)))
        # P ว่างไว้ให้ระบบเขียนหัว "หมายเหตุราคาน้ำมัน" ตอน export
        self.assertEqual(header(views.EXPORT_DOC_RATE_NOTE_COL), '')

    def test_payment_summary_uses_freight_rate_column(self):
        """หน้าสรุปจ่ายโชว์ อัตรา ณ น้ำมันฐาน + ส่วนปรับ = อัตราสุทธิ ต้องดึงช่อง J ไม่ใช่ค่าตามสัญญา G
        และช่องตรวจ BF4 นับแถวที่ช่องนี้เป็น 0 ถ้าดึง G ผิดตัว จะฟ้องว่าอัตรายังไม่ได้กรอกทั้งที่มีราคา"""
        pay = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)['สรุปจ่ายรถร่วม']
        self.assertIn('อัตราค่าขนส่ง!$J$5:$J$204', pay['AT5'].value)
        self.assertIn('อัตราค่าขนส่ง!$J$5:$J$204', pay['AT404'].value)
        self.assertIn('อัตราค่าขนส่ง!$N$5:$N$204', pay['BD5'].value)
        self.assertEqual(pay['G2'].value, 'อัตรา ณ')
        self.assertEqual(pay['G3'].value, 'น้ำมันฐาน')
