# -*- coding: utf-8 -*-
"""issue #137 : บัญชีแบ่งนามที่จ่าย แล้วออกไฟล์บัญชีทีละนาม

กติกา (ตามที่บัญชีทำจริง : ดูจากใบปะหน้าเหมือง ไม่ได้ดูรายเที่ยว)
  - แถวทีม = เส้นทาง × หิน(ช่วงน้ำหนัก) × ทีม แบบใบปะหน้า ของทุกต้นทางทั้งเดือน (ทำจากแท็บที่เห็นทุกต้นทางเท่านั้น)
  - เป้า = นามไหนจ่ายหินชนิดไหนกี่ตัน (ได้มาก่อน) แล้วแบ่งแถวทีมจากกองกลางให้ครบเป้า
  - ปกติเลือกนามให้ทั้งแถว · แถวเดียวแบ่งให้หลายนามได้โดยกรอกตัน · ไม่ได้เลือก = ค้าง stock
  - ห้ามเกินตันของแถว / เกินเป้า / เลือกหินที่ไม่มีเป้า · นามที่ยังไม่ครบเป้าออกไฟล์ไม่ได้
  - ไฟล์ของนาม : เที่ยวของแถวที่รับ น้ำหนักจริง · แถวที่แบ่ง เขียนสัดส่วนลง AD ให้ชีตสรุปคูณเอง
    หัวเอกสารเป็นชื่อนาม · ชีต oil ติดไว้ แต่สรุปจ่ายรถร่วมยังไม่หัก oil
"""
import io
from datetime import date
from decimal import Decimal
from urllib.parse import quote

import openpyxl
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings

from weightapp import views
from weightapp.models import (BaseBusiness, BaseCompany, BaseCompanyMapBaseCustomer, BaseCustomer,
                              BaseWeightStation, BaseWeightType, ExportDocumentPayerAllocation,
                              ExportDocumentPayerRowAllocation, INTERNATIONAL_FREIGHT_RATE_FIRST_DATE,
                              InternationalFreightRate, InternationalFreightRateTeam, UserProfile, Weight)

