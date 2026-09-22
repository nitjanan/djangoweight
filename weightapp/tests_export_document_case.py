# -*- coding: utf-8 -*-
"""หน้า /exportDocument/ : ใบไหนเข้ารายงาน และแต่ละใบเป็นเคสไหน

กติกา
  - เที่ยวลงท่าเรือเรามี 2 ใบ (ใบเหมือง bws = เหมือง customer = ท่าเรือ + ใบท่าเรือ bws = ท่าเรือ customer = เหมือง)
    นับจากใบท่าเรือใบเดียว ใบเหมืองตัดทิ้ง ยกเว้นเที่ยวที่เกิดก่อนท่าเรือนั้นเปิดใช้ตาชั่ง
  - เที่ยวลงท่าเรือบริษัทอื่นมีแค่ใบเหมือง เก็บไว้
  - ใบท่าเรือที่ customer เป็นท่าเรือเราด้วย (ท่าเรือ -> ท่าเรือ) ตัดทิ้ง
  - เคส = ลงท่าเรือไหน ดูจากปลายทาง / ชั่งที่ไหน = ใช้สลับต้นทาง-ปลายทางและเลือกช่องน้ำหนัก
"""
from datetime import date
from decimal import Decimal

from django.core.cache import cache
from django.test import RequestFactory, TestCase

from weightapp import views
from weightapp.models import (BaseBusiness, BaseCompany, BaseCompanyMapBaseCustomer, BaseCustomer,
                              BaseWeightStation, BaseWeightType, InternationalFreightRate, Weight)

OWN = views.EXPORT_DOC_CASE_OWN_PORT
OTHER = views.EXPORT_DOC_CASE_OTHER_PORT


class ExportDocumentCaseTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        BaseBusiness.objects.create(id=1, name='ขายหินในประเทศ')
        BaseBusiness.objects.create(id=views.EXPORT_DOC_OWN_PORT_BIZ_ID, name='ขายหินส่งออก')
        BaseWeightType.objects.create(id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID, name='ขาย')

        mine = BaseCompany.objects.create(name='ศิลาชัย', code='SLC', biz_id=1)
        surat = BaseCompany.objects.create(name='ท่าเรือสุราษฏร์', code='STPS',
                                           biz_id=views.EXPORT_DOC_OWN_PORT_BIZ_ID)
        krabi = BaseCompany.objects.create(name='ท่าเรือกระบี่', code='STPK',
                                           biz_id=views.EXPORT_DOC_OWN_PORT_BIZ_ID)

        for sid, company in (('W1A', mine), ('P1V', surat), ('K1V', krabi)):
            BaseWeightStation.objects.create(
                id=sid, company=company, weight_type_id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID)

        customers = {
            '06-V-011': ('ศิลาชัยสุราษฎร์', mine),        # เหมือง (ต้นทางของใบท่าเรือ)
            '06-V-013': ('ท่าเรือสุราษฎร์', surat),        # ท่าเรือเรา
            '06-V-018': ('ท่าเรือกระบี่', krabi),           # ท่าเรือเรา
            '06-V-900': ('ท่าเรือบริษัทอื่น', None),        # ท่าเรือของคนอื่น
        }
        cls.map_rows = {}
        for code, (name, company) in customers.items():
            BaseCustomer.objects.create(customer_id=code, customer_name=name)
            cls.map_rows[code] = BaseCompanyMapBaseCustomer.objects.create(
                name=name, base_customer_id=code, base_company=company)

        # ปลายทางในตารางราคา = ลูกค้าที่ใบเหมืองจะเข้ารายงานได้
        for dest in ('06-V-013', '06-V-018', '06-V-900'):
            InternationalFreightRate.objects.create(
                origin=cls.map_rows['06-V-011'], destination=cls.map_rows[dest])

        # วันเปิดใช้ตาชั่ง = ใบแรกสุดของตาชั่งท่าเรือนั้น : สุราษฎร์ 1/7/2025 · กระบี่ 6/7/2026
        cls.trip(1, date(2025, 7, 1), 'P1V', '06-V-011', '44.000', '43.800')
        cls.trip(2, date(2026, 7, 6), 'K1V', '06-V-011', '44.000', '43.900')

        # ใบท่าเรือปกติ (เหมือง -> ท่าเรือเรา) : เก็บ
        cls.trip(10, date(2026, 8, 10), 'P1V', '06-V-011', '44.260', '44.380')
        # ท่าเรือ -> ท่าเรือ (ขนกองสต็อกลงเรือ) : ตัด
        cls.trip(11, date(2026, 8, 10), 'P1V', '06-V-013', '22.670', '0')
        # ท่าเรือเราอีกแห่ง -> ท่าเรือนี้ : ตัด (ต้นทางเป็นท่าเรือเหมือนกัน)
        cls.trip(12, date(2026, 8, 10), 'P1V', '06-V-018', '30.000', '0')
        # ใบเหมืองไปสุราษฎร์ หลังเปิดใช้ตาชั่ง : ตัด (ใบท่าเรือ id 10 เป็นตัวแทน)
        cls.trip(20, date(2026, 8, 10), 'W1A', '06-V-013', '44.380', None)
        # ใบเหมืองไปสุราษฎร์ ก่อนเปิดใช้ตาชั่ง : เก็บ เป็นเคสลงท่าเรือเรา
        cls.trip(21, date(2025, 6, 15), 'W1A', '06-V-013', '45.100', None)
        # ใบเหมืองไปกระบี่ : ก่อนกระบี่เปิดใช้ = เก็บ / หลังเปิดใช้ = ตัด
        cls.trip(22, date(2026, 5, 20), 'W1A', '06-V-018', '43.000', None)
        cls.trip(23, date(2026, 8, 20), 'W1A', '06-V-018', '43.500', None)
        # ใบเหมืองไปท่าเรือบริษัทอื่น : เก็บ เป็นเคส 2
        cls.trip(30, date(2026, 8, 10), 'W1A', '06-V-900', '42.000', None)

    @staticmethod
    def trip(weight_id, day, bws_id, customer_id, weight_total, origin_weight):
        Weight.objects.create(
            weight_id=weight_id, date=day, bws_id=bws_id, customer_id=customer_id,
            customer_name=BaseCustomer.objects.get(pk=customer_id).customer_name,
            carry_type_name=views.EXPORT_DOC_CARRY_TYPE, is_cancel=False,
            car_registration_name='83-2751', doc_id=str(weight_id),
            weight_total=Decimal(weight_total),
            origin_weight=None if origin_weight is None else Decimal(origin_weight))

    def setUp(self):
        # วันเปิดใช้และรายชื่อเดือนถูก cache ไว้ ต้องล้างทุกเทสต์ ไม่งั้นค่าของเทสต์ก่อนหน้าค้าง
        cache.clear()

    def querySet(self, **params):
        request = RequestFactory().get('/exportDocument/', params)
        # แท็บร้อยเกาะเห็นทุกต้นทาง ไม่ต้องไปผูกต้นทางกับแท็บในเทสต์นี้
        request.session = {'company_code': 'ROI'}
        return views._exportDocumentQuerySet(request)

    def ids(self, qs):
        return set(qs.values_list('weight_id', flat=True))

    # ---------- ใบไหนเข้ารายงาน ----------

    def test_go_live_date_comes_from_first_port_ticket(self):
        customers = views._exportDocumentOwnPortCustomers()
        self.assertEqual(customers, {'06-V-013': date(2025, 7, 1), '06-V-018': date(2026, 7, 6)})

    def test_which_tickets_stay(self):
        _, filters, _ = self.querySet()
        self.assertEqual(self.ids(filters['base_qs']), {1, 2, 10, 21, 22, 30})

    def test_port_to_port_is_dropped(self):
        _, filters, _ = self.querySet()
        kept = self.ids(filters['base_qs'])
        self.assertNotIn(11, kept)   # ท่าเรือ -> ตัวเอง
        self.assertNotIn(12, kept)   # กระบี่ -> สุราษฎร์

    def test_mine_ticket_after_go_live_is_dropped_per_port(self):
        _, filters, _ = self.querySet()
        kept = self.ids(filters['base_qs'])
        self.assertNotIn(20, kept)   # สุราษฎร์เปิดแล้ว
        self.assertNotIn(23, kept)   # กระบี่เปิดแล้ว
        self.assertIn(22, kept)      # วันเดียวกันนั้นกระบี่ยังไม่เปิด (สุราษฎร์เปิดแล้วก็ไม่เกี่ยว)
        self.assertIn(21, kept)      # สุราษฎร์ยังไม่เปิด

    def test_port_without_any_ticket_keeps_mine_tickets(self):
        """ท่าเรือที่ยังไม่เคยออกใบ = ยังไม่เปิดใช้ ใบเหมืองต้องไม่ถูกตัด"""
        Weight.objects.filter(bws_id='K1V').delete()
        _, filters, _ = self.querySet()
        self.assertIsNone(views._exportDocumentOwnPortCustomers()['06-V-018'])
        self.assertTrue({22, 23} <= self.ids(filters['base_qs']))

    def test_page_and_export_use_the_same_tickets(self):
        """ตัดที่ชั้น query : ยอดบนหน้าเว็บกับแถวที่ลงไฟล์ต้องเป็นชุดเดียวกัน"""
        qs, filters, _ = self.querySet(month='2026-08')
        rows = views._exportDocumentRows(qs, filters['own_port_bws'], filters['own_port_customers'])
        self.assertEqual(qs.count(), len(rows))
        self.assertEqual({r['weight_id'] for r in rows}, {10, 30})

    # ---------- เคส + การสลับต้นทาง/ปลายทาง ----------

    def rowOf(self, weight_id):
        qs = Weight.objects.filter(weight_id=weight_id).select_related('bws')
        return views._exportDocumentRows(qs)[0]

    def test_port_ticket_is_own_port_weighed_at_port(self):
        row = self.rowOf(10)
        self.assertEqual(row['case'], OWN)
        self.assertEqual(row['weighed_at'], views.EXPORT_DOC_WEIGHED_AT_PORT)
        self.assertEqual(row['origin_map_id'], self.map_rows['06-V-011'].id)
        self.assertEqual(row['destination_map_id'], self.map_rows['06-V-013'].id)
        self.assertEqual(row['origin_weight'], Decimal('44.380'))   # ใบท่าเรือ : ต้นทาง = origin_weight
        self.assertEqual(row['dest_weight'], Decimal('44.260'))

    def test_mine_ticket_before_go_live_is_own_port_but_weighed_at_mine(self):
        """เคสลงท่าเรือเรา แต่ยังต้องสลับข้างแบบใบเหมือง"""
        row = self.rowOf(21)
        self.assertEqual(row['case'], OWN)
        self.assertEqual(row['case_label'], 'ลงท่าเรือของบริษัท')
        self.assertEqual(row['weighed_at'], views.EXPORT_DOC_WEIGHED_AT_MINE)
        self.assertEqual(row['origin_map_id'], self.map_rows['06-V-011'].id)
        self.assertEqual(row['destination_map_id'], self.map_rows['06-V-013'].id)
        self.assertEqual(row['origin_weight'], Decimal('45.100'))   # ใบเหมือง : ต้นทาง = weight_total
        self.assertIsNone(row['dest_weight'])

    def test_mine_ticket_to_other_port_is_other_port(self):
        row = self.rowOf(30)
        self.assertEqual(row['case'], OTHER)
        self.assertEqual(row['weighed_at'], views.EXPORT_DOC_WEIGHED_AT_MINE)

    def test_case_filter_uses_destination(self):
        _, filters, _ = self.querySet()
        base = filters['base_qs']
        own = views._exportDocumentApplyCaseFilter(
            base, OWN, filters['own_port_bws'], filters['own_port_customers'])
        other = views._exportDocumentApplyCaseFilter(
            base, OTHER, filters['own_port_bws'], filters['own_port_customers'])
        self.assertEqual(self.ids(own), {1, 2, 10, 21, 22})
        self.assertEqual(self.ids(other), {30})

    def test_case_param_on_the_page(self):
        qs, _, _ = self.querySet(month='2025-06', case=OWN)
        self.assertEqual(self.ids(qs), {21})
        qs, _, _ = self.querySet(month='2025-06', case=OTHER)
        self.assertEqual(self.ids(qs), set())

    # ---------- ช่องน้ำหนักในไฟล์แก้ไขรายเที่ยว ----------

    def test_ton_attr_follows_where_it_was_weighed(self):
        """ใบเหมืองก่อนเปิดใช้ตาชั่งเป็นเคสลงท่าเรือเรา แต่ น.น.ปลายทางยังอยู่ช่อง origin_weight"""
        self.assertEqual(views._exportDocumentTonAttr('dest_ton', views.EXPORT_DOC_WEIGHED_AT_MINE),
                         'origin_weight')
        self.assertEqual(views._exportDocumentTonAttr('dest_ton', views.EXPORT_DOC_WEIGHED_AT_PORT),
                         'weight_total')
        self.assertEqual(views._exportDocumentTonAttr('origin_ton', views.EXPORT_DOC_WEIGHED_AT_MINE),
                         'weight_total')
        self.assertEqual(views._exportDocumentTonAttr('origin_ton', views.EXPORT_DOC_WEIGHED_AT_PORT),
                         'origin_weight')


