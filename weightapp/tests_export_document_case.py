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

from django.contrib.auth.models import User
from django.core.cache import cache
from unittest import mock

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from weightapp import views
from weightapp.models import (CarryingweightRate, BaseBusiness, BaseCompany, BaseCompanyMapBaseCustomer,
                              BaseCompanyMapCustomerAlias, BaseCustomer,
                              BaseSite, BaseStoneType, BaseWeightStation, BaseWeightType,
                              INTERNATIONAL_FREIGHT_RATE_FIRST_DATE, InternationalFreightRate,
                              InternationalFreightRateStatus, InternationalFreightRateTeam,
                              UserProfile, Weight)

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
                name=name, base_customer_id=code, base_company=company,
                is_export_destination=True)

        # ปลายทางในตารางราคา = ลูกค้าที่ใบเหมืองจะเข้ารายงานได้
        for dest in ('06-V-013', '06-V-018', '06-V-900'):
            InternationalFreightRate.objects.create(
                origin=cls.map_rows['06-V-011'], destination=cls.map_rows[dest],
                effective_date=INTERNATIONAL_FREIGHT_RATE_FIRST_DATE)

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
    def trip(weight_id, day, bws_id, customer_id, weight_total, origin_weight, site_id=None,
             carry=views.EXPORT_DOC_CARRY_TYPE):
        Weight.objects.create(
            weight_id=weight_id, date=day, bws_id=bws_id, customer_id=customer_id,
            site_id=site_id,
            customer_name=BaseCustomer.objects.get(pk=customer_id).customer_name,
            carry_type_name=carry, is_cancel=False,
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

    def querySetTab(self, tab, **params):
        request = RequestFactory().get('/exportDocument/', params)
        request.session = {'company_code': tab}
        return views._exportDocumentQuerySet(request)

    # ---------- แท็บบริษัท = ต้นทาง · ช่อง "ชั่งที่ (ตาชั่ง)" = bws_id ----------

    def test_tab_sees_trips_whose_origin_belongs_to_it(self):
        """แท็บศิลาชัยเห็นเที่ยวต้นทางศิลาชัยทั้งที่ชั่งที่ท่าเรือเรา (10) และที่ชั่งที่เหมือง (30)"""
        qs, filters, _ = self.querySetTab('SLC', month='2026-08')
        self.assertEqual(self.ids(qs), {10, 30})
        self.assertEqual([b['id'] for b in filters['bws_options']], ['P1V', 'W1A'])
        self.assertFalse(filters['tab_no_origin'])

    def test_station_filter_narrows_the_tab(self):
        qs, filters, _ = self.querySetTab('SLC', month='2026-08', bws='P1V')
        self.assertEqual(filters['selected_bws'], 'P1V')
        self.assertEqual(self.ids(qs), {10})
        qs, _, _ = self.querySetTab('SLC', month='2026-08', bws='W1A')
        self.assertEqual(self.ids(qs), {30})

    def test_station_without_trips_in_tab_is_ignored(self):
        """สลับแท็บแล้ว ?bws= ของแท็บเดิมค้างอยู่ : ถือว่าไม่ได้เลือก = ทุกตาชั่ง"""
        qs, filters, _ = self.querySetTab('SLC', month='2026-08', bws='K1V')
        self.assertEqual(filters['selected_bws'], '')
        self.assertEqual(self.ids(qs), {10, 30})

    def test_case_filter_inside_a_mine_tab(self):
        """แท็บเหมืองเลือกได้ว่าจะดูเที่ยวที่ลงท่าเรือเรา หรือที่ลงท่าเรือบริษัทอื่น"""
        qs, filters, _ = self.querySetTab('SLC', month='2026-08', case=OWN)
        self.assertEqual(filters['selected_case'], OWN)
        self.assertEqual(self.ids(qs), {10})
        qs, _, _ = self.querySetTab('SLC', month='2026-08', case=OTHER)
        self.assertEqual(self.ids(qs), {30})

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_page_offers_case_filter(self):
        user = User.objects.create_user('acc', 'acc@t.com', 'pw12345!')
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'SLC'
        session.save()
        page = self.client.get('/exportDocument/', {'month': '2026-08', 'case': OTHER})
        self.assertEqual({r['weight_id'] for r in page.context['rows']}, {30})
        html = page.content.decode('utf-8')
        self.assertIn('name="case"', html)
        self.assertIn('<option value="%s" selected>' % OTHER, html)

    def test_port_tab_sees_trips_weighed_at_its_station(self):
        """แท็บท่าเรือเรา = ที่ชั่งที่ท่าเรือนั้น ทุกต้นทาง (ถ้ากรองด้วยต้นทาง แท็บท่าเรือจะว่างเสมอ)"""
        qs, filters, _ = self.querySetTab('STPS', month='2026-08')
        self.assertEqual(self.ids(qs), {10})
        self.assertEqual([b['id'] for b in filters['bws_options']], ['P1V'])
        qs, _, _ = self.querySetTab('STPK', month='2026-07')
        self.assertEqual(self.ids(qs), {2})

    def test_tab_without_origin_sees_nothing(self):
        BaseCompany.objects.create(name='บริษัทไม่มีต้นทาง', code='NOOR', biz_id=1)
        qs, filters, _ = self.querySetTab('NOOR', month='2026-08')
        self.assertTrue(filters['tab_no_origin'])
        self.assertEqual(self.ids(qs), set())

    def test_rows_tell_who_weighed(self):
        qs, filters, _ = self.querySet(month='2026-08')
        rows = views._exportDocumentRows(qs, filters['own_port_bws'], filters['own_port_customers'])
        names = {'P1V': 'ท่าเรือสุราษฏร์', 'K1V': 'ท่าเรือกระบี่', 'W1A': 'ศิลาชัย'}
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r['bws_company'], names[r['bws_id']])

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

    def test_destination_without_any_rate_still_shows_up(self):
        """ปลายทางที่ผูก map แล้วแต่ยังไม่มีใบราคา ต้องขึ้นในหน้านี้ (แล้วไปเตือนว่าไม่มีราคาแทน)"""
        BaseCustomer.objects.create(customer_id='06-V-901', customer_name='ท่าเรือยังไม่มีราคา')
        BaseCompanyMapBaseCustomer.objects.create(name='ท่าเรือยังไม่มีราคา',
                                                  base_customer_id='06-V-901',
                                                  is_export_destination=True)
        self.trip(31, date(2026, 8, 12), 'W1A', '06-V-901', '41.000', None)

        _, filters, _ = self.querySet()
        self.assertIn(31, self.ids(filters['base_qs']))

    def test_customer_without_map_row_stays_out(self):
        """ลูกค้าในประเทศ (ยังไม่ผูก map) ต้องไม่หลุดเข้ามา"""
        BaseCustomer.objects.create(customer_id='04-V-027', customer_name='ผู้รับเหมาในประเทศ')
        self.trip(32, date(2026, 8, 12), 'W1A', '04-V-027', '40.000', None)

        _, filters, _ = self.querySet()
        self.assertNotIn(32, self.ids(filters['base_qs']))

    def test_destination_must_be_flagged_as_export(self):
        """ผูก map แล้วแต่ไม่ติ๊ก = เที่ยวไม่เข้ารายงาน (เช่นเหมืองในเครือที่เป็นต้นทางอย่างเดียว)"""
        BaseCustomer.objects.create(customer_id='06-V-902', customer_name='เหมืองในเครือ')
        row = BaseCompanyMapBaseCustomer.objects.create(name='เหมืองในเครือ',
                                                        base_customer_id='06-V-902')
        self.trip(33, date(2026, 8, 12), 'W1A', '06-V-902', '40.000', None)

        _, filters, _ = self.querySet()
        self.assertNotIn(33, self.ids(filters['base_qs']))

        # ติ๊กแล้วต้องเข้ามาทันที
        row.is_export_destination = True
        row.save()
        _, filters, _ = self.querySet()
        self.assertIn(33, self.ids(filters['base_qs']))

    def test_alias_follows_the_flag_of_its_map_row(self):
        """รหัสสำรองไม่มีธงของตัวเอง ใช้ธงของแถวแม่"""
        from weightapp.models import BaseCompanyMapCustomerAlias
        BaseCustomer.objects.create(customer_id='77-V-900', customer_name='ท่าเรืออื่น รหัสสำรอง')
        alias_row = self.map_rows['06-V-900']
        BaseCompanyMapCustomerAlias.objects.create(map_row=alias_row,
                                                   base_customer_id='77-V-900')
        self.trip(34, date(2026, 8, 12), 'W1A', '77-V-900', '40.000', None)

        _, filters, _ = self.querySet()
        self.assertIn(34, self.ids(filters['base_qs']))

        # เอาติ๊กออกที่แถวแม่ รหัสสำรองต้องหลุดออกไปด้วย
        alias_row.is_export_destination = False
        alias_row.save()
        _, filters, _ = self.querySet()
        self.assertNotIn(34, self.ids(filters['base_qs']))

    def test_unflagged_destination_with_trips_is_reported(self):
        """ผูก map แล้วแต่ลืมติ๊ก ต้องมีรายการให้เห็นบนหน้าเว็บ ไม่ใช่เงียบหาย"""
        BaseCustomer.objects.create(customer_id='06-V-903', customer_name='ท่าเรือลืมติ๊ก')
        BaseCompanyMapBaseCustomer.objects.create(name='ท่าเรือลืมติ๊ก',
                                                  base_customer_id='06-V-903')
        self.trip(35, date(2026, 8, 12), 'W1A', '06-V-903', '40.000', None)

        _, filters, _ = self.querySet()
        pending = views._exportDocumentUnflaggedDestinations(
            views._exportDocumentOtherBwsIds(), filters['export_customers'])
        by_code = {p['customer_id']: p for p in pending}
        self.assertIn('06-V-903', by_code)
        self.assertEqual(by_code['06-V-903']['trips'], 1)

    def test_internal_and_charity_sites_are_dropped(self):
        """หน้างาน ใช้ภายใน (200PL) / อนุเคราะห์ (300PL) ไม่ใช่เที่ยวส่งออก"""
        BaseSite.objects.create(base_site_id='200PL', base_site_name='ใช้ภายใน')
        BaseSite.objects.create(base_site_id='300PL', base_site_name='อนุเคราะห์')
        BaseSite.objects.create(base_site_id='001PL', base_site_name='หน้างานปกติ')
        self.trip(40, date(2026, 8, 12), 'W1A', '06-V-900', '40.000', None, site_id='200PL')
        self.trip(41, date(2026, 8, 12), 'W1A', '06-V-900', '40.000', None, site_id='300PL')
        self.trip(42, date(2026, 8, 12), 'W1A', '06-V-900', '40.000', None, site_id='001PL')
        self.trip(43, date(2026, 8, 12), 'W1A', '06-V-900', '40.000', None)   # ไม่ระบุหน้างาน

        kept = self.ids(self.querySet()[1]['base_qs'])
        self.assertNotIn(40, kept)
        self.assertNotIn(41, kept)
        self.assertIn(42, kept)
        self.assertIn(43, kept)   # site_id เป็น NULL ต้องไม่ถูกตัด

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

    # ---------- ชนิดสินค้า : น้ำมัน ----------

    def test_oil_and_fertilizer_are_dropped(self):
        """น้ำมัน / ปุ๋ย ไม่ใช่เที่ยวขนหิน ตัดทั้งใบที่ผูกรหัสและใบเก่าที่มีแต่ชื่อ (รวมชื่อสะกดผิด)"""
        BaseStoneType.objects.create(base_stone_type_id='45ST', base_stone_type_name='น้ำมัน')
        BaseStoneType.objects.create(base_stone_type_id='46ST', base_stone_type_name='น้ำมันปาล์ม')
        BaseStoneType.objects.create(base_stone_type_id='001S', base_stone_type_name='ปุ๋ย')
        BaseStoneType.objects.create(base_stone_type_id='40ST', base_stone_type_name='ปุ๋ยโดโลไมท์ 80 เมช')
        BaseStoneType.objects.create(base_stone_type_id='61ST', base_stone_type_name='แอมโมเนียมไนเตรต')
        BaseStoneType.objects.create(base_stone_type_id='37ST', base_stone_type_name='ขี้แร่')
        BaseStoneType.objects.create(base_stone_type_id='39ST', base_stone_type_name='แอนไฮไดรต์ 2 นิ้ว')
        BaseStoneType.objects.create(base_stone_type_id='01ST', base_stone_type_name='หิน 3/4')
        for weight_id, stone_id, stone_name in ((50, '45ST', 'น้ำมัน'),
                                                (51, '46ST', 'น้ำมันปาล์ม'),
                                                (52, None, 'น้ำมัน'),          # ใบเก่า ไม่ได้ผูกรหัส
                                                (55, None, 'นำมัน'),           # สะกดผิด
                                                (56, '001S', 'ปุ๋ย'),
                                                (57, '40ST', 'ปุ๋ยโดโลไมท์ 80 เมช'),
                                                (58, None, 'ปุ๋ยน้ำ bulk'),
                                                (59, '61ST', 'แอมโมเนียมไนเตรต'),
                                                (60, '37ST', 'ขี้แร่'),              # ยังนับ
                                                (61, None, 'เศษเหล็ก'),
                                                (62, None, 'บริการชั่งน้ำหนัก'),
                                                (63, '39ST', 'แอนไฮไดรต์ 2 นิ้ว'),   # แร่ ยังนับ
                                                (53, '01ST', 'หิน 3/4'),
                                                (54, None, None)):             # ไม่ได้ระบุชนิด
            self.trip(weight_id, date(2026, 8, 14), 'W1A', '06-V-900', '42.000', None)
            Weight.objects.filter(weight_id=weight_id).update(stone_type_id=stone_id,
                                                              stone_type_name=stone_name)
        kept = self.ids(self.querySet(month='2026-08')[0])
        self.assertTrue({53, 54, 60, 63} <= kept)
        self.assertFalse({50, 51, 52, 55, 56, 57, 58, 59, 61, 62} & kept)

    # ---------- ประเภทการบรรทุกว่าง ----------

    def addCarryTrips(self):
        """ใบเหมืองไปท่าเรือบริษัทอื่น เดือน 8/2026 : ส่งให้ (30 จาก setUpTestData) + ว่าง 2 แบบ + รับเอง"""
        self.trip(40, date(2026, 8, 11), 'W1A', '06-V-900', '42.000', None, carry=None)
        self.trip(41, date(2026, 8, 12), 'W1A', '06-V-900', '42.000', None, carry='')
        self.trip(42, date(2026, 8, 13), 'W1A', '06-V-900', '42.000', None, carry='รับเอง')

    def test_only_deliver_carry_type_is_counted(self):
        """นับเฉพาะ "ส่งให้" : ใบที่ว่าง (NULL / ข้อความว่าง) กับรับเอง ไม่อยู่ในรายงาน"""
        self.addCarryTrips()
        qs, _, _ = self.querySet(month='2026-08')
        kept = self.ids(qs)
        self.assertIn(30, kept)              # ส่งให้
        self.assertFalse({40, 41, 42} & kept)

    def test_empty_carry_type_is_split_out_as_a_warning(self):
        """ใบว่างไม่ได้หายเงียบ : แยกเป็นชุดคำเตือน ส่วนรับเองไม่ต้องเตือน"""
        self.addCarryTrips()
        _, filters, _ = self.querySet(month='2026-08')
        self.assertEqual(self.ids(filters['carry_empty_qs']), {40, 41})
        self.assertFalse({40, 41} & self.ids(filters['off_route_qs']))

    def test_trip_edit_file_accepts_only_deliver_carry_type(self):
        """ไฟล์แก้ไขรายเที่ยวแก้ได้เฉพาะเที่ยวที่อยู่ในรายงาน = ส่งให้"""
        self.assertTrue(views._exportDocumentCarryCounted(views.EXPORT_DOC_CARRY_TYPE))
        self.assertFalse(views._exportDocumentCarryCounted(None))
        self.assertFalse(views._exportDocumentCarryCounted(''))
        self.assertFalse(views._exportDocumentCarryCounted('รับเอง'))

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_page_warns_about_empty_carry_type(self):
        self.addCarryTrips()
        user = User.objects.create_user('acc', 'acc@t.com', 'pw12345!')
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'ROI'
        session.save()

        page = self.client.get('/exportDocument/', {'month': '2026-08'})
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context['summary']['carry_empty_count'], 2)
        self.assertEqual(page.context['carry_empty_by_bws'], [{'bws_id': 'W1A', 'trips': 2}])
        self.assertFalse({40, 41} & {r['weight_id'] for r in page.context['rows']})
        html = page.content.decode('utf-8')
        self.assertIn('ประเภทการบรรทุกว่าง — ไม่นับในรายงาน', html)
        self.assertIn('problem=carry_empty#trips', html)

        only = self.client.get('/exportDocument/', {'month': '2026-08', 'problem': 'carry_empty'})
        self.assertEqual({r['weight_id'] for r in only.context['rows']}, {40, 41})
        self.assertEqual(only.context['problem_count'], 2)

    def test_case_param_on_the_page(self):
        qs, _, _ = self.querySet(month='2025-06', case=OWN)
        self.assertEqual(self.ids(qs), {21})
        qs, _, _ = self.querySet(month='2025-06', case=OTHER)
        self.assertEqual(self.ids(qs), set())

    # ---------- นับเฉพาะเส้นทางที่มีในหน้าค่าขนส่ง ----------

    def addOffRouteTrips(self):
        """เที่ยวที่ผ่านกติกาใบชั่งทุกข้อ แต่ ต้นทาง -> ปลายทาง ไม่มีใบราคาที่ใช้อยู่"""
        BaseCustomer.objects.create(customer_id='07-V-001', customer_name='เงินสด')
        self.trip(60, date(2026, 8, 12), 'P1V', '07-V-001', '20.000', None)    # ขายออกจากกองสต๊อก
        self.trip(61, date(2026, 8, 12), 'W1A', '06-V-011', '41.000', None)    # เหมืองชั่งให้ตัวเอง
        Weight.objects.create(weight_id=62, date=date(2026, 8, 12), bws_id='P1V', customer_id=None,
                              carry_type_name=views.EXPORT_DOC_CARRY_TYPE, is_cancel=False,
                              weight_total=Decimal('20.000'))                   # ไม่ระบุลูกค้า
        # ปลายทางที่ติ๊กส่งออกแล้ว แต่มีแค่ใบราคาที่ยังรออนุมัติ = ยังไม่มีเส้นทาง
        BaseCustomer.objects.create(customer_id='06-V-901', customer_name='ท่าเรือใหม่')
        new_port = BaseCompanyMapBaseCustomer.objects.create(
            name='ท่าเรือใหม่', base_customer_id='06-V-901', is_export_destination=True)
        InternationalFreightRate.objects.create(
            origin=self.map_rows['06-V-011'], destination=new_port,
            effective_date=INTERNATIONAL_FREIGHT_RATE_FIRST_DATE,
            status=InternationalFreightRateStatus.PENDING)
        self.trip(63, date(2026, 8, 12), 'W1A', '06-V-901', '42.000', None)

    def test_only_routes_in_freight_rate_page_are_counted(self):
        self.addOffRouteTrips()
        qs, filters, _ = self.querySet(month='2026-08')
        self.assertEqual(self.ids(qs), {10, 30})
        self.assertEqual(self.ids(filters['off_route_qs']), {60, 61, 62, 63})

    def test_route_without_approved_rate_moves_in_once_approved(self):
        self.addOffRouteTrips()
        InternationalFreightRate.objects.filter(destination__base_customer_id='06-V-901').update(
            status=InternationalFreightRateStatus.APPROVED)
        qs, filters, _ = self.querySet(month='2026-08')
        self.assertIn(63, self.ids(qs))
        self.assertNotIn(63, self.ids(filters['off_route_qs']))

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_page_lists_off_route_trips_in_grey_box(self):
        self.addOffRouteTrips()
        user = User.objects.create_user('acc', 'acc@t.com', 'pw12345!')
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'ROI'
        session.save()

        page = self.client.get('/exportDocument/', {'month': '2026-08'})
        self.assertEqual(page.status_code, 200)
        stats = page.context['rate_stats']
        self.assertEqual(stats['off_route_trips'], 4)
        self.assertEqual(stats['wc_total'], 2)           # นับแค่เที่ยวในเส้นทาง
        by_dest = {d['destination']: d['trips'] for d in stats['off_route']}
        self.assertEqual(by_dest['ท่าเรือสุราษฎร์'], 2)    # เงินสด + ไม่ระบุลูกค้า
        html = page.content.decode('utf-8')
        self.assertIn('เส้นทางยังไม่มีในหน้าค่าขนส่ง', html)
        self.assertIn('ifr-issue-info', html)

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_warning_buttons_filter_only_the_trip_table(self):
        """ปุ่มในกล่องเตือน : ตารางเหลือเฉพาะกลุ่มนั้น แต่ตัวเลขสรุปและกล่องเตือนยังเป็นทั้งชุด"""
        self.addOffRouteTrips()
        user = User.objects.create_user('acc', 'acc@t.com', 'pw12345!')
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'ROI'
        session.save()

        def table(problem):
            page = self.client.get('/exportDocument/', {'month': '2026-08', 'problem': problem, 'page': '3'})
            self.assertEqual(page.status_code, 200)
            self.assertEqual(page.context['summary']['trip_count'], 2)       # ตัวเลขสรุปไม่เปลี่ยน
            self.assertEqual(page.context['rate_stats']['off_route_trips'], 4)
            return page, {r['weight_id'] for r in page.context['rows']}

        # ใบราคาในเทสต์ยังไม่มีทีม : ทุกเที่ยวในเส้นทางจึงเป็น "ทีมไม่อยู่ในสัญญา" และไม่มีทีม
        page, ids = table('no_contract')
        self.assertEqual(ids, {10, 30})
        self.assertEqual(page.context['problem_count'], 2)
        self.assertIn('กำลังดูเฉพาะ', page.content.decode('utf-8'))
        self.assertEqual(table('unpaid')[1], {10, 30})
        self.assertEqual(table('no_team')[1], {10, 30})
        self.assertEqual(table('out_of_range')[1], set())
        self.assertEqual(table('off_route')[1], {60, 61, 62, 63})
        # ค่าที่ไม่รู้จัก = ไม่กรอง
        page, ids = table('xxx')
        self.assertEqual(page.context['problem'], '')
        self.assertEqual(ids, {10, 30})
        # ลิงก์ของปุ่มไม่พา page เดิมไปด้วย
        self.assertNotIn('page=3', page.context['problem_query'])

    # ---------- แผงเตือนในหน้า /internationalFreightRate/ ----------

    def addBandOnOtherPortRoute(self):
        """เส้น เหมือง -> ท่าเรือบริษัทอื่น : ทุกทีมได้ช่วง 0-35 ตัน (เที่ยว 30 หนัก 42 ตัน = ไม่เข้าช่วง)
        เส้น เหมือง -> สุราษฎร์ ยังไม่มีทีมในสัญญา (เที่ยว 10 = ทีมไม่อยู่ในสัญญา)"""
        band = CarryingweightRate.objects.create(name='0-35', description='0 ถึง 35',
                                                 min_weight=Decimal('0'), max_weight=Decimal('35'))
        rate = InternationalFreightRate.objects.get(destination=self.map_rows['06-V-900'])
        InternationalFreightRateTeam.objects.create(international_freight_rate=rate, team=None,
                                                    weight_carried=band, freight_rate=Decimal('100'))
        # แถวราคาของ sheet ใช้ชนิดหินเป็นส่วนหนึ่งของคีย์ เที่ยวที่ไม่ระบุชนิดหินจึงจับสัญญาไม่ได้
        Weight.objects.filter(weight_id__in=[10, 30]).update(stone_type_name='หิน 3/4')
        return rate

    def test_freight_rate_alert_lists_missing_team_and_band(self):
        rate = self.addBandOnOtherPortRoute()
        data = views._ifrContractAlertData('2026-08')
        self.assertEqual(data['trip_count'], 2)
        self.assertEqual(data['no_contract_trips'], 1)
        self.assertEqual(data['no_contract'][0]['route'], 'ศิลาชัยสุราษฎร์ - ท่าเรือสุราษฎร์')
        self.assertEqual(data['no_contract'][0]['teams'], [{'name': views.EXPORT_DOC_NO_TEAM, 'trips': 1}])
        self.assertEqual(data['out_of_range_trips'], 1)
        group = data['out_of_range'][0]
        self.assertEqual((group['trips'], group['min'], group['max'], group['rate_id']),
                         (1, Decimal('42.000'), Decimal('42.000'), rate.id))
        team = group['teams'][0]
        self.assertEqual((team['team'], team['trips'], team['bands']), (views.EXPORT_DOC_NO_TEAM, 1, ['0-35']))

    def test_freight_rate_alert_cache_is_cleared_when_a_rate_changes(self):
        before = views._ifrContractAlertData('2026-08')
        self.assertEqual(before['out_of_range_trips'], 0)
        self.addBandOnOtherPortRoute()
        self.assertEqual(views._ifrContractAlertData('2026-08')['out_of_range_trips'], 0)   # ยังเป็นค่าที่เก็บไว้
        views._ifrContractAlertClearCache()
        self.assertEqual(views._ifrContractAlertData('2026-08')['out_of_range_trips'], 1)

    def test_rate_apis_clear_the_alert_cache(self):
        user = User.objects.create_user('acc2', 'acc2@t.com', 'pw12345!')
        self.client.force_login(user)
        with mock.patch.object(views, '_ifrContractAlertClearCache') as clear:
            self.client.delete('/internationalFreightRate/api/delete/999999/')
            self.client.patch('/internationalFreightRate/api/update/999999/', {}, content_type='application/json')
            self.client.post('/internationalFreightRate/api/create/', {}, content_type='application/json')
        self.assertEqual(clear.call_count, 3)

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_freight_rate_alert_fragment(self):
        self.addBandOnOtherPortRoute()
        user = User.objects.create_user('acc', 'acc@t.com', 'pw12345!')
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        with mock.patch.object(views, '_ifrContractAlertMonthOptions', return_value=['2026-09', '2026-08']):
            page = self.client.get('/internationalFreightRate/alert/', {'month': '2026-08'})
            fallback = self.client.get('/internationalFreightRate/alert/', {'month': 'xxx'})
        self.assertEqual(page.status_code, 200)
        html = page.content.decode('utf-8')
        self.assertIn('มีเส้นทางแล้ว แต่ทีมรถนี้ยังไม่อยู่ในสัญญา', html)
        self.assertIn('ตั้งราคาไว้แล้ว แต่น้ำหนักรถไม่เข้าช่วงที่ตั้งไว้', html)
        self.assertIn('problem=out_of_range', html)
        self.assertEqual(fallback.context['month'], '2026-08')   # ค่าแปลก -> เดือนก่อน

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
            name='สุราษฎร์พอร์ท', base_customer_id='06-V-024', is_export_destination=True)
        # ใบราคาผูกกับรหัสหลัก 06-V-024 อย่างเดียว
        InternationalFreightRate.objects.create(origin=cls.origin, destination=cls.spt,
                                                effective_date=INTERNATIONAL_FREIGHT_RATE_FIRST_DATE)

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


