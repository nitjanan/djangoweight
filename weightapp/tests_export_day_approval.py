# -*- coding: utf-8 -*-
"""หน้า /exportDocument/ : หน้าเหมืองตรวจและอนุมัติเที่ยวรายวัน (วันที่ × ต้นทาง)

กติกา
  - ระบบตรวจเอง : ทีม / นน.ต้นทาง / นน.ปลายทาง / ช่วงน้ำหนักที่แบก / ใบที่ประเภทการบรรทุกว่าง
    ขาดอย่างใดอย่างหนึ่ง = "มีปัญหา" กดอนุมัติไม่ได้
  - อนุมัติแล้วเก็บ fingerprint ของเที่ยวทั้งชุด มีคนแก้ทีหลัง = "แก้หลังอนุมัติ" ต้องตรวจใหม่
  - ตอนกดอนุมัติ server ตรวจใหม่จาก db ทุกครั้ง ข้อมูลต้องตรงกับที่คนกดเห็นบนจอ
"""
from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings

from weightapp import views
from weightapp.models import (BaseBusiness, BaseCompany, BaseCompanyMapBaseCustomer, BaseCustomer,
                              BaseWeightStation, BaseWeightType, ExportDocumentDayApproval,
                              INTERNATIONAL_FREIGHT_RATE_FIRST_DATE, InternationalFreightRate,
                              UserProfile, Weight)

PROBLEM = views.EXPORT_DOC_APPROVAL_PROBLEM
READY = views.EXPORT_DOC_APPROVAL_READY
APPROVED = views.EXPORT_DOC_APPROVAL_APPROVED
CHANGED = views.EXPORT_DOC_APPROVAL_CHANGED


def fillWeightBand(trip_rows, weight_carried_by_key):
    """แทน _exportDocumentAssignWeightCarried : ทุกเที่ยวมีช่วงน้ำหนัก ยกเว้นทีม 'ไม่มีสัญญา'
    (เทสต์นี้ไม่ได้ทดสอบการเลือกช่วงจากสัญญา ซึ่งมีเทสต์ของตัวเองอยู่แล้ว)"""
    for r in trip_rows:
        if r['team'] == 'ไม่มีสัญญา':
            r['wc_status'] = 'no_contract'
        else:
            r['wc_status'] = 'filled'
            r['weight_carried'] = '0-35'
    return len(trip_rows), 0, 0