MONTH = date(2026, 8, 1)
STONE_2 = 'หิน 2 นิ้ว'
STONE_6 = 'หิน 6 นิ้ว'
OWN_PORT = 'ท่าเรือสุราษฎร์'
OTHER_PORT = 'ท่าเรือบริษัทอื่น'


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PayerAllocationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        BaseBusiness.objects.create(id=1, name='ขายหินในประเทศ')
        BaseBusiness.objects.create(id=views.EXPORT_DOC_OWN_PORT_BIZ_ID, name='ขายหินส่งออก')
        BaseWeightType.objects.create(id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID, name='ขาย')
        cls.mine = BaseCompany.objects.create(name='ศิลาชัย', code='SLC', biz_id=1)
        cls.creative = BaseCompany.objects.create(name='ครีเอทีฟ', code='CTM', biz_id=1)
        port = BaseCompany.objects.create(name='ท่าเรือสุราษฏร์', code='STPS',
                                          biz_id=views.EXPORT_DOC_OWN_PORT_BIZ_ID)
        BaseCompany.objects.create(name='ร้อยเกาะ', code='ROI')   # ผู้รับเงิน : ไม่ใช่นามที่จ่าย
        for sid, company in (('W1A', cls.mine), ('P1V', port)):
            BaseWeightStation.objects.create(
                id=sid, company=company, weight_type_id=views.EXPORT_DOC_OTHER_PORT_WEIGHT_TYPE_ID)
        maps = {}
        for code, name, company in (('06-V-011', 'ศิลาชัยสุราษฎร์', cls.mine),
                                    ('06-V-013', OWN_PORT, port),
                                    ('06-V-900', OTHER_PORT, None)):
            BaseCustomer.objects.create(customer_id=code, customer_name=name)
            maps[code] = BaseCompanyMapBaseCustomer.objects.create(
                name=name, base_customer_id=code, base_company=company, is_export_destination=True)
        for dest in ('06-V-013', '06-V-900'):
            InternationalFreightRate.objects.create(origin=maps['06-V-011'], destination=maps[dest],
                                                    effective_date=INTERNATIONAL_FREIGHT_RATE_FIRST_DATE)
        # แถวทีม 3 แถว (ทีม A ทั้งหมด) :
        #   ศิลาชัย -> ท่าเรือสุราษฎร์ หิน 2 นิ้ว 44.260 (ใบท่าเรือ ปลายทางน้อยกว่า)
        #   ศิลาชัย -> ท่าเรือบริษัทอื่น หิน 2 นิ้ว 41.500 · หิน 6 นิ้ว 29.500
        cls.trip(10, 'P1V', '06-V-011', STONE_2, '44.260', '44.380')
        cls.trip(30, 'W1A', '06-V-900', STONE_2, '42.000', '41.500')
        cls.trip(31, 'W1A', '06-V-900', STONE_6, '30.000', '29.500')

        cls.user = User.objects.create_user('acc', 'a@t.com', 'pw12345!')
        UserProfile.objects.create(user=cls.user).company.add(
            *BaseCompany.objects.filter(code__in=('ROI', 'SLC')))

    @staticmethod
    def trip(weight_id, bws_id, customer_id, stone, weight_total, origin_weight):
        Weight.objects.create(
            weight_id=weight_id, date=date(2026, 8, 10), bws_id=bws_id, customer_id=customer_id,
            customer_name=BaseCustomer.objects.get(pk=customer_id).customer_name,
            carry_type_name=views.EXPORT_DOC_CARRY_TYPE, is_cancel=False, car_team_name='ทีม A',
            car_registration_name='83-2751', doc_id=str(weight_id), stone_type_name=stone,
            weight_total=Decimal(weight_total), origin_weight=Decimal(origin_weight))

    def setUp(self):
        cache.clear()
        self.client.force_login(self.user)
        self.useTab('ROI')

    def useTab(self, code):
        session = self.client.session
        session['company_code'] = code
        session.save()

    def page(self):
        return self.client.get('/exportDocument/payer/', {'month': '2026-08'})

    def plan(self):
        return self.page().context['plan']

    @staticmethod
    def team_rows(plan):
        """{(ปลายทาง, หิน): แถวทีม}"""
        return {(r['destination'], r['stone']): r
                for g in plan['groups'] for p in g['products'] for r in p['rows']}

    def save(self, modes=None, splits=None, targets=None):
        """modes = {(ปลายทาง, หิน): บริษัท | 'split'} · splits = {((ปลายทาง, หิน), บริษัท): ตัน}
        targets = {(บริษัท, หิน): ตัน} · แถวที่ไม่ได้ระบุ = ค้าง stock"""
        plan = self.plan()
        data = {'month': '2026-08'}
        for i, s in enumerate(plan['stones']):
            data['stone-%d' % i] = s['stone']
            for (company, stone), tons in (targets or {}).items():
                if stone == s['stone']:
                    data['target-%d-%d' % (company.id, i)] = tons
        for where, row in self.team_rows(plan).items():
            data['row-%d' % row['index']] = row['key']
            mode = (modes or {}).get(where)
            data['mode-%d' % row['index']] = (mode if isinstance(mode, str) else
                                              str(mode.id) if mode else '')
        for (where, company), tons in (splits or {}).items():
            data['split-%d-%d' % (company.id, self.team_rows(plan)[where]['index'])] = tons
        return self.client.post('/exportDocument/payer/', data, follow=True)

    def targets(self):
        """เป้า : ศิลาชัย หิน 2 นิ้ว 64.26 · ครีเอทีฟ หิน 2 นิ้ว 21.5"""
        return {(self.mine, STONE_2): '64.26', (self.creative, STONE_2): '21.5'}

    def allocate(self):
        """ศิลาชัย : ท่าเรือเราทั้งแถว 44.26 + แบ่งแถวท่าเรือบริษัทอื่นหิน 2 นิ้ว 20 ตัน = ครบเป้า 64.26
        ครีเอทีฟ : อีก 21.5 ตัน = ครบเป้า · หิน 6 นิ้ว ค้าง stock"""
        return self.save(modes={(OWN_PORT, STONE_2): self.mine, (OTHER_PORT, STONE_2): 'split'},
                         splits={((OTHER_PORT, STONE_2), self.mine): '20',
                                 ((OTHER_PORT, STONE_2), self.creative): '21.5'},
                         targets=self.targets())

    # ---------- หน้าแบ่งนาม ----------

    def test_team_rows_like_mine_cover(self):
        plan = self.plan()
        rows = self.team_rows(plan)
        self.assertEqual({k: (r['trips'], r['tons']) for k, r in rows.items()},
                         {(OWN_PORT, STONE_2): (1, Decimal('44.260')),
                          (OTHER_PORT, STONE_2): (1, Decimal('41.500')),
                          (OTHER_PORT, STONE_6): (1, Decimal('29.500'))})
        self.assertEqual([g['label'] for g in plan['groups']],
                         ['ศิลาชัยสุราษฎร์-ท่าเรือบริษัทอื่น', 'ศิลาชัยสุราษฎร์-ท่าเรือสุราษฎร์'])
        self.assertTrue(all(r['team'] == 'ทีม A' and r['mode'] == '' for r in rows.values()))
        self.assertEqual([(s['stone'], s['tons'], s['stock']) for s in plan['stones']],
                         [(STONE_2, Decimal('85.760'), Decimal('85.760')),
                          (STONE_6, Decimal('29.500'), Decimal('29.500'))])
        names = [c['name'] for c in plan['companies']]
        self.assertIn('ครีเอทีฟ', names)
        self.assertNotIn('ร้อยเกาะ', names)
        self.assertTrue(plan['can_export'])

    def test_tab_not_in_user_profile_is_refused(self):
        """ปลอมแท็บร้อยเกาะใน session (setSessionCompany รับรหัสอะไรก็ได้) : ดู / บันทึก / ออกไฟล์ไม่ได้"""
        other = User.objects.create_user('mine2', 'b@t.com', 'pw12345!')
        UserProfile.objects.create(user=other).company.add(self.mine)
        self.client.force_login(other)
        self.useTab('ROI')
        self.assertEqual(self.page().status_code, 403)
        response = self.client.post('/exportDocument/payer/', {
            'month': '2026-08', 'stone-0': STONE_2, 'target-%d-0' % self.mine.id: '10'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ExportDocumentPayerAllocation.objects.exists())
        self.assertEqual(self.download(self.mine).status_code, 403)

    def test_mine_tab_cannot_allocate(self):
        """ยอดต้องเป็นของทุกต้นทาง แท็บเหมืองเห็นไม่ครบ"""
        self.useTab('SLC')
        page = self.page()
        self.assertIsNone(page.context['plan'])
        self.assertIn('แท็บ <strong>ร้อยเกาะ</strong>', page.content.decode('utf-8'))

    def test_whole_row_and_split_then_edit(self):
        self.allocate()
        saved = {(a.destination, a.company_id): a.tons
                 for a in ExportDocumentPayerRowAllocation.objects.filter(month=MONTH)}
        self.assertEqual(saved, {(OWN_PORT, self.mine.id): None,
                                 (OTHER_PORT, self.mine.id): Decimal('20.000'),
                                 (OTHER_PORT, self.creative.id): Decimal('21.500')})
        plan = self.plan()
        rows = self.team_rows(plan)
        self.assertEqual(rows[(OWN_PORT, STONE_2)]['mode'], str(self.mine.id))
        self.assertEqual(rows[(OTHER_PORT, STONE_2)]['mode'], views.EXPORT_DOC_PAYER_SPLIT)
        self.assertEqual(rows[(OTHER_PORT, STONE_6)]['stock'], Decimal('29.500'))
        stone2 = plan['stones'][0]
        chosen = {c['company_id']: c['chosen'] for c in stone2['cells']}
        self.assertEqual(chosen[self.mine.id], Decimal('64.260'))     # 44.260 ทั้งแถว + 20
        self.assertEqual(chosen[self.creative.id], Decimal('21.500'))
        self.assertEqual(stone2['stock'], Decimal('0'))
        self.assertEqual(plan['stones'][1]['stock'], Decimal('29.500'))

        self.assertTrue(all(c['complete'] for c in plan['companies'] if c['id'] in (self.mine.id, self.creative.id)))

        # แก้ : แถวที่แบ่งไว้ให้ครีเอทีฟทั้งแถว (เป้า 41.5) · ท่าเรือเรากลับเป็นค้าง stock
        self.save(modes={(OTHER_PORT, STONE_2): self.creative}, targets={(self.creative, STONE_2): '41.5'})
        saved = {(a.destination, a.company_id): a.tons
                 for a in ExportDocumentPayerRowAllocation.objects.filter(month=MONTH)}
        self.assertEqual(saved, {(OTHER_PORT, self.creative.id): None})
        self.assertEqual(ExportDocumentPayerRowAllocation.objects.get().updated_by, self.user)

    def test_split_over_row_is_rejected(self):
        response = self.save(modes={(OTHER_PORT, STONE_2): 'split'},
                             splits={((OTHER_PORT, STONE_2), self.mine): '30',
                                     ((OTHER_PORT, STONE_2), self.creative): '20'},
                             targets={(self.mine, STONE_2): '30', (self.creative, STONE_2): '20'})
        self.assertIn('เกินยอดของแถว', response.content.decode('utf-8'))
        self.assertFalse(ExportDocumentPayerRowAllocation.objects.exists())

    def test_bad_input_saves_nothing(self):
        self.save(modes={(OWN_PORT, STONE_2): self.mine}, targets={(self.mine, STONE_2): '-1'})
        self.save(modes={(OTHER_PORT, STONE_2): 'split'}, splits={((OTHER_PORT, STONE_2), self.mine): 'abc'})
        self.assertFalse(ExportDocumentPayerRowAllocation.objects.exists())
        self.assertFalse(ExportDocumentPayerAllocation.objects.exists())

    def test_targets_compare_with_chosen_rows(self):
        self.save(modes={(OWN_PORT, STONE_2): self.mine},
                  targets={(self.mine, STONE_2): '50', (self.creative, STONE_6): '29.5'})
        target = ExportDocumentPayerAllocation.objects.get(month=MONTH, company=self.mine)
        self.assertEqual((target.stone_type_name, target.tons, target.updated_by),
                         (STONE_2, Decimal('50.000'), self.user))
        plan = self.plan()
        cell = next(c for c in plan['stones'][0]['cells'] if c['company_id'] == self.mine.id)
        self.assertEqual((cell['target'], cell['chosen'], cell['status'], cell['gap']),
                         (Decimal('50.000'), Decimal('44.260'), 'short', Decimal('5.740')))
        # มีเป้าแต่ยังไม่ครบ : ติ๊กเป็นนามของเดือนนี้ แต่ออกไฟล์ไม่ได้
        companies = {c['id']: c for c in plan['companies']}
        self.assertEqual((companies[self.mine.id]['complete'], companies[self.mine.id]['problems']),
                         (False, [STONE_2]))
        self.assertEqual((companies[self.creative.id]['selected'], companies[self.creative.id]['tons']),
                         (True, Decimal('0')))
        self.assertTrue(plan['can_export'])      # ยังไม่ครบไม่ได้ผิด แค่นามนั้นยังออกไฟล์ไม่ได้
        self.assertIn('ยังแบ่งไม่ครบเป้า', self.download(self.mine).content.decode('utf-8'))

    def test_rows_need_a_target(self):
        response = self.save(modes={(OWN_PORT, STONE_2): self.mine})
        self.assertIn('ยังไม่ได้ตั้งเป้า', response.content.decode('utf-8'))
        self.assertFalse(ExportDocumentPayerRowAllocation.objects.exists())

    def test_rows_cannot_go_over_target(self):
        """เป้าศิลาชัย 50 : ท่าเรือเรา 44.26 + บริษัทอื่น 41.5 ทั้งแถว = 85.76 เกินเป้า"""
        response = self.save(modes={(OWN_PORT, STONE_2): self.mine, (OTHER_PORT, STONE_2): self.mine},
                             targets={(self.mine, STONE_2): '50'})
        self.assertIn('เกินเป้า', response.content.decode('utf-8'))
        self.assertFalse(ExportDocumentPayerRowAllocation.objects.exists())
        # แบ่งแถวที่สองเอาแค่ที่ขาด 5.74 = ครบเป้าพอดี ออกไฟล์ได้
        self.save(modes={(OWN_PORT, STONE_2): self.mine, (OTHER_PORT, STONE_2): 'split'},
                  splits={((OTHER_PORT, STONE_2), self.mine): '5.74'},
                  targets={(self.mine, STONE_2): '50'})
        mine = next(c for c in self.plan()['companies'] if c['id'] == self.mine.id)
        self.assertEqual((mine['tons'], mine['complete']), (Decimal('50.000'), True))
        self.assertEqual(self.download(self.mine)['Content-Type'],
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_export_page_links_payer_page_only_in_sees_all_tab(self):
        html = self.client.get('/exportDocument/', {'month': '2026-08'}).content.decode('utf-8')
        self.assertIn('/exportDocument/payer/?month=2026-08', html)
        self.useTab('SLC')
        html = self.client.get('/exportDocument/', {'month': '2026-08'}).content.decode('utf-8')
        self.assertNotIn('/exportDocument/payer/?month=', html)

    # ---------- ไฟล์ของนาม ----------

    def download(self, company):
        return self.client.get('/exportDocument/payer/excel/', {'month': '2026-08', 'company': company.id})

    def trip_cells(self, wb):
        """{เลขที่ชั่ง: (J นน.ต้นทาง, K นน.ปลายทาง, สัดส่วน)}
        สัดส่วน = ค่าที่สูตร AD หาได้จากชีตซ่อน สัดส่วนนาม ด้วยคีย์ของแถว (None = ทั้งเที่ยว)"""
        ws = wb['บันทึกรายเที่ยว']
        table = {}
        if views.EXPORT_DOC_PAYER_SHARE_SHEET in wb.sheetnames:
            shares = wb[views.EXPORT_DOC_PAYER_SHARE_SHEET]
            self.assertEqual(shares.sheet_state, 'hidden')
            table = {shares.cell(row=r, column=1).value: shares.cell(row=r, column=2).value
                     for r in range(2, shares.max_row + 1)}
        first = views.EXPORT_DOC_FIRST_DATA_ROW
        out = {}
        for row in range(first, first + 10):
            doc = ws.cell(row=row, column=9).value
            if doc:
                ad = ws.cell(row=row, column=views.EXPORT_DOC_PAYER_SHARE_COL).value
                if ad is not None:
                    self.assertIn('VLOOKUP($I%d&"|"&$B%d&"|"&$F%d' % (row, row, row), ad)
                key = views._exportDocumentPayerShareKey(doc, ws.cell(row=row, column=2).value,
                                                         ws.cell(row=row, column=6).value)
                out[doc] = (ws.cell(row=row, column=10).value, ws.cell(row=row, column=11).value,
                            table.get(key))
        return out

    def test_sort_filters_on_list_sheets_only(self):
        """ปุ่มกรอง / เรียงเฉพาะชีตที่ 1 แถว = 1 รายการ · ชีตสรุป / ปะหน้า / รายการมาตรฐาน ไม่ใส่"""
        self.allocate()
        wb = openpyxl.load_workbook(io.BytesIO(self.download(self.mine).content))
        self.assertTrue(wb[views.EXPORT_DOC_EXPRESS_SHEET].auto_filter.ref.startswith('A4:I'))
        self.assertEqual(wb['บันทึกรายเที่ยว'].auto_filter.ref, 'A5:M10005')
        for name in ('สรุปจ่ายรถร่วม', 'ปะหน้าจ่ายรถร่วม', 'สรุปหน้าเหมือง', 'รายการมาตรฐาน', 'oil',
                     views.EXPORT_DOC_RATE_SHEET):
            self.assertIsNone(wb[name].auto_filter.ref, name)

    def test_payer_file_keeps_real_weights(self):
        self.allocate()
        response = self.download(self.mine)
        self.assertEqual(response['Content-Type'],
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        self.assertEqual(wb['บันทึกรายเที่ยว']['F3'].value, 'ศิลาชัย')   # หัวปะหน้า / สรุปจ่าย ดึงจากช่องนี้
        cells = self.trip_cells(wb)
        self.assertEqual(set(cells), {'10', '30'})      # หิน 6 นิ้วค้าง stock ไม่อยู่ในไฟล์
        # น้ำหนักจริงทุกเที่ยว ไม่คูณสัดส่วน (เดิม 005062 กลายเป็น 0.00 / 0.22)
        self.assertEqual(cells['10'][:2], (44.38, 44.26))
        self.assertEqual(cells['30'][:2], (42.0, 41.5))
        self.assertIsNone(cells['10'][2])                         # ทั้งแถว = ไม่มีสัดส่วน
        self.assertAlmostEqual(cells['30'][2], 20 / 41.5)        # แบ่ง 20 จาก 41.5 ตัน

        # ชีตสรุปรวมจากคอลัมน์ช่วย AE / AF (= ค่าจริง × สัดส่วน) ของ template v22
        trip = wb['บันทึกรายเที่ยว']
        self.assertEqual(trip['AF6'].value, '=IF($M6="","",IF($AD6="",$M6,$M6*$AD6))')
        pay = wb['สรุปจ่ายรถร่วม']
        self.assertIn('บันทึกรายเที่ยว!$AF$6:$AF$10005', pay['AU5'].value)
        self.assertIn('บันทึกรายเที่ยว!$AE$6:$AE$10005', pay['AR5'].value)
        calc = wb['คำนวณค่าขนส่ง']
        self.assertIn('บันทึกรายเที่ยว!$AF$6:$AF$10005', calc['R5'].value)
        self.assertEqual(calc.max_column, views.EXPORT_DOC_FUEL_TABLE_FIRST_COL + 4)
        self.assertIn('oil', wb.sheetnames)
        self.assertEqual(pay.cell(row=views.EXPORT_DOC_PAY_FIRST_ROW, column=views.EXPORT_DOC_PAY_OIL_COL).value, 0)
        self.assertEqual(pay.cell(row=views.EXPORT_DOC_PAY_LAST_ROW, column=views.EXPORT_DOC_PAY_OIL_COL).value, 0)

    def test_other_payer_gets_its_split_only(self):
        self.allocate()
        wb = openpyxl.load_workbook(io.BytesIO(self.download(self.creative).content))
        cells = self.trip_cells(wb)
        self.assertEqual(set(cells), {'30'})
        self.assertEqual(cells['30'][:2], (42.0, 41.5))
        self.assertAlmostEqual(cells['30'][2], 21.5 / 41.5)
        self.assertEqual(wb['บันทึกรายเที่ยว']['F3'].value, 'ครีเอทีฟ')

    def test_payer_without_rows_has_no_file(self):
        self.allocate()
        response = self.download(BaseCompany.objects.get(code='STPS'))
        self.assertIn('ยังแบ่งไม่ครบเป้า', response.content.decode('utf-8'))

    def test_over_after_data_change_blocks_export(self):
        """บันทึกไว้แล้วข้อมูลชั่งเปลี่ยน จนตันที่แบ่งเกินยอดของแถว : ห้ามออกไฟล์จนกว่าจะแก้"""
        row = self.team_rows(self.plan())[(OTHER_PORT, STONE_2)]
        ExportDocumentPayerRowAllocation.objects.create(
            month=MONTH, row_key=row['key'], origin=row['origin'], destination=row['destination'],
            stone_type_name=row['stone'], team=row['team'], company=self.mine, tons=Decimal('50'))
        plan = self.plan()
        self.assertEqual(plan['over_rows'], 1)
        self.assertFalse(plan['can_export'])
        self.assertIn('เกินยอดจริง', self.download(self.mine).content.decode('utf-8'))

    def test_split_shares_add_up_to_row(self):
        self.allocate()
        plan_rows = views._exportDocumentPayerTeamRows(
            views._exportDocumentRows(Weight.objects.filter(weight_id__in=[10, 30, 31])
                                      .select_related('bws', 'bws__company')))
        allocs = list(ExportDocumentPayerRowAllocation.objects.filter(month=MONTH))
        mine = views._exportDocumentPayerShares(plan_rows, allocs, self.mine.id)
        creative = views._exportDocumentPayerShares(plan_rows, allocs, self.creative.id)
        split_key = next(k for k, v in creative.items())
        self.assertAlmostEqual(float(mine[split_key] + creative[split_key]), 1.0)
        self.assertEqual(len([v for v in mine.values() if v is None]), 1)   # แถวท่าเรือเรา ทั้งแถว

    def test_credit_from_contract_groups_and_files(self):
        """เครดิตของทีม = เงื่อนไขการชำระเงินในสัญญาของเส้นทางนั้น (แถวทุกทีม team = None ใช้กับทีมที่ไม่มีแถวของตัวเอง)
        ไฟล์ของนามแยกตามเครดิตได้ เครดิตน้อยก่อน ไม่ระบุท้ายสุด + ไฟล์รวม"""
        other = InternationalFreightRate.objects.get(destination__name=OTHER_PORT)
        InternationalFreightRateTeam.objects.create(international_freight_rate=other, team=None, credit_days=15)
        self.allocate()
        plan = self.plan()
        rows = self.team_rows(plan)
        self.assertEqual(rows[(OTHER_PORT, STONE_2)]['credit_label'], 'เครดิต 15 วัน')
        self.assertEqual(rows[(OWN_PORT, STONE_2)]['credit_label'], 'ไม่ระบุเครดิต')
        self.assertEqual([f['param'] for f in plan['filter_credits']], ['15', 'none'])
        mine = next(c for c in plan['companies'] if c['id'] == self.mine.id)
        self.assertEqual([(g['param'], g['tons']) for g in mine['credit_groups']],
                         [('15', Decimal('20.000')), ('none', Decimal('44.260'))])

        def docs(credit):
            response = self.client.get('/exportDocument/payer/excel/',
                                       {'month': '2026-08', 'company': self.mine.id, 'credit': credit})
            return response, set(self.trip_cells(openpyxl.load_workbook(io.BytesIO(response.content))))
        response, found = docs('15')
        self.assertEqual(found, {'30'})
        self.assertIn(quote('เครดิต15วัน'), response['Content-Disposition'])
        self.assertEqual(docs('none')[1], {'10'})
        self.assertEqual(set(self.trip_cells(openpyxl.load_workbook(
            io.BytesIO(self.download(self.mine).content)))), {'10', '30'})   # รวมทั้งหมด
        self.assertIn('ยังไม่ได้รับแถวทีมไหน', self.client.get(
            '/exportDocument/payer/excel/', {'month': '2026-08', 'company': self.mine.id, 'credit': '30'}
        ).content.decode('utf-8'))

    def test_mine_summary_sheet_reads_like_cover(self):
        """ชีตสรุปหน้าเหมืองแบบใบปะหน้า แทนชีต สรุปเหมือง เดิมของ template · รวมตามส่วนที่นามนี้รับ"""
        self.allocate()
        wb = openpyxl.load_workbook(io.BytesIO(self.download(self.mine).content))
        self.assertNotIn('สรุปเหมือง', wb.sheetnames)
        ws = wb['สรุปหน้าเหมือง']
        self.assertIn('ผู้อำนวยการฝ่ายผลิต', ws['A4'].value)
        labels = [ws.cell(row=r, column=1).value for r in range(7, 21)]
        self.assertEqual(labels[:4], ['ต้นทาง - ปลายทาง / สินค้า / ทีม',
                                      'ศิลาชัยสุราษฎร์-ท่าเรือบริษัทอื่น', STONE_2, 'ทีม A'])
        self.assertIn('ผลรวมทั้งหมด', labels)
        cond = ("'บันทึกรายเที่ยว'!$B$6:$B$10005,\"ศิลาชัยสุราษฎร์\","
                "'บันทึกรายเที่ยว'!$C$6:$C$10005,\"ท่าเรือบริษัทอื่น\","
                "'บันทึกรายเที่ยว'!$D$6:$D$10005,\"หิน 2 นิ้ว\","
                "'บันทึกรายเที่ยว'!$E$6:$E$10005,\"\"")
        self.assertEqual(ws.cell(row=9, column=2).value,
                         "=ROUND(SUMIFS('บันทึกรายเที่ยว'!$AE$6:$AE$10005,%s),0)" % cond)
        self.assertEqual(ws.cell(row=9, column=6).value,
                         "=SUMIFS('บันทึกรายเที่ยว'!$AF$6:$AF$10005,%s)" % cond)
        self.assertNotIn('"สรุปเหมือง"', wb['บันทึกรายเที่ยว']['A4'].value)