class ExportDocumentRemainingTeamsTests(TestCase):
    """แถว "ทีมที่เหลือ" (team = NULL) ใช้กับทีมที่ไม่มีราคาของตัวเองในใบเดียวกันเท่านั้น"""

    def test_named_team_keeps_its_own_rate(self):
        from weightapp.models import BaseCarTeam
        origin = BaseCompanyMapBaseCustomer.objects.create(name='เหมือง')
        destination = BaseCompanyMapBaseCustomer.objects.create(name='ท่าเรือ')
        named = BaseCarTeam.objects.create(car_team_id='TNAM', car_team_name='ทีมมีราคาเอง')
        other = BaseCarTeam.objects.create(car_team_id='TOTH', car_team_name='ทีมอื่น')
        band = CarryingweightRate.objects.create(name='50.01 ขึ้นไป', min_weight=Decimal('50.01'),
                                                 max_weight=Decimal('999999'))
        rate = InternationalFreightRate.objects.create(origin=origin, destination=destination,
                                                       effective_date=INTERNATIONAL_FREIGHT_RATE_FIRST_DATE)
        InternationalFreightRateTeam.objects.create(international_freight_rate=rate, team=None,
                                                    weight_carried=band, contract_freight_rate=Decimal('180'))
        InternationalFreightRateTeam.objects.create(international_freight_rate=rate, team=named,
                                                    weight_carried=band, contract_freight_rate=Decimal('200'))
        trips = [{'origin_map_id': origin.id, 'destination_map_id': destination.id, 'origin': 'เหมือง',
                  'destination': 'ท่าเรือ', 'team_id': team.pk, 'team': team.car_team_name,
                  'stone': 'หิน', 'pay_weight': Decimal('60'), 'weight_carried': None, 'date': date(2026, 9, 1)}
                 for team in (named, other)]
        rate_rows, _, _ = views._exportDocumentRatePlan(trips, '2026-09')
        by_team = {}
        for row in rate_rows:
            by_team.setdefault(row['team'], []).append(row['contract_freight_rate'])
        self.assertEqual(by_team, {'ทีมมีราคาเอง': [Decimal('200')], 'ทีมอื่น': [Decimal('180')]})