class DayApprovalStatusTests(TestCase):
    """สถานะของแต่ละช่อง คิดจากแถวรายเที่ยวล้วน ๆ (ไม่ผ่านหน้าเว็บ)"""

    @classmethod
    def setUpTestData(cls):
        cls.mine = BaseCompanyMapBaseCustomer.objects.create(name='ศิลาชัย')
        cls.other = BaseCompanyMapBaseCustomer.objects.create(name='กงตาก')
        cls.user = User.objects.create_user('mine', 'm@t.com', 'pw12345!')

    def row(self, weight_id, day=10, origin=None, **extra):
        origin = origin or self.mine
        r = {'weight_id': weight_id, 'date': date(2026, 8, day), 'origin_map_id': origin.id,
             'origin': origin.name, 'doc_id': str(weight_id), 'origin_weight': Decimal('44.000'),
             'dest_weight': Decimal('43.900'), 'team_id': 'T1', 'team': 'ทีม A', 'team_missing': False,
             'stone': 'หิน', 'car_registration': '83-2751', 'wc_status': 'filled'}
        r.update(extra)
        return r

    def test_complete_day_is_ready(self):
        [item] = views._exportDocumentDayApprovals([self.row(1), self.row(2)])
        self.assertEqual((item['status'], item['trips'], item['problem_trips']), (READY, 2, 0))

    def test_each_missing_field_blocks_the_day(self):
        rows = [self.row(1), self.row(2, dest_weight=None), self.row(3, team_missing=True),
                self.row(4, origin_weight=None, wc_status='out_of_range')]
        [item] = views._exportDocumentDayApprovals(rows)
        self.assertEqual(item['status'], PROBLEM)
        self.assertEqual(item['problem_trips'], 3)
        self.assertEqual(item['problems'], [('ไม่ระบุทีม', 1), ('ขาด นน.ต้นทาง', 1),
                                            ('ขาด นน.ปลายทาง', 1), ('ไม่มีช่วงน้ำหนักที่แบก', 1)])

    def test_trip_dropped_for_empty_carry_type_blocks_the_day(self):
        """ใบที่ประเภทการบรรทุกว่างหลุดจากรายงาน ถ้าอนุมัติไปจะได้เที่ยวไม่ครบ"""
        [item] = views._exportDocumentDayApprovals([self.row(1)], carry_empty_rows=[self.row(9)])
        self.assertEqual((item['status'], item['carry_empty']), (PROBLEM, 1))

    def test_split_by_day_and_origin(self):
        rows = [self.row(1, day=10), self.row(2, day=11), self.row(3, day=11, origin=self.other)]
        items = views._exportDocumentDayApprovals(rows)
        self.assertEqual([(i['date'].day, i['origin']) for i in items],
                         [(11, 'กงตาก'), (11, 'ศิลาชัย'), (10, 'ศิลาชัย')])

    def test_approved_until_someone_edits(self):
        rows = [self.row(1), self.row(2)]
        fingerprint = views._exportDocumentDayFingerprint(rows)
        ExportDocumentDayApproval.objects.create(date=date(2026, 8, 10), origin=self.mine, trip_count=2,
                                                 fingerprint=fingerprint, approved_by=self.user)
        [item] = views._exportDocumentDayApprovals(rows)
        self.assertEqual(item['status'], APPROVED)
        self.assertEqual(item['approval'].approved_by, self.user)

        for edited in ([self.row(1), self.row(2, dest_weight=Decimal('40.000'))],   # แก้น้ำหนัก
                       [self.row(1), self.row(2, team_id='T2')],                     # เปลี่ยนทีม
                       [self.row(1)],                                                # เที่ยวหาย (ยกเลิกใบ)
                       [self.row(1), self.row(2), self.row(3)]):                     # เที่ยวเพิ่ม
            [item] = views._exportDocumentDayApprovals(edited)
            self.assertEqual(item['status'], CHANGED)

    def test_contract_change_does_not_count_as_edit(self):
        """ช่วงน้ำหนักที่แบกมาจากสัญญาของบัญชี ไม่อยู่ใน fingerprint"""
        a = views._exportDocumentDayFingerprint([self.row(1, weight_carried='0-35')])
        b = views._exportDocumentDayFingerprint([self.row(1, weight_carried='35-40')])
        self.assertEqual(a, b)

    def test_board_is_days_by_origins(self):
        rows = [self.row(1, day=10), self.row(2, day=11, origin=self.other)]
        board = views._exportDocumentApprovalBoard(views._exportDocumentDayApprovals(rows))
        self.assertEqual([o['name'] for o in board['origins']], ['กงตาก', 'ศิลาชัย'])
        self.assertEqual([r['date'].day for r in board['rows']], [11, 10])
        day11, day10 = board['rows']
        self.assertEqual([c and c['origin'] for c in day11['cells']], ['กงตาก', None])
        self.assertEqual([c and c['origin'] for c in day10['cells']], [None, 'ศิลาชัย'])
        self.assertEqual(board['counts'][READY], 2)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
