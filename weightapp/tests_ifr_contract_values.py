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
    """ไฟล์รายงานรายเที่ยว template v22 : ราคาน้ำมันเฉลี่ยทั้งเดือนของทีม (บิล Express) คิดเงินต่อชุดราคาทั้งเดือน

    ชีตคำนวณค่าขนส่ง (เดิมชื่อ อัตราค่าขนส่ง)
      G ค่าขนส่งตามสัญญา / H-I น้ำมันฐานวันทำสัญญา ขอบล่าง-ขอบบน / J ปรับตามน้ำมัน / K คีย์ / L หมายเหตุ
      M สาขาที่ใช้ราคา / N ราคาน้ำมันเฉลี่ย / O อัตรา / P เที่ยว / Q ตันรวม / R ค่าขนส่งทั้งเดือน
      ตารางน้ำมัน T-W (X เฉลี่ย) · ไม่มีตารางค่าขนส่งรายเที่ยวแล้ว (v20 เคยอยู่ W-AE)
    บันทึกรายเที่ยว เหลือ A-M (ไม่มีส่วนคิดค่าขนส่งแล้ว) ช่องตรวจ N-O
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
        # แถวหลังชุดราคาสุดท้ายล้างสูตรออก ให้ปุ่มเรียง (A4:R5) ไม่ถูก Excel ขยายลงไป
        self.assertEqual(ws.auto_filter.ref, 'A4:R5')
        self.assertIsNone(ws['K6'].value)
        self.assertIsNone(ws['K204'].value)

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
        # (N ราคาน้ำมันเฉลี่ยของทีม เป็นของ v20 อยู่นอกช่วง A-L)
        texts = ' '.join(header(c) for c in range(1, 13))
        for gone in ('ราคาน้ำมันเฉลี่ย', 'ส่วนปรับน้ำมัน', 'อัตราสุทธิ'):
            self.assertNotIn(gone, texts)

        self.assertEqual(header(views.EXPORT_DOC_RATE_FUEL_BRANCH_COL), 'สาขาที่ใช้ราคาน้ำมัน')
        self.assertTrue(header(14).startswith('ราคาน้ำมันเฉลี่ย'))     # N
        self.assertTrue(header(15).startswith('อัตราค่าขนส่ง'))        # O
        self.assertEqual([header(views.EXPORT_DOC_FUEL_TABLE_FIRST_COL + i) for i in range(4)],
                         ['ทีมรถร่วม', 'สาขาที่ไปเติม', 'ลิตรรวม', 'เงินรวม (บาท)'])

        trip = workbook['บันทึกรายเที่ยว']
        self.assertEqual(trip['E5'].value, 'ช่วงน้ำหนักที่แบก')
        self.assertEqual(trip['M5'].value, 'นน.จ่ายค่าบรรทุก (ตัน)')
        self.assertEqual(trip['N4'].value, 'ช่องตรวจทาน (ห้ามลบ)')      # ไม่มีคอลัมน์อัตรา/ค่าขนส่งแล้ว
        self.assertEqual([header(c) for c in (16, 17, 18)],
                         ['เที่ยว (ทั้งเดือน)', 'นน.จ่ายค่าบรรทุก (ตัน ทั้งเดือน)', 'ค่าขนส่งทั้งเดือน (บาท)'])
        self.assertEqual(header(views.EXPORT_DOC_FUEL_TABLE_FIRST_COL + 4), 'ราคาน้ำมันเฉลี่ย (บาท/ลิตร)')
        # ไม่มีอะไรต่อท้ายตารางน้ำมัน X แล้ว (v26 ตาราง Z-AE ย้ายไปชีต ราคาน้ำมันเฉลี่ย)
        self.assertFalse([c.coordinate for row in ws.iter_rows(min_col=views.EXPORT_DOC_FUEL_TABLE_FIRST_COL + 5)
                          for c in row if c.value is not None])

    def test_trip_rate_formula_reads_the_calc_sheet(self):
        """ค่าขนส่งต่อชุดราคาทั้งเดือน : R = อัตรา O x นน.จ่ายรวมของเที่ยวที่ตรงชุดราคานั้น (บันทึกรายเที่ยว AB = ลำดับชุดราคา)
        O คิดจากราคาน้ำมันเฉลี่ย N ซึ่งหาจากตารางน้ำมันด้วยทีม + สาขาในช่อง M"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        trip = workbook['บันทึกรายเที่ยว']
        calc = workbook[views.EXPORT_DOC_RATE_SHEET]
        self.assertEqual(calc['R5'].value,
                         '=IF(OR($K5="",$O5=""),"",ROUND($O5*SUMIF(บันทึกรายเที่ยว!$AB$6:$AB$10005,ROW()-4,'
                         'บันทึกรายเที่ยว!$AF$6:$AF$10005),2))')
        # v22 : เที่ยว / ตัน อ่านคอลัมน์ช่วย AE / AF (= ค่าจริง x สัดส่วนที่นามนี้จ่าย AD · ว่าง = ทั้งเที่ยว)
        self.assertIn('SUMIF(บันทึกรายเที่ยว!$AB$6:$AB$10005,ROW()-4,บันทึกรายเที่ยว!$AE$6:$AE$10005)',
                      calc['P204'].value)
        self.assertEqual(trip['AE6'].value, '=IF($A6="","",IF($AD6="",1,N($AD6)))')
        self.assertIn('MATCH($V6,คำนวณค่าขนส่ง!$K$5:$K$204,0)', trip['AB6'].value)
        self.assertEqual(trip['O12'].value, '=COUNTIF($AC$6:$AC$10005,"*|-")')   # เที่ยวที่ยังไม่มีราคาน้ำมัน
        # v26 : N = ราคาที่ใช้ของ (ทีม, สาขา M) จากชีต ราคาน้ำมันเฉลี่ย · ไม่มี "รวมทุกสาขา" แล้ว
        self.assertNotIn('รวมทุกสาขา', calc['N5'].value)
        self.assertIn('INDEX(ราคาน้ำมันเฉลี่ย!$A$30:$BZ$229,MATCH($A5,ราคาน้ำมันเฉลี่ย!$B$30:$B$229,0),'
                      'MATCH($M5,ราคาน้ำมันเฉลี่ย!$A$4:$BZ$4,0))', calc['N5'].value)
        # v27 : ช่องว่าง (Excel อ่านเป็น 0) / ไม่มีแถวทีม -> ราคาของสาขาส่วนบน · ไม่มีอีก = ว่าง
        self.assertEqual(calc['N5'].value,
                         '=IF(OR($A5="",$M5=""),"",IFERROR(ROUND(1/(1/INDEX(ราคาน้ำมันเฉลี่ย!$A$30:$BZ$229,'
                         'MATCH($A5,ราคาน้ำมันเฉลี่ย!$B$30:$B$229,0),MATCH($M5,ราคาน้ำมันเฉลี่ย!$A$4:$BZ$4,0))),2),'
                         'IFERROR(ROUND(1/(1/INDEX(ราคาน้ำมันเฉลี่ย!$G$6:$G$25,'
                         'MATCH($M5,ราคาน้ำมันเฉลี่ย!$B$6:$B$25,0))),2),"")))')
        self.assertTrue(calc['N204'].value.startswith('=IF(OR($A204="",$M204=""),"",IFERROR(ROUND(1/(1/'))
        self.assertIsNone(calc['AE5'].value)                   # ตาราง Z-AE ของ v25 ย้ายไปชีตใหม่แล้ว
        fuel = workbook[views.EXPORT_DOC_FUEL_SHEET]
        self.assertEqual(workbook.sheetnames.index(views.EXPORT_DOC_FUEL_SHEET),
                         workbook.sheetnames.index(views.EXPORT_DOC_RATE_SHEET) + 1)
        self.assertEqual(fuel['E6'].value, '=IF(OR($B6="",N($C6)=0),"",ROUND($D6/$C6,2))')
        self.assertEqual(fuel['G25'].value, '=IF($B25="","",IF(N($F25)>0,ROUND($F25,2),$E25))')
        self.assertTrue(fuel.row_dimensions[4].hidden)
        self.assertIn('IF($N5="","",', calc['O5'].value)      # ไม่มีราคาน้ำมัน = อัตราว่าง
        self.assertNotIn('วิธีกรอก', workbook.sheetnames)

    def test_fuel_branch_and_fuel_table_are_written(self):
        """M = สาขาที่ใช้ราคา / Q-T = ยอดลิตร-เงินของทีมที่มีเที่ยวในไฟล์เท่านั้น"""
        lines = [
            {'team': 'ทีมทดสอบ', 'branch': 'ศิลาชัย', 'company_id': 1, 'litre': Decimal('100'), 'amount': Decimal('4000')},
            {'team': 'ทีมทดสอบ', 'branch': 'ศิลาชัย', 'company_id': 1, 'litre': Decimal('50'), 'amount': Decimal('2100')},
            {'team': 'ทีมอื่น', 'branch': 'ศิลาชัย', 'company_id': 1, 'litre': Decimal('10'), 'amount': Decimal('400')},
        ]
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        views._exportDocumentWriteRateSheet(workbook, [self.rateRow(fuel_branch='ศิลาชัย')], None,
                                            lines, {'ทีมทดสอบ'})
        ws = workbook[views.EXPORT_DOC_RATE_SHEET]
        self.assertEqual(ws['M5'].value, 'ศิลาชัย')
        self.assertEqual([ws['%s5' % c].value for c in 'TUVW'], ['ทีมทดสอบ', 'ศิลาชัย', 150.0, 6100.0])
        self.assertIsNone(ws['T6'].value)
        self.assertTrue(ws['N5'].value.startswith('=IF(OR($A5="",$M5="")'))   # สูตรยังอยู่

    def test_fuel_sheet_lists_branches_and_teams(self):
        """ชีต ราคาน้ำมันเฉลี่ย : ส่วนบน = สาขาต้นทางที่มีเที่ยว (บิลทุกทีม รวมทีมที่ไม่อยู่ในไฟล์ / ไม่มีบิล = ว่างให้กรอก)
        ส่วนล่าง = ทีม x กลุ่มสาขา เที่ยว / ตันที่แบก / ราคาจากบิล / กรอกเอง / ราคาที่ใช้"""
        lines = [
            {'team': 'ทีมทดสอบ', 'branch': 'ศิลาชัย', 'company_id': 1, 'litre': Decimal('150'), 'amount': Decimal('6100')},
            {'team': 'ทีมอื่น', 'branch': 'ศิลาชัย', 'company_id': 1, 'litre': Decimal('10'), 'amount': Decimal('400')},
        ]
        trips = [{'team': 'ทีมทดสอบ', 'fuel_branch': 'ศิลาชัย', 'pay_weight': Decimal('30.5')},
                 {'team': 'ทีมทดสอบ', 'fuel_branch': 'ศิลาชัย', 'pay_weight': Decimal('20'), 'payer_share': Decimal('0.5')},
                 {'team': 'ทีม ข', 'fuel_branch': 'กงตาก', 'pay_weight': Decimal('40')}]
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        views._exportDocumentWriteFuelSheet(workbook, trips, lines)
        ws = workbook[views.EXPORT_DOC_FUEL_SHEET]
        # ส่วนบน เรียงแบบพจนานุกรม : กงตาก (ไม่มีบิล) / ศิลาชัย (160 ลิตร 6,500 บาท)
        self.assertEqual([[ws.cell(r, c).value for c in (2, 3, 4, 6)] for r in (6, 7)],
                         [['กงตาก', None, None, None], ['ศิลาชัย', 160.0, 6500.0, None]])
        # กลุ่ม C-G = กงตาก / H-L = ศิลาชัย · แถว 4 = คีย์สาขาเหนือคอลัมน์ราคาที่ใช้
        self.assertEqual((ws['C28'].value, ws['H28'].value, ws['G4'].value, ws['L4'].value),
                         ('กงตาก', 'ศิลาชัย', 'กงตาก', 'ศิลาชัย'))
        self.assertEqual((ws['B30'].value, ws['B31'].value), ('ทีม ข', 'ทีมทดสอบ'))
        self.assertEqual((ws['C30'].value, ws['D30'].value, ws['H30'].value), (1.0, 40.0, None))
        self.assertEqual((ws['H31'].value, ws['I31'].value), (1.5, 40.5))      # ครึ่งเที่ยวที่นามนี้จ่าย
        self.assertIn("SUMIFS('คำนวณค่าขนส่ง'!$W$5:$W$204,'คำนวณค่าขนส่ง'!$T$5:$T$204,$B31,"
                      "'คำนวณค่าขนส่ง'!$U$5:$U$204,L$4)", ws['J31'].value)
        self.assertEqual(ws['L31'].value,
                         '=IF($B31="","",IF(N(K31)>0,ROUND(K31,2),IF(J31<>"",J31,'
                         'IFERROR(INDEX($G$6:$G$25,MATCH(L$4,$B$6:$B$25,0)),""))))')
        self.assertEqual(ws['K31'].fill.start_color.rgb[-6:], 'FFF2CC')   # ช่องกรอกเอง
        # ทีมทดสอบไม่ได้วิ่งกงตาก : ไม่มีเที่ยว แต่มีสูตร / ช่องกรอก (กรอกเองได้)
        self.assertIsNone(ws['C31'].value)
        self.assertTrue(ws['G31'].value.startswith('=IF($B31="","",'))
        self.assertEqual(ws['F31'].fill.start_color.rgb[-6:], 'FFF2CC')
        # เพิ่มทีมเองได้ : แถวเปล่าต่อท้ายมีกรอบ + ช่องเหลือง (10 แถว ถึงแถว 41) · สูตรมีถึงแถว 229 · พิมพ์ถึงแถว 41
        self.assertIsNone(ws['B32'].value)
        self.assertTrue(ws['L32'].value.startswith('=IF($B32="","",'))
        self.assertEqual(ws['K41'].fill.start_color.rgb[-6:], 'FFF2CC')
        self.assertNotEqual(ws['K42'].fill.start_color.rgb[-6:], 'FFF2CC')
        self.assertTrue(ws['L229'].value.startswith('=IF($B229="","",'))
        self.assertEqual(ws.print_area, ['$A$1:$L$41'])

    def test_fuel_sheet_team_dropdown_lists_calc_teams(self):
        """เพิ่มทีมเองด้วย dropdown : รายการ = ทีมในชีตคำนวณ (มีชุดราคาแต่ไม่มีเที่ยวก็อยู่) + ทีมในชีตนี้ ไม่ซ้ำ"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        views._exportDocumentWriteRateSheet(workbook, [self.rateRow(team='ทีมมีราคาไม่มีเที่ยว'),
                                                       self.rateRow(team='ทีม ข', stone='หินฝุ่น')], None, [], set())
        trips = [{'team': 'ทีม ข', 'fuel_branch': 'กงตาก', 'pay_weight': Decimal('40')}]
        views._exportDocumentWriteFuelSheet(workbook, trips, [])
        ws = workbook[views.EXPORT_DOC_FUEL_SHEET]
        self.assertEqual([ws.cell(row=r, column=views.EXPORT_DOC_FUEL_TEAM_LIST_COL).value for r in (30, 31, 32)],
                         ['ทีม ข', 'ทีมมีราคาไม่มีเที่ยว', None])
        self.assertTrue(ws.column_dimensions['CD'].hidden)
        [dv] = ws.data_validations.dataValidation
        self.assertEqual((dv.type, dv.formula1, str(dv.sqref), dv.errorStyle), ('list', '$CD$30:$CD$31', 'B30:B229', 'warning'))

    def test_branch_without_bills_note_says_type_the_price(self):
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        views._exportDocumentWriteRateSheet(
            workbook, [self.rateRow(fuel_branch='กงตาก', fuel_needed=True, fuel_price=None)], None, [], set())
        ws = workbook[views.EXPORT_DOC_RATE_SHEET]
        self.assertEqual(ws['M5'].value, 'กงตาก')
        self.assertIn('กรอกราคาเองที่ชีต ราคาน้ำมันเฉลี่ย', ws['L5'].value)

    def test_payment_group_tables_are_gone(self):
        """v20 : ไม่มีตารางกลุ่มจ่าย / ข้อความแถวรวมในชีตคำนวณแล้ว สรุปจ่ายใส่ค่าตายตัวในสูตรแทน
        ทีมที่ชื่อมีคำว่า ร้อยเกาะ (มีหรือไม่มีเว้นวรรคก่อนวงเล็บ) = กลุ่มร้อยเกาะ"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        pay = workbook['สรุปจ่ายรถร่วม']
        self.assertEqual(pay['AK5'].value,
                         '=IF($S5="","",IF(ISNUMBER(SEARCH("ร้อยเกาะ",$S5)),"ร้อยเกาะ",'
                         'INDEX(รายการมาตรฐาน!$G$2:$G$3,1)))')
        self.assertIn('"รวมจ่ายรถร้อยเกาะ"', pay['A704'].value)
        self.assertIn('"รวมรถร่วม เครดิตปกติ"', pay['A5'].value)
        for ws in workbook.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    if isinstance(cell.value, str) and cell.value.startswith('='):
                        for gone in ('คำนวณค่าขนส่ง!$M', 'คำนวณค่าขนส่ง!$N', 'คำนวณค่าขนส่ง!$P', 'คำนวณค่าขนส่ง!$Q'):
                            self.assertNotIn(gone, cell.value, '%s!%s' % (ws.title, cell.coordinate))

    def test_payment_summary_splits_lines_by_rate(self):
        """หน้าสรุปจ่าย : 1 บรรทัด = accKey + อัตรา (payKey บันทึกรายเที่ยว AC)
        อัตรา = O ของชุดราคา / รายได้ = อัตรา x นน.จ่ายรวมของบรรทัด (ยอดเท่ากับรวมทีละเที่ยว เพราะอัตราเดียวกัน)"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        trip = workbook['บันทึกรายเที่ยว']
        self.assertEqual(trip['AC6'].value,
                         '=IF($V6="","",$V6&"|"&IF($A6="","-",IF($AB6="","0.00",'
                         'IF(INDEX(คำนวณค่าขนส่ง!$O$5:$O$204,$AB6)="","-",'
                         'TEXT(INDEX(คำนวณค่าขนส่ง!$O$5:$O$204,$AB6),"0.00")))))')
        pay = workbook['สรุปจ่ายรถร่วม']
        self.assertIn('บันทึกรายเที่ยว!$AC$6:$AC$10005', pay['R5'].value)
        self.assertIn('บันทึกรายเที่ยว!$AC$6:$AC$10005', pay['AR5'].value)
        self.assertIn('INDEX(คำนวณค่าขนส่ง!$O$5:$O$204,INDEX(บันทึกรายเที่ยว!$AB$6:$AB$10005,$W5))',
                      pay['BD5'].value)                                       # อัตรา
        self.assertEqual(pay['AU404'].value,
                         '=IF($Y404="",0,ROUND(N($BD404)*SUMIF(บันทึกรายเที่ยว!$AC$6:$AC$10005,$Y404,'
                         'บันทึกรายเที่ยว!$AF$6:$AF$10005),2))')             # รายได้
        self.assertIn('คำนวณค่าขนส่ง!$G$5:$G$204', pay['AT404'].value)       # ตามสัญญา (ซ่อน)

    def test_payment_summary_levels_are_coloured(self):
        """v23 : สีแยกระดับอ้างประเภทแถว AD (เดิมอ้าง AA ที่เป็นตัวนับ สีไม่ขึ้น) กฎขอบทั่วไปอยู่ท้ายสุด
        แถวเส้นทางย่อหน้า · แถวรวมของทีมบอกชื่อทีม"""
        pay = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)['สรุปจ่ายรถร่วม']
        rules = sorted((rule for cf in pay.conditional_formatting for rule in cf.rules), key=lambda r: r.priority)
        self.assertEqual([r.formula[0] for r in rules],
                         ['$AD5="Z"', '$AD5="H"', '$AD5="B"', '$AD5="T"', '$AD5<>""'])
        self.assertIn('IF($AD5="T","รวม "&$AF5,', pay['A5'].value)
        self.assertIn('"      "&INDEX($AY$5:$AY$404,$AC5)', pay['A5'].value)

    def test_pay_cover_shows_roikoh_apart_from_partner_teams(self):
        """v24 : ปะหน้าจ่ายรถร่วม แถว 20 ร้อยเกาะ (กลุ่มจ่าย 2) · แถว 21 ทีมรถร่วม รวม (กลุ่ม 1)
        แถว 22-61 ทีมรถร่วมทีละทีม · รวมทั้งสิ้น = สองกลุ่มรวมกัน (ตรงกับรวมจ่ายทั้งสิ้นของสรุปจ่ายรถร่วม)"""
        cover = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)['ปะหน้าจ่ายรถร่วม']
        self.assertEqual((cover['B20'].value, cover['C20'].value, cover['H20'].value), ('ร้อยเกาะ', '=$M$11', '=$M$16'))
        self.assertEqual((cover['B21'].value, cover['C21'].value, cover['H21'].value),
                         ('ทีมรถร่วม รวม', '=$M$5', '=$M$10'))
        self.assertIn('สรุปจ่ายรถร่วม!$AN$5:$AN$404,2,', cover['M11'].value)
        self.assertIn('สรุปจ่ายรถร่วม!$AQ$5:$AQ$704,2,', cover['M15'].value)
        self.assertEqual(cover['A22'].value, '=IF($M22="","",1)')
        self.assertEqual(cover['M22'].value, '=IFERROR(MATCH(1,สรุปจ่ายรถร่วม!$AZ$5:$AZ$704,0),"")')
        self.assertEqual(cover['M61'].value, '=IFERROR(MATCH(40,สรุปจ่ายรถร่วม!$AZ$5:$AZ$704,0),"")')
        self.assertEqual((cover['B62'].value, cover['C62'].value, cover['H62'].value),
                         ('รวมทั้งสิ้น', '=$M$5+$M$11', '=ROUND($M$10+$M$16,2)'))
        self.assertEqual(cover.print_area, ['$A$1:$H$77'])

    def test_summary_headers_follow_accounting_layout(self):
        """หัวตารางหน้าสรุปเหมือนไฟล์บัญชีเดิม (ส่งออก ด.5-69)
        สรุปจ่าย ซ่อนตามสัญญา/ส่วนปรับ เหลือ อัตราค่าขนส่ง (บาท/ตัน) คู่ (บาท/กม.)
        v21 ไม่มีชีต สรุปเหมือง เดิมแล้ว (ระบบใส่ชีต สรุปหน้าเหมือง ให้ตอน export)"""
        workbook = openpyxl.load_workbook(xlsx_template.TRIP_REPORT_TEMPLATE)
        pay = workbook['สรุปจ่ายรถร่วม']
        self.assertTrue(pay.column_dimensions['G'].hidden)
        self.assertEqual([pay['I%d' % r].value for r in (2, 3, 4)], ['อัตรา', 'ค่าขนส่ง', '(บาท/ตัน)'])
        self.assertEqual([pay['J%d' % r].value for r in (2, 3, 4)], ['อัตรา', 'ค่าขนส่ง', '(บาท/กม.)'])

        self.assertNotIn('สรุปเหมือง', workbook.sheetnames)