class ExportDocumentTripRateTests(SimpleTestCase):
    """อัตรารายเที่ยวฝั่ง Python ต้องเท่ากับสูตร O ในไฟล์ (รายงานค่าขนส่งเฉลี่ยใช้ตัวนี้)"""

    def rate(self, **extra):
        row = {'contract_freight_rate': Decimal('100'), 'contract_base_fuel_price': Decimal('30.00'),
               'contract_base_fuel_price_max': Decimal('30.99'), 'fuel_freight_adjustment': Decimal('2')}
        row.update(extra)
        return row

    def test_band_rules(self):
        trip_rate = views._exportDocumentTripRate
        self.assertEqual(trip_rate({'fuel_price': Decimal('30.50')}, self.rate()), Decimal('100.00'))  # ในช่วง
        self.assertEqual(trip_rate({'fuel_price': Decimal('29.00')}, self.rate()), Decimal('98.00'))   # ต่ำกว่า
        self.assertEqual(trip_rate({'fuel_price': Decimal('32.00')}, self.rate()), Decimal('102.02'))  # สูงกว่า
        single = self.rate(contract_base_fuel_price_max=None)
        self.assertEqual(trip_rate({'fuel_price': Decimal('32.00')}, single), Decimal('104.00'))      # ราคาเดียว

    def test_missing_values(self):
        trip_rate = views._exportDocumentTripRate
        self.assertEqual(trip_rate({'fuel_price': Decimal('32')}, None), Decimal(0))               # ไม่มีแถวอัตรา
        self.assertIsNone(trip_rate({'fuel_price': None}, self.rate()))                            # ไม่มีราคาน้ำมัน
        no_fuel_clause = self.rate(contract_base_fuel_price=None)
        self.assertEqual(trip_rate({'fuel_price': None}, no_fuel_clause), Decimal('100.00'))      # ไม่ปรับตามน้ำมัน
        self.assertEqual(trip_rate({'fuel_price': Decimal('32')},
                                   self.rate(contract_freight_rate=None)), Decimal(0))          # ไม่มีค่าสัญญา


