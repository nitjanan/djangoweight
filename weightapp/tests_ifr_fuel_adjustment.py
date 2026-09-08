# -*- coding: utf-8 -*-
"""ค่าปรับตามน้ำมันย้ายจาก "ทั้งใบ" มาเป็น "รายแถวทีม" (ทีม + ช่วงแบก นน.)

เทสต์ชุดนี้ยิงผ่าน serializer ตัวเดียวกับที่หน้าเว็บใช้ ไม่ได้ตั้งค่าลงโมเดลตรง ๆ
เพราะกับดักที่ตั้งใจดักอยู่ในชั้น serializer ทั้งหมด (การบังคับกรอก / การตัดสินว่าต้องออกใบใหม่)
"""
from decimal import Decimal

from django.test import TestCase

from weightapp.models import (BaseCarTeam, BaseCompanyMapBaseCustomer, CarryingweightRate,
                              InternationalFreightRate, InternationalFreightRateTeam)
from weightapp.serializers import InternationalFreightRateSerializer


class IfrFuelAdjustmentPerTeamTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # ต้นทาง/ปลายทางไม่ผูกบริษัทหรือลูกค้า (null ได้ทั้งคู่) พอสำหรับเทสต์ชั้น serializer
        cls.origin = BaseCompanyMapBaseCustomer.objects.create(name='ท่าต้นทางทดสอบ')
        cls.destination = BaseCompanyMapBaseCustomer.objects.create(name='ท่าปลายทางทดสอบ')
        cls.team = BaseCarTeam.objects.create(car_team_id='TSTA', car_team_name='ทีมทดสอบ A')
        cls.band_low = CarryingweightRate.objects.create(
            name='นน. 35.01-40 ตัน', description='นน. 35.01-40 ตัน',
            min_weight=Decimal('35.01'), max_weight=Decimal('40.00'))
        cls.band_high = CarryingweightRate.objects.create(
            name='นน. 40.01-50 ตัน', description='นน. 40.01-50 ตัน',
            min_weight=Decimal('40.01'), max_weight=Decimal('50.00'))

    def basePayload(self, teams):
        return {
            'origin': self.origin.id,
            'destination': self.destination.id,
            'base_fuel_price': '32.50',
            'distance': '450.00',
            'fuel_used_per_trip': '120.00',
            'teams': teams,
        }

    def createRate(self, teams):
        serializer = InternationalFreightRateSerializer(data=self.basePayload(teams))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save()

    def test_each_team_row_keeps_its_own_adjustment(self):
        """ทีมเดียวกันคนละช่วงแบก นน. เก็บค่าปรับตามน้ำมันคนละค่าได้"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00'},
            {'team_id': self.team.pk, 'weight_carried': self.band_high.id,
             'freight_rate': '1350.00', 'fuel_freight_adjustment': '1.25'},
        ])

        by_band = {t.weight_carried_id: t.fuel_freight_adjustment
                   for t in rate.teams.all()}
        self.assertEqual(by_band[self.band_low.id], Decimal('1.00'))
        self.assertEqual(by_band[self.band_high.id], Decimal('1.25'))

    def test_adjustment_is_required_on_every_team_row(self):
        """เว้นว่างไม่ได้ ปล่อยผ่านแล้วสูตร (เฉลี่ย - ฐาน) x ค่านี้ จะไม่ปรับเลยแบบเงียบ ๆ"""
        serializer = InternationalFreightRateSerializer(data=self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00'},
        ]))
        self.assertFalse(serializer.is_valid())
        self.assertIn('fuel_freight_adjustment', serializer.errors['teams'][0])

    def test_rate_no_longer_accepts_the_removed_fields(self):
        """payload_weight กับค่าปรับระดับใบ ไม่มีในโมเดลแล้ว ส่งมาก็ต้องไม่ถูกเก็บ"""
        payload = self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00'},
        ])
        payload['payload_weight'] = '25.00'
        payload['fuel_freight_adjustment'] = '9.99'
        serializer = InternationalFreightRateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rate = serializer.save()
        self.assertFalse(hasattr(rate, 'payload_weight'))
        self.assertFalse(hasattr(rate, 'fuel_freight_adjustment'))

    def test_changing_only_the_adjustment_issues_a_new_version(self):
        """กับดักหลัก : ถ้า _teamKey ไม่รวมช่องนี้ ระบบจะคิดว่า "ไม่มีอะไรเปลี่ยน" แล้วทับใบเดิม"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00'},
        ])
        self.assertEqual(rate.version, 1)

        payload = self.basePayload([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.50'},
        ])
        serializer = InternationalFreightRateSerializer(rate, data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertNotEqual(updated.id, rate.id)
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.teams.get().fuel_freight_adjustment, Decimal('1.50'))
        # ใบเก่ายังอยู่ครบ เอกสารเดือนเก่าจึงได้ตัวเลขเดิม
        self.assertEqual(
            InternationalFreightRateTeam.objects.get(
                international_freight_rate=rate).fuel_freight_adjustment,
            Decimal('1.00'))

    def test_new_version_without_teams_copies_the_adjustment(self):
        """ออกใบใหม่โดยไม่ส่งทีมมา ต้อง copy ค่าปรับตามน้ำมันตามไปด้วย ไม่ใช่ปล่อย null"""
        rate = self.createRate([
            {'team_id': self.team.pk, 'weight_carried': self.band_low.id,
             'freight_rate': '1200.00', 'fuel_freight_adjustment': '1.00'},
        ])

        payload = self.basePayload([])
        payload.pop('teams')
        payload['distance'] = '460.00'   # แก้ช่องอื่นเพื่อให้ถือว่าเป็นการปรับราคาจริง
        serializer = InternationalFreightRateSerializer(rate, data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.teams.get().fuel_freight_adjustment, Decimal('1.00'))

    def test_rate_row_ordering_is_untouched_for_all_teams_rows(self):
        """แถว "ทุกทีม" (team = NULL) ก็เก็บค่าปรับของตัวเองได้เหมือนแถวที่ระบุทีม"""
        rate = self.createRate([
            {'weight_carried': self.band_low.id,
             'freight_rate': '1100.00', 'fuel_freight_adjustment': '0.80'},
        ])
        row = rate.teams.get()
        self.assertIsNone(row.team_id)
        self.assertEqual(row.fuel_freight_adjustment, Decimal('0.80'))