@mock.patch.object(views, '_exportDocumentAssignWeightCarried', side_effect=fillWeightBand)
class DayApprovalPageTests(TestCase):
    """ตารางบนหน้าเว็บ + ปุ่มอนุมัติ / ยกเลิก ผ่าน view จริง"""

    @classmethod
    def setUpTestData(cls):
        BaseBusiness.objects.create(id=1, name='ขายหินในประเทศ')
        BaseBusiness.objects.create(id=views.EXPORT_DOC_OWN_PORT_BIZ_ID, name='ขายหินส่งออก')
        BaseWeightType.objects.create(id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID, name='ขาย')
        mine = BaseCompany.objects.create(name='ศิลาชัย', code='SLC', biz_id=1)
        port = BaseCompany.objects.create(name='ท่าเรือสุราษฏร์', code='STPS',
                                          biz_id=views.EXPORT_DOC_OWN_PORT_BIZ_ID)
        for sid, company in (('W1A', mine), ('P1V', port)):
            BaseWeightStation.objects.create(
                id=sid, company=company, weight_type_id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID)
        maps = {}
        for code, name, company in (('06-V-011', 'ศิลาชัยสุราษฎร์', mine),
                                    ('06-V-013', 'ท่าเรือสุราษฎร์', port),
                                    ('06-V-900', 'ท่าเรือบริษัทอื่น', None)):
            BaseCustomer.objects.create(customer_id=code, customer_name=name)
            maps[code] = BaseCompanyMapBaseCustomer.objects.create(
                name=name, base_customer_id=code, base_company=company, is_export_destination=True)
        cls.origin = maps['06-V-011']
        for dest in ('06-V-013', '06-V-900'):
            InternationalFreightRate.objects.create(origin=cls.origin, destination=maps[dest],
                                                    effective_date=INTERNATIONAL_FREIGHT_RATE_FIRST_DATE)
        # 10 ส.ค. ครบทุกช่อง (ใบท่าเรือ 1 + ใบเหมืองไปท่าเรือบริษัทอื่น 1)
        cls.trip(10, 10, 'P1V', '06-V-011', '44.260', '44.380')
        cls.trip(30, 10, 'W1A', '06-V-900', '42.000', '41.500')
        # 11 ส.ค. ยังไม่กรอก นน.ปลายทาง
        cls.trip(31, 11, 'W1A', '06-V-900', '42.000', None)

        cls.user = User.objects.create_user('mine', 'm@t.com', 'pw12345!')
        UserProfile.objects.create(user=cls.user).company.add(mine, port)

    @staticmethod
    def trip(weight_id, day, bws_id, customer_id, weight_total, origin_weight):
        Weight.objects.create(
            weight_id=weight_id, date=date(2026, 8, day), bws_id=bws_id, customer_id=customer_id,
            customer_name=BaseCustomer.objects.get(pk=customer_id).customer_name,
            carry_type_name=views.EXPORT_DOC_CARRY_TYPE, is_cancel=False, car_team_name='ทีม A',
            car_registration_name='83-2751', doc_id=str(weight_id), stone_type_name='หิน',
            weight_total=Decimal(weight_total),
            origin_weight=None if origin_weight is None else Decimal(origin_weight))

    def setUp(self):
        cache.clear()
        self.client.force_login(self.user)
        self.useTab('SLC')

    def useTab(self, code):
        session = self.client.session
        session['company_code'] = code
        session.save()

    def page(self, **params):
        params.setdefault('month', '2026-08')
        return self.client.get('/exportDocument/approval/', params)

    def board(self, **params):
        return self.page(**params).context['board']

    def cell(self, board, day):
        row = next(r for r in board['rows'] if r['date'].day == day)
        return next(c for c in row['cells'] if c)

    def post(self, action, day, fingerprint=''):
        return self.client.post('/exportDocument/approveDay/', {
            'action': action, 'date': '2026-08-%02d' % day, 'origin': self.origin.id,
            'fingerprint': fingerprint, 'next': '/exportDocument/approval/?month=2026-08#board'})

    def test_page_shows_status_per_day(self, _wc):
        board = self.board()
        self.assertEqual(self.cell(board, 10)['status'], READY)
        self.assertEqual(self.cell(board, 10)['trips'], 2)
        self.assertEqual(self.cell(board, 11)['status'], PROBLEM)
        self.assertEqual(self.cell(board, 11)['problems'], [('ขาด นน.ปลายทาง', 1)])
        html = self.page().content.decode('utf-8')
        self.assertIn('รออนุมัติ', html)
        self.assertNotIn('name="action" value="approve"', html)   # ตารางรวมไม่มีปุ่มอนุมัติ
        self.assertNotIn('{{', html)

    def test_port_tab_has_no_board(self, _wc):
        self.useTab('STPS')
        page = self.page()
        self.assertIsNone(page.context['board'])
        self.assertIn('แท็บท่าเรือเห็นเฉพาะเที่ยวที่ชั่งที่ท่าเรือนี้', page.content.decode('utf-8'))

    def test_export_page_only_links_to_approval_page(self, _wc):
        """หน้า /exportDocument/ ไม่มีตารางอนุมัติแล้ว เหลือปุ่มไปหน้าแยก"""
        page = self.client.get('/exportDocument/', {'month': '2026-08'})
        html = page.content.decode('utf-8')
        self.assertIn('/exportDocument/approval/?month=2026-08', html)
        self.assertNotIn('approval_board', page.context)
        self.assertNotIn('name="action" value="approve"', html)
        self.useTab('STPS')
        html = self.client.get('/exportDocument/', {'month': '2026-08'}).content.decode('utf-8')
        self.assertNotIn('/exportDocument/approval/?month=', html)

    def test_approve_then_edit_then_revoke(self, _wc):
        fingerprint = self.cell(self.board(), 10)['fingerprint']
        response = self.post('approve', 10, fingerprint)
        self.assertRedirects(response, '/exportDocument/approval/?month=2026-08#board',
                             fetch_redirect_response=False)
        saved = ExportDocumentDayApproval.objects.get(date=date(2026, 8, 10), origin=self.origin)
        self.assertEqual((saved.trip_count, saved.approved_by), (2, self.user))
        self.assertEqual(self.cell(self.board(), 10)['status'], APPROVED)

        # แก้น้ำหนักปลายทางหลังอนุมัติ -> ต้องตรวจใหม่
        Weight.objects.filter(weight_id=30).update(origin_weight=Decimal('41.000'))
        self.assertEqual(self.cell(self.board(), 10)['status'], CHANGED)

        self.post('revoke', 10)
        self.assertFalse(ExportDocumentDayApproval.objects.exists())
        self.assertEqual(self.cell(self.board(), 10)['status'], READY)

    def test_cannot_approve_day_with_problems(self, _wc):
        fingerprint = self.cell(self.board(), 11)['fingerprint']
        self.post('approve', 11, fingerprint)
        self.assertFalse(ExportDocumentDayApproval.objects.exists())

    def test_cannot_approve_stale_page(self, _wc):
        """เปิดหน้าค้างไว้ ระหว่างนั้นมีเที่ยวเพิ่ม : fingerprint ไม่ตรง ไม่บันทึก"""
        fingerprint = self.cell(self.board(), 10)['fingerprint']
        self.trip(32, 10, 'W1A', '06-V-900', '42.500', '42.100')
        self.post('approve', 10, fingerprint)
        self.assertFalse(ExportDocumentDayApproval.objects.exists())

    def test_link_back_to_export_page_filters_trip_table(self, _wc):
        """ลิงก์ "เปิดวันนี้ในหน้า Export เอกสาร" : ตารางรายเที่ยวเหลือวันนั้น ต้นทางนั้น"""
        page = self.client.get('/exportDocument/', {'month': '2026-08', 'date_from': '2026-08-11',
                                                    'date_to': '2026-08-11', 'origin': self.origin.id,
                                                    'problem': 'approval'})
        self.assertEqual([r['weight_id'] for r in page.context['rows']], [31])
        self.assertEqual(page.context['origin_label'], 'ศิลาชัยสุราษฎร์')
        self.assertNotIn('{{', page.content.decode('utf-8'))

    def test_other_tab_cannot_touch_this_origin(self, _wc):
        """แท็บเหมืองอื่น / แท็บท่าเรือ ยกเลิกหรืออนุมัติต้นทางที่ไม่ใช่ของตัวเองไม่ได้ แม้จะยิงคำขอเอง"""
        fingerprint = self.cell(self.board(), 10)['fingerprint']
        self.post('approve', 10, fingerprint)
        UserProfile.objects.get(user=self.user).company.add(
            BaseCompany.objects.create(name='กงตาก', code='KTK', biz_id=1))
        for tab in ('KTK', 'STPS'):
            self.useTab(tab)
            self.post('revoke', 10)
            self.assertTrue(ExportDocumentDayApproval.objects.exists())
        ExportDocumentDayApproval.objects.filter(date=date(2026, 8, 10), origin=self.origin).delete()
        self.useTab('KTK')
        self.post('approve', 10, fingerprint)
        self.assertFalse(ExportDocumentDayApproval.objects.exists())

    def test_tab_not_in_user_profile_cannot_approve(self, _wc):
        """ปลอมแท็บใน session เป็นเหมืองที่ไม่ได้ผูกกับผู้ใช้ (setSessionCompany รับรหัสอะไรก็ได้) : อนุมัติไม่ได้"""
        fingerprint = self.cell(self.board(), 10)['fingerprint']
        other = User.objects.create_user('port', 'p@t.com', 'pw12345!')
        UserProfile.objects.create(user=other).company.add(BaseCompany.objects.get(code='STPS'))
        self.client.force_login(other)
        for tab in ('SLC', 'ROI', 'ALL'):
            self.useTab(tab)
            self.post('approve', 10, fingerprint)
            self.assertFalse(ExportDocumentDayApproval.objects.exists())

    def test_day_view_lists_the_day_and_offers_approve(self, _wc):
        """กดช่องในตารางรวม -> หน้าดูรายวัน : เที่ยวของวันนั้น ต้นทางนั้น + ปุ่มอนุมัติ (หน้าต่างยืนยันมีรายเที่ยว)"""
        page = self.page(date='2026-08-10', origin=self.origin.id)
        day = page.context['day']
        self.assertEqual((day['status'], day['trips']), (READY, 2))
        self.assertEqual([t['weight_id'] for t in page.context['day_trips']], [10, 30])   # เรียงตามเลขที่ชั่ง
        self.assertEqual(day['totals']['origin_weight'], Decimal('86.380'))   # ใบท่าเรือ 44.380 + ใบเหมือง 42.000
        html = page.content.decode('utf-8')
        self.assertIn('อนุมัติวันนี้', html)
        self.assertIn('ยืนยันอนุมัติ 2 เที่ยว', html)
        self.assertEqual(html.count('name="action" value="approve"'), 1)
        self.assertEqual((page.context['prev_day'], page.context['next_day']), (None, date(2026, 8, 11)))
        self.assertNotIn('{{', html)

    def test_day_view_only_problems(self, _wc):
        page = self.page(date='2026-08-11', origin=self.origin.id, problems='1')
        self.assertEqual([t['weight_id'] for t in page.context['day_trips']], [31])
        self.assertEqual(page.context['day_trips'][0]['approval_problems'], ['ขาด นน.ปลายทาง'])
        self.assertNotIn('name="action" value="approve"', page.content.decode('utf-8'))

    def test_bad_day_params_fall_back_to_board(self, _wc):
        page = self.page(date='not-a-date', origin=self.origin.id)
        self.assertIsNone(page.context['day'])
        self.assertIsNotNone(page.context['board'])

    def test_day_view_lists_slips_with_empty_carry_type(self, _wc):
        """ใบที่ประเภทการบรรทุกว่าง (ไม่อยู่ในรายงาน) โชว์ในหน้าดูรายวันเลย ไม่ต้องข้ามไปหาหน้า export"""
        Weight.objects.create(
            weight_id=40, date=date(2026, 8, 10), bws_id='W1A', customer_id='06-V-900',
            customer_name='ท่าเรือบริษัทอื่น', carry_type_name=None, is_cancel=False, car_team_name='ทีม A',
            car_registration_name='80-8753', doc_id='029757', stone_type_name='หิน',
            weight_total=Decimal('28.990'), origin_weight=Decimal('29.060'))
        page = self.page(date='2026-08-10', origin=self.origin.id)
        day = page.context['day']
        self.assertEqual((day['status'], day['trips'], day['carry_empty']), (PROBLEM, 2, 1))
        self.assertEqual([t['weight_id'] for t in day['carry_list']], [40])
        html = page.content.decode('utf-8')
        self.assertIn('ใบชั่งที่ไม่ได้นับ เพราะประเภทการบรรทุกว่าง (1 ใบ)', html)
        self.assertIn('029757', html)

    def test_get_is_not_allowed_to_approve(self, _wc):
        response = self.client.get('/exportDocument/approveDay/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ExportDocumentDayApproval.objects.exists())


class ConfirmTripEditHistoryLookupTests(TestCase):
    """ยืนยันไฟล์กรอก นน.ปลายทาง : หาแถวประวัติที่ signal เพิ่งสร้าง ด้วยคอลัมน์ที่มี index (weight_table_id)

    weight_history.weight_id ไม่มี index ค้นด้วยคอลัมน์นี้ = ไล่ทั้งตาราง (~2.8 แสนแถว) ทีละเที่ยว
    ไฟล์ 1,096 เที่ยวจึงค้างใน transaction เดียว 20+ นาที ถือ lock ใบชั่งไว้ทั้งหมด
    กดยืนยันซ้ำระหว่างนั้นเลยเจอ (1205) Lock wait timeout exceeded
    """

    @classmethod
    def setUpTestData(cls):
        BaseBusiness.objects.create(id=views.EXPORT_DOC_OWN_PORT_BIZ_ID, name='ขายหินส่งออก')
        port = BaseCompany.objects.create(name='ท่าเรือสุราษฏร์', code='STPS',
                                          biz_id=views.EXPORT_DOC_OWN_PORT_BIZ_ID)
        BaseWeightStation.objects.create(id='P1V', company=port)
        BaseCustomer.objects.create(customer_id='06-V-011', customer_name='ศิลาชัยสุราษฎร์')
        Weight.objects.create(weight_id=10, date=date(2026, 8, 10), bws_id='P1V', customer_id='06-V-011',
                              carry_type_name=views.EXPORT_DOC_CARRY_TYPE, is_cancel=False,
                              doc_id='10', weight_total=Decimal('44.000'))
        cls.user = User.objects.create_user('mine', 'm@t.com', 'pw12345!')
        UserProfile.objects.create(user=cls.user)

    def test_history_found_by_indexed_column(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from weightapp.models import WeightHistory

        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'STPS'
        session[views.EXPORT_DOC_EDIT_SESSION_KEY] = {'changes': [
            {'weight_id': 10, 'date': '10/08/2026', 'doc_id': '10', 'fields': [],
             'apply': {'origin_weight': '43.500'}}]}
        session.save()

        with CaptureQueriesContext(connection) as ctx:
            self.client.post('/exportDocument/edit/confirm/')

        self.assertEqual(Weight.objects.get(pk=10).origin_weight, Decimal('43.500'))
        history = WeightHistory.objects.get(weight_table_id=10)
        self.assertEqual(history.user_update, self.user)
        lookups = [q['sql'] for q in ctx.captured_queries
                   if q['sql'].startswith('SELECT') and 'FROM `weight_history`' in q['sql']]
        self.assertTrue(lookups)
        for sql in lookups:
            self.assertIn('`weight_history`.`weight_table_id`', sql)
            self.assertNotIn('`weight_history`.`weight_id` =', sql)