class FreightAverageReportTests(TestCase):
    """รายงานค่าขนส่งเฉลี่ย : รวมรายเที่ยวเป็นกลุ่ม แยกช่วงน้ำหนัก และปุ่มโหลดในหน้าค่าขนส่ง"""

    def test_group_puts_every_banded_trip_into_its_band(self):
        """ตันเข้าช่วงน้ำหนักแม้เที่ยวนั้นยังคิดเงินไม่ได้ (เช่นไม่มีราคาน้ำมัน) ค่าเฉลี่ยคิดจากเที่ยวที่คิดเงินได้"""
        rows = [{'pay_weight': Decimal('40'), 'paid': True, 'amount': Decimal('4000'), 'weight_carried': '35.01-50'},
                {'pay_weight': Decimal('45'), 'paid': False, 'amount': Decimal(0), 'weight_carried': '35.01-50'},
                {'pay_weight': Decimal('30'), 'paid': True, 'amount': Decimal('3300'), 'weight_carried': '0-35'},
                {'pay_weight': Decimal('20'), 'paid': False, 'amount': Decimal(0), 'weight_carried': None}]
        g = views._freightReportGroup(rows, lambda r: 'all')['all']
        self.assertEqual((g['trips'], g['tons'], g['paid_tons'], g['amount']),
                         (4, Decimal('135'), Decimal('70'), Decimal('7300')))
        self.assertEqual((g['unpaid_tons'], g['no_band_tons']), (Decimal('65'), Decimal('20')))
        heavy = g['bands']['35.01-50']
        self.assertEqual((heavy['trips'], heavy['tons'], heavy['paid_tons'], heavy['amount']),
                         (2, Decimal('85'), Decimal('40'), Decimal('4000')))
        self.assertEqual(views._freightReportAvg(heavy['amount'], heavy['paid_tons']), 100.0)
        self.assertEqual(g['bands']['0-35']['tons'], Decimal('30'))

    @override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
    def test_download_has_three_sheets(self):
        import openpyxl
        from io import BytesIO
        user = User.objects.create_user('acc', 'acc@t.com', 'pw12345!')
        UserProfile.objects.create(user=user)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'ROI'
        session.save()
        month = views._ifrContractAlertMonthOptions()[1]
        response = self.client.get('/internationalFreightRate/averageReport/', {'month': month})
        self.assertEqual(response.status_code, 200)
        workbook = openpyxl.load_workbook(BytesIO(response.content))
        self.assertEqual(workbook.sheetnames, [views.FREIGHT_REPORT_SHEET_COMPANY,
                                               views.FREIGHT_REPORT_SHEET_STONE,
                                               views.FREIGHT_REPORT_SHEET_BAND])
        page = self.client.get('/internationalFreightRate/')
        self.assertContains(page, 'รายงานค่าขนส่งเฉลี่ย')


