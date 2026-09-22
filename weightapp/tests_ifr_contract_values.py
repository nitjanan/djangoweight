# -*- coding: utf-8 -*-
"""ค่าที่ตกลงกันตอนทำสัญญาในแถวทีม : ค่าขนส่งตามสัญญา / ราคาน้ำมันฐานวันทำสัญญา / วันทำสัญญา

ตอนนี้เก็บไว้อ้างอิงอย่างเดียว ยังไม่มีสูตรไหนเอาไปคิดเงิน เทสต์จึงคุมแค่
การเก็บค่า (รายแถว ทีมเดียวกันต่างกันได้) และการออกเวอร์ชันใหม่
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

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
