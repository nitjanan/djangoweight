# -*- coding: utf-8 -*-
"""ค่าที่ตกลงกันตอนทำสัญญาในแถวทีม : ค่าขนส่งตามสัญญา กับ ราคาน้ำมันฐานวันทำสัญญา

ตอนนี้เก็บไว้อ้างอิงอย่างเดียว ยังไม่มีสูตรไหนเอาไปคิดเงิน เทสต์จึงคุมแค่
การเก็บค่า กติกา "ทีมเดียวกันต้องใช้ราคาน้ำมันวันทำสัญญาเดียวกัน" และการออกเวอร์ชันใหม่
"""
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

    def test_same_team_must_use_same_contract_fuel_price(self):
        """สัญญาฉบับเดียวเซ็นวันเดียว ราคาน้ำมันวันนั้นจึงมีค่าเดียวทั้งทีม"""
        serializer = InternationalFreightRateSerializer(data=self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00',
             'contract_base_fuel_price': '29.75'},
            {'team_id': self.team.pk, 'weight_carried': self.band_high.id,
             'freight_rate': '1350.00', 'fuel_freight_adjustment': '1.00',
             'contract_base_fuel_price': '31.00'},
        ]))
        self.assertFalse(serializer.is_valid())
        self.assertIn('ราคาน้ำมันฐานวันทำสัญญา', str(serializer.errors))

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
             'contract_freight_rate': '1150.00', 'contract_base_fuel_price': '29.75'},
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
