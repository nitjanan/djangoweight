# -*- coding: utf-8 -*-
"""ค่าที่ตกลงกันตอนทำสัญญาในแถวทีม : ค่าขนส่งตามสัญญา / ราคาน้ำมันฐานวันทำสัญญา / วันทำสัญญา

issue #125 : ค่าสัญญาเป็นตัวตั้งของค่าขนส่งที่จ่าย (บังคับกรอก) แทนช่อง "ค่าขนส่ง" รายแถวที่เลิกใช้
    ค่าขนส่งที่จ่าย = ค่าขนส่งตามสัญญา + (ราคาน้ำมันเฉลี่ย − น้ำมันฐานวันทำสัญญา) × ปรับตามน้ำมัน
น้ำมันฐานวันทำสัญญาเป็นช่วงได้ (ขอบล่าง / ขอบบน) ราคาเฉลี่ยอยู่ในช่วง = ไม่ปรับ หลุดขอบไหนวัดจากขอบนั้น
ไฟล์รายงานรายเที่ยว (template v17) คิดสูตรนี้ในชีตอัตรา : ส่วนปรับ L / อัตราสุทธิ M = G + L
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

    def test_contract_values_are_required(self):
        """#125 : ค่าสัญญา 2 ช่องเป็นตัวตั้งของค่าขนส่งที่จ่าย ขาดช่องไหนต้องบันทึกไม่ได้"""
        serializer = InternationalFreightRateSerializer(data=self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00'},
        ], fill_contract=False))
        self.assertFalse(serializer.is_valid())
        errors = serializer.errors['teams'][0]
        self.assertIn('contract_freight_rate', errors)
        self.assertIn('contract_base_fuel_price', errors)

    def test_contract_fuel_may_be_a_range(self):
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1150.00',
             'contract_base_fuel_price': '30.00', 'contract_base_fuel_price_max': '30.99'},
            {'team_id': self.team.pk, 'weight_carried': self.band_high.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1300.00',
             'contract_base_fuel_price': '31.00'},
        ])
        by_band = {t.weight_carried_id: t for t in rate.teams.all()}
        self.assertEqual(by_band[self.band_low.id].contractFuelLabel(), '30.00 - 30.99')
        self.assertEqual(by_band[self.band_high.id].contractFuelLabel(), '31.00')   # ราคาเดียว

    def test_contract_fuel_same_value_on_both_bounds_counts_as_single_price(self):
        """ราคาเดียวให้ใส่เลขเดิมทั้งสองช่อง ต้องอ่านผลเท่ากับแถวเก่าที่เว้นขอบบนไว้

        สูตรในไฟล์ Excel ใช้ IF(I="",H,I) อยู่แล้ว สองแบบนี้จึงคิดเงินออกมาเท่ากัน
        เหลือแค่ตอนแสดงผลที่ต้องไม่ขึ้นเป็น "31.00 - 31.00"
        """
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1150.00',
             'contract_base_fuel_price': '31.00', 'contract_base_fuel_price_max': '31.00'},
        ])
        row = rate.teams.get()
        self.assertTrue(row.contractFuelIsSingle())
        self.assertEqual(row.contractFuelLabel(), '31.00')

    def test_contract_fuel_upper_bound_must_not_be_below_lower(self):
        serializer = InternationalFreightRateSerializer(data=self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1150.00',
             'contract_base_fuel_price': '31.00', 'contract_base_fuel_price_max': '30.00'},
        ]))
        self.assertFalse(serializer.is_valid())
        self.assertIn('contract_base_fuel_price_max', serializer.errors['teams'][0])

    def test_changing_contract_fuel_upper_bound_issues_new_version(self):
        row = {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
               'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1150.00',
               'contract_base_fuel_price': '30.00', 'contract_base_fuel_price_max': '30.99'}
        rate = self.createRate([row])
        serializer = InternationalFreightRateSerializer(
            rate, data=self.basePayload([dict(row, contract_base_fuel_price_max='31.49')]), partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertNotEqual(updated.id, rate.id)
        self.assertEqual(updated.teams.get().contract_base_fuel_price_max, Decimal('31.49'))

    def test_freight_rate_is_ignored_and_per_ton_km_follows_contract(self):
        """#125 : ช่องค่าขนส่งรายแถวเลิกใช้ ส่งมาก็ไม่เก็บ บาท/ตัน/กม. คิดจากค่าขนส่งตามสัญญาแทน"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '9999.00', 'fuel_freight_adjustment': '1.00',
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75'},
        ])
        row = rate.teams.get()
        self.assertIsNone(row.freight_rate)
        self.assertEqual(row.freight_rate_per_ton_km, Decimal('2.56'))   # 1150 / 450

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

    def test_approval_memo_writes_contract_fuel_range_as_text(self):
        import openpyxl
        from weightapp import views
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1150.00',
             'contract_base_fuel_price': '30.00', 'contract_base_fuel_price_max': '30.99'},
        ])
        worksheet = openpyxl.Workbook().active
        views._ifrExportWriteTeamRow(worksheet, 10, list(rate.teams.all()), {self.band_low: 7},
                                     payment_col=40, note_col=41, rate=rate)
        self.assertEqual(worksheet.cell(row=10, column=9).value, '30.00 - 30.99')

    def test_approval_memo_writes_contract_values_into_their_band(self):
        """ไฟล์บันทึกขออนุมัติ : ตามสัญญา เดิม/ใหม่ แล้วตามด้วยน้ำมันฐานวันทำสัญญา / วันทำสัญญา"""
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
        self.assertIsNone(cell(0))                 # ตามสัญญา เดิม : ใบแรก ไม่มีฉบับก่อนหน้า
        self.assertEqual(cell(1), 1150.0)          # ตามสัญญา ใหม่
        self.assertEqual(cell(2), 29.75)           # น้ำมันฐานวันทำสัญญา
        self.assertEqual(cell(3), '01/03/2569')    # วันทำสัญญา (พ.ศ.)
        self.assertEqual(cell(4), '± 1.00')        # น้ำมัน ± 1
        self.assertEqual(cell(5), 2.56)            # บาท/ตัน/กม. = ตามสัญญา 1150 / ระยะทาง 450

    def exportMemo(self):
        from io import BytesIO
        from django.contrib.auth.models import User
        from django.test import override_settings
        from weightapp.models import InternationalFreightRate, InternationalFreightRateStatus, UserProfile
        InternationalFreightRate.objects.update(status=InternationalFreightRateStatus.APPROVED,
                                                effective_date=date(2026, 1, 1))
        user = User.objects.create_user('acc', 'acc@t.com', 'pw12345!')
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'ROI'
        session.save()
        with override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'):
            response = self.client.get('/internationalFreightRate/excel/')
        self.assertEqual(response.status_code, 200)
        return openpyxl.load_workbook(BytesIO(response.content)).active

    def test_approval_memo_lists_remaining_teams_as_a_team_row(self):
        """แถวเส้นทางมีแค่ต้นทาง/ปลายทาง/ระยะทาง อัตราของแถว team = NULL ลงเป็นทีมลำดับแรก
        มีทีมเจาะจงอยู่ด้วยจึงเรียก "ทีมที่เหลือ" """
        self.createRate([
            {'team_id': None, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1100.00'},
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1150.00'},
        ])
        ws = self.exportMemo()
        route_row = views.IFR_EXPORT_FIRST_DATA_ROW
        new_col = views.IFR_EXPORT_FIXED_COLS + 2      # ตามสัญญา ใหม่ ของช่วงแรก
        self.assertEqual(ws.cell(row=route_row, column=2).value, 'ท่าต้นทางทดสอบ')
        self.assertIsNone(ws.cell(row=route_row, column=new_col).value)
        self.assertEqual(ws.cell(row=route_row + 1, column=2).value, '1. ทีมที่เหลือ')
        self.assertEqual(ws.cell(row=route_row + 1, column=new_col).value, 1100.0)
        self.assertEqual(ws.cell(row=route_row + 2, column=2).value, '2. ทีมทดสอบ A')
        self.assertEqual(ws.cell(row=route_row + 2, column=new_col).value, 1150.0)

    def test_approval_memo_calls_shared_row_all_teams_when_alone(self):
        self.createRate([
            {'team_id': None, 'weight_carried': self.band_low.id,
             'fuel_freight_adjustment': '1.00', 'contract_freight_rate': '1100.00'},
        ])
        ws = self.exportMemo()
        self.assertEqual(ws.cell(row=views.IFR_EXPORT_FIRST_DATA_ROW + 1, column=2).value, '1. ทุกทีม')


class TripReportRateSheetColumnTests(SimpleTestCase):
    """ไฟล์รายงานรายเที่ยว template v19 : คิดค่าขนส่งรายเที่ยวจากราคาน้ำมันวันที่วิ่ง

    ชีตอัตราค่าขนส่ง เหลือแค่เงื่อนไขสัญญา
      G ค่าขนส่งตามสัญญา / H-I น้ำมันฐานวันทำสัญญา ขอบล่าง-ขอบบน / J ปรับตามน้ำมัน / K คีย์ / L หมายเหตุ
    บันทึกรายเที่ยว N ราคาน้ำมันวันที่วิ่ง (ระบบเติม) / O อัตรา / P ค่าขนส่ง (สูตรในไฟล์)
    """

    def rateRow(self, **extra):
        row = {
            'team': 'ทีมทดสอบ', 'origin': 'เหมืองทดสอบ', 'destination': 'ท่าเรือทดสอบ',
            'weight_carried': 'แบก นน.', 'stone': 'หินทดสอบ', 'distance': Decimal('450'),
            'contract_freight_rate': Decimal('1150.00'), 'contract_base_fuel_price': Decimal('29.75'),
            'contract_base_fuel_price_max': Decimal('30.50'), 'fuel_freight_adjustment': Decimal('15.00'),
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
        self.assertEqual(ws['H5'].value, 29.75)         # น้ำมันฐานวันทำสัญญา ขอบล่าง
        self.assertEqual(ws['I5'].value, 30.5)          # น้ำมันฐานวันทำสัญญา ขอบบน
        self.assertEqual(ws['J5'].value, 15.0)          # ปรับค่าขนส่ง
        self.assertIsNone(ws['L5'].value)               # มีค่าสัญญาครบ ไม่มีหมายเหตุ

    def test_key_formula_is_not_overwritten(self):
        ws = self.writeSheet([self.rateRow()])[views.EXPORT_DOC_RATE_SHEET]
        self.assertTrue(ws['K5'].value.startswith('=IF(OR($A5="",$B5="",$C5="",$D5="",$E5="")'))
        self.assertTrue(ws['K204'].value.startswith('=IF(OR($A204="",'))

    def test_missing_contract_values_get_a_note(self):
        """ใบเก่าที่ไม่มีค่าสัญญา : เว้นว่าง (ไม่ใช่ 0) และบอกเหตุผลไว้ในช่องหมายเหตุ"""
        ws = self.writeSheet([
            self.rateRow(contract_freight_rate=None, contract_base_fuel_price=None,
                         contract_base_fuel_price_max=None),
            self.rateRow(contract_base_fuel_price=None, contract_base_fuel_price_max=None),
        ])[views.EXPORT_DOC_RATE_SHEET]
        self.assertIsNone(ws['G5'].value)
        self.assertIsNone(ws['H5'].value)
        self.assertIsNone(ws['I5'].value)
        self.assertIn('ไม่มีค่าขนส่งตามสัญญา', ws['L5'].value)
        self.assertIn('ไม่ปรับตามน้ำมัน', ws['L6'].value)

    def test_sample_rows_are_cleared(self):
        """แถวตัวอย่างสีเหลืองของ template (แถว 5) ต้องหายหมด"""
        ws = self.writeSheet([])[views.EXPORT_DOC_RATE_SHEET]
        for col in 'ABCDEFGHIJL':
            self.assertIsNone(ws['%s5' % col].value, col)

    def test_template_headers_match_column_numbers(self):
        """ตัวเลขคอลัมน์ใน views กับหัวตารางในไฟล์ template ต้องเดินตรงกัน"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        ws = workbook[views.EXPORT_DOC_RATE_SHEET]

        def header(col):
            return (ws.cell(row=4, column=col).value or '').replace('\n', ' ')

        expected = (
            (views.EXPORT_DOC_RATE_CONTRACT_RATE_COL, 'อัตราค่าขนส่ง ตามสัญญา'),
            (views.EXPORT_DOC_RATE_CONTRACT_FUEL_COL, 'น้ำมันฐานวันทำสัญญา ขอบล่าง'),
            (views.EXPORT_DOC_RATE_CONTRACT_FUEL_MAX_COL, 'น้ำมันฐานวันทำสัญญา ขอบบน'),
            (views.EXPORT_DOC_RATE_ADJUST_COL, 'ปรับค่าขนส่ง'),
        )
        for col, text in expected:
            self.assertTrue(header(col).startswith(text), '%s : %r' % (col, header(col)))
        # L ว่างไว้ให้ระบบเขียนหัว "หมายเหตุ" ตอน export
        self.assertEqual(header(views.EXPORT_DOC_RATE_NOTE_COL), '')
        # ราคาเฉลี่ย / ส่วนปรับ / อัตราสุทธิ รายเดือนต้องไม่อยู่ในชีตนี้แล้ว
        texts = ' '.join(header(c) for c in range(1, 30))
        for gone in ('ราคาน้ำมันเฉลี่ย', 'ส่วนปรับน้ำมัน', 'อัตราสุทธิ'):
            self.assertNotIn(gone, texts)

        trip = workbook['บันทึกรายเที่ยว']
        self.assertTrue(trip.cell(row=5, column=views.EXPORT_DOC_TRIP_FUEL_COL).value.startswith('ราคาน้ำมัน'))
        self.assertTrue(trip['O5'].value.startswith('อัตราค่าขนส่ง'))
        self.assertTrue(trip['P5'].value.startswith('ค่าขนส่ง'))

    def test_trip_rate_formula_uses_daily_fuel_price(self):
        """อัตรารายเที่ยว O : อ่านเงื่อนไขสัญญาจากชีตอัตรา (แถว AE) แล้วเทียบกับราคาน้ำมัน N ของเที่ยวนั้น"""
        trip = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)['บันทึกรายเที่ยว']
        rate = trip['O6'].value
        self.assertIn('INDEX(อัตราค่าขนส่ง!$G$5:$G$204,$AE6)', rate)    # ตามสัญญา
        self.assertIn('INDEX(อัตราค่าขนส่ง!$J$5:$J$204,$AE6)', rate)    # ปรับ
        self.assertIn('IF($N6="","",', rate)                             # ไม่มีราคา = อัตราว่าง
        self.assertEqual(trip['P6'].value, '=IF(OR($A6="",$M6="",$O6=""),"",$M6*$O6)')
        self.assertIn('MATCH($Y6,อัตราค่าขนส่ง!$K$5:$K$204,0)', trip['AE6'].value)
        self.assertTrue(trip['O10005'].value.startswith('=IF($A10005="",'))

    def test_payment_summary_splits_lines_by_rate(self):
        """หน้าสรุปจ่าย : 1 บรรทัด = accKey + อัตรา (payKey AF) อัตราอ่านจาก O รายได้ = Σ P"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        trip = workbook['บันทึกรายเที่ยว']
        self.assertEqual(trip['AF6'].value, '=IF($Y6="","",$Y6&"|"&IF($O6="","-",TEXT($O6,"0.00")))')
        pay = workbook['สรุปจ่ายรถร่วม']
        self.assertIn('บันทึกรายเที่ยว!$AF$6:$AF$10005', pay['R5'].value)
        self.assertIn('บันทึกรายเที่ยว!$AF$6:$AF$10005', pay['AR5'].value)
        self.assertIn('บันทึกรายเที่ยว!$O$6:$O$10005', pay['BD5'].value)     # อัตรา
        self.assertIn('บันทึกรายเที่ยว!$P$6:$P$10005', pay['AU5'].value)     # รายได้
        self.assertIn('อัตราค่าขนส่ง!$G$5:$G$204', pay['AT404'].value)       # ตามสัญญา (ซ่อน)

    def test_summary_headers_follow_accounting_layout(self):
        """หัวตารางหน้าสรุปเหมือนไฟล์บัญชีเดิม (ส่งออก ด.5-69)
        สรุปจ่าย ซ่อนตามสัญญา/ส่วนปรับ เหลือ อัตราค่าขนส่ง (บาท/ตัน) คู่ (บาท/กม.)
        สรุปเหมือง มีหัวใหญ่ "อัตราค่าขนส่ง" ครอบสองคอลัมน์นี้"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        pay = workbook['สรุปจ่ายรถร่วม']
        self.assertTrue(pay.column_dimensions['G'].hidden)
        self.assertEqual([pay['I%d' % r].value for r in (2, 3, 4)], ['อัตรา', 'ค่าขนส่ง', '(บาท/ตัน)'])
        self.assertEqual([pay['J%d' % r].value for r in (2, 3, 4)], ['อัตรา', 'ค่าขนส่ง', '(บาท/กม.)'])

        mine = workbook['สรุปเหมือง']
        self.assertEqual(mine['I7'].value, 'อัตราค่าขนส่ง')
        self.assertIn('I7:J7', {str(m) for m in mine.merged_cells.ranges})
        self.assertEqual((mine['I8'].value, mine['J8'].value), ('(บาท/ตัน)', '(บาท/กม.)'))
        # อัตราแถวทีม = ค่าขนส่งรวม (P ของเที่ยวในกลุ่ม) ÷ ตันจ่ายรวม
        self.assertIn('บันทึกรายเที่ยว!$P$6:$P$10005', mine['AM9'].value)
        self.assertEqual(mine['AK9'].value, '=IF($W9="","",IF(N($AJ9)=0,0,ROUND($AM9/$AJ9,2)))')