class ExportDocumentFuelPricePerTripTests(TestCase):
    """ราคาน้ำมันรายเที่ยว : ราคาวันที่วิ่งของบริษัทต้นทาง ไม่มีใช้ของปลายทาง ไม่มีทั้งคู่ = ว่าง"""

    @classmethod
    def setUpTestData(cls):
        from weightapp.models import InternationalFreightRateFuelPrice
        cls.mine = BaseCompany.objects.create(name='เหมืองทดสอบ', code='TMIN')
        cls.port = BaseCompany.objects.create(name='ท่าเรือทดสอบ', code='TPRT')
        cls.origin = BaseCompanyMapBaseCustomer.objects.create(name='เหมือง', base_company=cls.mine)
        cls.destination = BaseCompanyMapBaseCustomer.objects.create(name='ท่าเรือ', base_company=cls.port)
        for company, day, price in ((cls.mine, 1, '32.00'), (cls.port, 1, '40.00'), (cls.port, 2, '33.50')):
            InternationalFreightRateFuelPrice.objects.create(
                base_comp=company, date=date(2026, 9, day), average_fuel_price=Decimal(price))

    def trip(self, day, team='ทีม A'):
        return {'origin_map_id': self.origin.id, 'destination_map_id': self.destination.id,
                'origin': 'เหมือง', 'destination': 'ท่าเรือ', 'team': team, 'stone': 'หิน',
                'weight_carried': '0-35', 'date': date(2026, 9, day)}

    def rateRow(self, team='ทีม A', **extra):
        row = {'team': team, 'origin': 'เหมือง', 'destination': 'ท่าเรือ', 'weight_carried': '0-35',
               'stone': 'หิน', 'contract_freight_rate': Decimal('100'),
               'contract_base_fuel_price': Decimal('30'), 'fuel_freight_adjustment': Decimal('1')}
        row.update(extra)
        return row

    def test_origin_price_first_then_destination(self):
        trips = [self.trip(1), self.trip(2)]
        views._exportDocumentAssignFuelPrice(trips, [self.rateRow()])
        self.assertEqual(trips[0]['fuel_price'], Decimal('32.00'))   # ต้นทางมี ใช้ต้นทาง (ไม่ใช่ 40)
        self.assertEqual(trips[1]['fuel_price'], Decimal('33.50'))   # ต้นทางไม่มี ใช้ปลายทาง
        self.assertFalse(trips[0]['fuel_missing'] or trips[1]['fuel_missing'])

    def test_no_price_on_either_side_is_left_blank_and_flagged(self):
        trips = [self.trip(3), self.trip(3), self.trip(4)]
        summary = views._exportDocumentAssignFuelPrice(trips, [self.rateRow()])
        self.assertIsNone(trips[0]['fuel_price'])
        self.assertTrue(all(t['fuel_missing'] for t in trips))
        self.assertEqual(summary['trips'], 3)
        self.assertEqual(summary['routes'], [{'route': 'เหมือง - ท่าเรือ', 'trips': 3,
                                              'days': '3-4 ก.ย. 69'}])

    def test_missing_price_does_not_matter_without_fuel_clause(self):
        """สัญญาไม่ปรับตามน้ำมัน หรือทีมไม่มีสัญญา : ราคาว่างไม่กระทบเงิน ไม่ต้องเตือน"""
        trips = [self.trip(3), self.trip(3, team='ทีมไม่มีสัญญา')]
        summary = views._exportDocumentAssignFuelPrice(
            trips, [self.rateRow(contract_base_fuel_price=None)])
        self.assertFalse(trips[0]['fuel_missing'] or trips[1]['fuel_missing'])
        self.assertEqual(summary['trips'], 0)