class ExportDocumentCustomerAliasTests(TestCase):
    """รหัสลูกค้าสำรอง : ที่เดียวกันมีหลายรหัส เช่น สุราษฎร์พอร์ท 06-V-024 กับ 77-V-007"""

    @classmethod
    def setUpTestData(cls):
        BaseBusiness.objects.create(id=1, name='ขายหินในประเทศ')
        BaseBusiness.objects.create(id=views.EXPORT_DOC_OWN_PORT_BIZ_ID, name='ขายหินส่งออก')
        BaseWeightType.objects.create(id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID, name='ขาย')
        kongtak = BaseCompany.objects.create(name='กงตาก', code='KT', biz_id=1)
        BaseWeightStation.objects.create(id='M1V', company=kongtak,
                                         weight_type_id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID)

        for code, name in (('06-V-028', 'โชคพนาไมนิ่ง (กงตาก 1)'),
                           ('06-V-024', 'ท่าเรือสุราษฎร์พอร์ท แอนด์ เทอร์มินอล'),
                           ('77-V-007', 'บริษัท สุราษฎร์พอร์ทแอนด์เทอร์มินอล (ปัญจะใหม่)')):
            BaseCustomer.objects.create(customer_id=code, customer_name=name)
        cls.origin = BaseCompanyMapBaseCustomer.objects.create(
            name='กงตาก', base_customer_id='06-V-028', base_company=kongtak)
        cls.spt = BaseCompanyMapBaseCustomer.objects.create(
            name='สุราษฎร์พอร์ท', base_customer_id='06-V-024')
        # ใบราคาผูกกับรหัสหลัก 06-V-024 อย่างเดียว
        InternationalFreightRate.objects.create(origin=cls.origin, destination=cls.spt)

        for weight_id, customer in ((1, '06-V-024'), (2, '77-V-007')):
            Weight.objects.create(
                weight_id=weight_id, date=date(2026, 8, 10), bws_id='M1V', customer_id=customer,
                customer_name=BaseCustomer.objects.get(pk=customer).customer_name,
                carry_type_name=views.EXPORT_DOC_CARRY_TYPE, is_cancel=False,
                car_registration_name='70-3725', doc_id=str(weight_id), weight_total=Decimal('44.000'))

    def setUp(self):
        cache.clear()

    def baseIds(self):
        request = RequestFactory().get('/exportDocument/', {})
        request.session = {'company_code': 'ROI'}
        _, filters, _ = views._exportDocumentQuerySet(request)
        return set(filters['base_qs'].values_list('weight_id', flat=True))

    def addAlias(self):
        from weightapp.models import BaseCompanyMapCustomerAlias
        return BaseCompanyMapCustomerAlias.objects.create(map_row=self.spt, base_customer_id='77-V-007')

    def test_without_alias_the_second_code_is_not_an_export_destination(self):
        self.assertEqual(self.baseIds(), {1})

    def test_alias_brings_trips_in_with_same_destination_row(self):
        self.addAlias()
        self.assertEqual(self.baseIds(), {1, 2})
        rows = views._exportDocumentRows(Weight.objects.filter(weight_id__in=[1, 2]).select_related('bws'))
        by_id = {r['weight_id']: r for r in rows}
        # ปลายทางเป็นแถว map เดียวกัน ใบราคาเดียวกันจึงจับคู่ได้ทั้งสองรหัส
        self.assertEqual(by_id[2]['destination_map_id'], self.spt.id)
        self.assertEqual(by_id[2]['destination'], by_id[1]['destination'])

    def test_alias_cannot_be_a_primary_code_of_any_row(self):
        from django.core.exceptions import ValidationError
        from weightapp.models import BaseCompanyMapCustomerAlias
        alias = BaseCompanyMapCustomerAlias(map_row=self.spt, base_customer_id='06-V-028')
        with self.assertRaises(ValidationError):
            alias.full_clean()

    def test_primary_code_cannot_reuse_an_alias(self):
        from django.core.exceptions import ValidationError
        self.addAlias()
        row = BaseCompanyMapBaseCustomer(name='ซ้ำ', base_customer_id='77-V-007')
        with self.assertRaises(ValidationError):
            row.clean()

    def test_alias_of_own_port_counts_as_own_port(self):
        from weightapp.models import BaseCompanyMapCustomerAlias
        surat = BaseCompany.objects.create(name='ท่าเรือสุราษฏร์', code='STPS',
                                           biz_id=views.EXPORT_DOC_OWN_PORT_BIZ_ID)
        BaseCustomer.objects.create(customer_id='06-V-013', customer_name='ท่าเรือเรา')
        BaseCustomer.objects.create(customer_id='77-V-013', customer_name='ท่าเรือเรา (รหัสสำรอง)')
        port_row = BaseCompanyMapBaseCustomer.objects.create(
            name='ท่าเรือเรา', base_customer_id='06-V-013', base_company=surat)
        BaseCompanyMapCustomerAlias.objects.create(map_row=port_row, base_customer_id='77-V-013')
        self.assertIn('77-V-013', views._exportDocumentOwnPortCustomers())