class ExportDocumentDayRangesTests(TestCase):
    """ย่อวันที่ที่ขาดราคาน้ำมันในคำเตือน ให้คนเอาไปกรอกต่อได้ทันที"""

    def test_consecutive_days_collapse_to_one_range(self):
        days = {date(2026, 9, d) for d in range(1, 16)}
        self.assertEqual(views._exportDocumentDayRanges(days), '1-15 ก.ย. 69')

    def test_gaps_split_ranges_and_single_days(self):
        days = {date(2026, 9, d) for d in (1, 2, 3, 5, 7, 8)}
        self.assertEqual(views._exportDocumentDayRanges(days), '1-3, 5, 7-8 ก.ย. 69')

    def test_two_months_label_each_range(self):
        days = {date(2026, 9, 30), date(2026, 10, 1), date(2026, 10, 2)}
        self.assertEqual(views._exportDocumentDayRanges(days), '30 ก.ย. 69, 1-2 ต.ค. 69')

    def test_empty(self):
        self.assertEqual(views._exportDocumentDayRanges(set()), '')


class ExportDocumentContractStatusTests(TestCase):
    """เที่ยวในเส้นทางที่มีแล้ว : ทีมไม่อยู่ในสัญญา (กล่องแดง) / น้ำหนักไม่เข้าช่วง (ทำสีแดง)"""

    def row(self, team_id, team, pay_weight):
        return {'origin_map_id': 1, 'destination_map_id': 2, 'team_id': team_id, 'team': team,
                'origin': 'เหมือง', 'destination': 'ท่าเรือ', 'pay_weight': Decimal(pay_weight),
                'weight_carried': None}

    def test_status_per_trip(self):
        band = CarryingweightRate(name='0-35', min_weight=Decimal('0'), max_weight=Decimal('35'))
        key = {(1, 2, 10): [band]}
        rows = [self.row(10, 'ทีม ก', '30'), self.row(10, 'ทีม ก', '42'), self.row(11, 'ทีม ข', '30')]
        counts = views._exportDocumentAssignWeightCarried(rows, key)
        self.assertEqual(counts, (1, 1, 1))
        self.assertEqual([r['wc_status'] for r in rows], ['filled', 'out_of_range', 'no_contract'])
        self.assertEqual(rows[0]['weight_carried'], '0-35')

    def test_missing_contract_lists_teams_per_route(self):
        key = {(1, 2, 10): {'x'}}
        rows = [self.row(10, 'ทีม ก', '30'), self.row(11, 'ทีม ข', '30'),
                self.row(11, 'ทีม ข', '31'), self.row(12, 'ทีม ค', '30')]
        missing = views._exportDocumentMissingRoutes(rows, key)
        self.assertEqual(missing, [{'route': 'เหมือง - ท่าเรือ', 'trips': 3,
                                    'teams': [{'name': 'ทีม ข', 'trips': 2},
                                              {'name': 'ทีม ค', 'trips': 1}]}])
