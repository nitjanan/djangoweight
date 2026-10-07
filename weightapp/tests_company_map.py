# -*- coding: utf-8 -*-
"""หน้า จัดการต้นทาง / ปลายทาง (views_company_map.py)

CRUD ตาราง base_company_map_base_customer + รหัสลูกค้าสำรอง เข้าได้เฉพาะคนที่มีสิทธิ์แก้ตาราง map
"""
from django.contrib.auth.models import Permission, User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from weightapp.models import (EXPORT_DOC_OWN_PORT_CUSTOMERS_CACHE_KEY, BaseCompany,
                              BaseCompanyMapBaseCustomer, BaseCompanyMapCustomerAlias, BaseCustomer,
                              InternationalFreightRate, UserProfile)


# ปิด whitenoise manifest ใน test เพราะไม่ได้รัน collectstatic
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CompanyMapPageTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.company = BaseCompany.objects.create(name='ศิลาชัย', code='SLC')
        for code, name in (('06-V-024', 'สุราษฎร์พอร์ท'), ('77-V-007', 'สุราษฎร์พอร์ท (รหัสเหมือง)'),
                           ('77-V-009', 'พี.ซี.ปิโตรเลียม'), ('13-V-105', 'ผาทองทุ่งสง')):
            BaseCustomer.objects.create(customer_id=code, customer_name=name)
        cls.surat = BaseCompanyMapBaseCustomer.objects.create(
            name='สุราษฎร์พอร์ท', base_customer_id='06-V-024', is_export_destination=True)
        BaseCompanyMapCustomerAlias.objects.create(map_row=cls.surat, base_customer_id='77-V-007')
        cls.mine = BaseCompanyMapBaseCustomer.objects.create(name='ศิลาชัย', base_company=cls.company)

    def setUp(self):
        self.user = self.makeUser('editor', perms=('change_basecompanymapbasecustomer',
                                                   'delete_basecompanymapbasecustomer'))
        self.login(self.user)

    def makeUser(self, username, perms=()):
        user = User.objects.create_user(username, username + '@t.com', 'pw12345!')
        profile = UserProfile.objects.create(user=user)
        profile.company.add(self.company)
        for codename in perms:
            user.user_permissions.add(Permission.objects.get(codename=codename))
        return user

    def login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'SLC'
        session['company'] = 'ศิลาชัย'
        session.save()

    def postForm(self, row=None, data=None, aliases=(), existing=()):
        """ส่งฟอร์มเพิ่ม/แก้ไข aliases = รหัสสำรองใหม่ · existing = [(alias, ลบไหม)]"""
        payload = {'name': 'แถวทดสอบ', 'base_company': '', 'base_customer': '', 'oi_soc_code': ''}
        payload.update(data or {})
        forms = [(alias.pk, alias.base_customer_id, delete) for alias, delete in existing]
        forms += [('', code, False) for code in aliases]
        payload.update({'alias-TOTAL_FORMS': str(len(forms)),
                        'alias-INITIAL_FORMS': str(len(existing)),
                        'alias-MIN_NUM_FORMS': '0', 'alias-MAX_NUM_FORMS': '1000'})
        for i, (alias_id, code, delete) in enumerate(forms):
            payload['alias-%d-id' % i] = alias_id
            payload['alias-%d-base_customer' % i] = code
            if delete:
                payload['alias-%d-DELETE' % i] = 'on'
        url = reverse('editCompanyMap', args=[row.id]) if row else reverse('createCompanyMap')
        return self.client.post(url, payload)

    def errorsOf(self, response):
        context = response.context
        errors = dict(context['form'].errors)
        errors['__formset__'] = list(context['formset'].non_form_errors())
        errors['__alias__'] = [e for f in context['formset'].forms for e in f.errors.get('base_customer', [])]
        return errors

    # ---------- สิทธิ์ ----------

    def test_list_needs_permission(self):
        self.login(self.makeUser('viewer'))
        self.assertEqual(self.client.get(reverse('settingCompanyMap')).status_code, 403)
        self.assertEqual(self.client.get(reverse('createCompanyMap')).status_code, 403)
        self.assertEqual(self.client.get(reverse('companyMapCustomerSearch')).status_code, 403)

    def test_delete_needs_delete_permission(self):
        self.login(self.makeUser('changer', perms=('change_basecompanymapbasecustomer',)))
        self.assertEqual(self.client.get(reverse('settingCompanyMap')).status_code, 200)
        self.assertEqual(self.client.post(reverse('deleteCompanyMap', args=[self.mine.id])).status_code, 403)
        self.assertTrue(BaseCompanyMapBaseCustomer.objects.filter(id=self.mine.id).exists())

    def test_freight_rate_page_shows_button_only_with_permission(self):
        url = reverse('viewInternationalFreightRate')
        self.assertContains(self.client.get(url), reverse('settingCompanyMap'))
        self.login(self.makeUser('viewer'))
        self.assertNotContains(self.client.get(url), reverse('settingCompanyMap'))

    # ---------- หน้ารายการ ----------

    def test_list_shows_rows_aliases_and_incomplete_flag(self):
        broken = BaseCompanyMapBaseCustomer.objects.create(name='ติ๊กแต่ไม่มีรหัส',
                                                          base_company=self.company,
                                                          is_export_destination=True)
        response = self.client.get(reverse('settingCompanyMap'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '77-V-007')
        self.assertContains(response, 'ไม่มีรหัสลูกค้า เที่ยวจะไม่เข้า')
        rows = {row.id: row for row in response.context['rows']}
        self.assertTrue(rows[broken.id].is_incomplete)
        self.assertFalse(rows[self.surat.id].is_incomplete)

    def test_list_search_finds_alias_code(self):
        response = self.client.get(reverse('settingCompanyMap'), {'q': '77-V-007'})
        self.assertEqual([row.id for row in response.context['rows']], [self.surat.id])

    def test_list_filter_incomplete(self):
        broken = BaseCompanyMapBaseCustomer.objects.create(name='ติ๊กแต่ไม่มีรหัส',
                                                          base_company=self.company,
                                                          is_export_destination=True)
        response = self.client.get(reverse('settingCompanyMap'), {'kind': 'incomplete'})
        self.assertEqual([row.id for row in response.context['rows']], [broken.id])

    # ---------- เพิ่ม / แก้ไข ----------

    def test_create_row_with_aliases(self):
        response = self.postForm(data={'name': 'พี.ซี.ปิโตรเลียม', 'base_customer': '77-V-009',
                                       'is_export_destination': 'on'}, aliases=['13-V-105'])
        self.assertRedirects(response, reverse('settingCompanyMap'))
        row = BaseCompanyMapBaseCustomer.objects.get(name='พี.ซี.ปิโตรเลียม')
        self.assertEqual(row.base_customer_id, '77-V-009')
        self.assertTrue(row.is_export_destination)
        self.assertEqual(list(row.customer_aliases.values_list('base_customer_id', flat=True)), ['13-V-105'])

    def test_edit_removes_and_adds_alias(self):
        alias = self.surat.customer_aliases.get()
        response = self.postForm(row=self.surat,
                                 data={'name': 'สุราษฎร์พอร์ท', 'base_customer': '06-V-024',
                                       'is_export_destination': 'on'},
                                 existing=[(alias, True)], aliases=['77-V-009'])
        self.assertRedirects(response, reverse('settingCompanyMap'))
        self.assertEqual(list(self.surat.customer_aliases.values_list('base_customer_id', flat=True)),
                         ['77-V-009'])

    def test_save_clears_own_port_cache(self):
        cache.set(EXPORT_DOC_OWN_PORT_CUSTOMERS_CACHE_KEY, {'x': None})
        self.postForm(row=self.mine, data={'name': 'ศิลาชัย', 'base_company': self.company.id})
        self.assertIsNone(cache.get(EXPORT_DOC_OWN_PORT_CUSTOMERS_CACHE_KEY))

    # ---------- กติกา ----------

    def test_row_needs_company_or_customer(self):
        response = self.postForm(data={'name': 'ว่างเปล่า'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('ต้องเลือกบริษัทหรือรหัสลูกค้าอย่างน้อย 1 อย่าง', self.errorsOf(response)['__all__'])
        self.assertFalse(BaseCompanyMapBaseCustomer.objects.filter(name='ว่างเปล่า').exists())

    def test_flagged_destination_needs_customer(self):
        """กันแถวแบบ 22-26 บน deploy : ติ๊กปลายทางแต่ไม่มีรหัส เที่ยวไม่เข้าเลย"""
        response = self.postForm(data={'name': 'ติ๊กแต่ไม่มีรหัส', 'base_company': self.company.id,
                                       'is_export_destination': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('ติ๊กใช้เป็นปลายทางแล้ว ต้องเลือกรหัสลูกค้าด้วย',
                      self.errorsOf(response)['base_customer'])

    def test_primary_code_cannot_repeat_even_without_company(self):
        """unique_together (บริษัท, ลูกค้า) ของตารางกันไม่ได้ตอนบริษัทว่าง ต้องกันในฟอร์ม"""
        response = self.postForm(data={'name': 'ซ้ำ', 'base_customer': '06-V-024'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('รหัสนี้เป็นรหัสหลักของ "สุราษฎร์พอร์ท" อยู่แล้ว',
                      self.errorsOf(response)['base_customer'])

    def test_primary_code_cannot_be_another_rows_alias(self):
        response = self.postForm(data={'name': 'ซ้ำ', 'base_customer': '77-V-007'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('รหัสนี้เป็นรหัสลูกค้าสำรองของ "สุราษฎร์พอร์ท" อยู่แล้ว',
                      self.errorsOf(response)['base_customer'])

    def test_alias_cannot_be_a_primary_code(self):
        response = self.postForm(data={'name': 'ใหม่', 'base_customer': '77-V-009'}, aliases=['06-V-024'])
        self.assertEqual(response.status_code, 200)
        self.assertIn('รหัสนี้เป็นรหัสลูกค้าหลักของ "สุราษฎร์พอร์ท" อยู่แล้ว', self.errorsOf(response)['__alias__'])

    def test_alias_cannot_belong_to_two_rows(self):
        response = self.postForm(data={'name': 'ใหม่', 'base_customer': '77-V-009'}, aliases=['77-V-007'])
        self.assertEqual(response.status_code, 200)
        self.assertIn('รหัสนี้เป็นรหัสลูกค้าสำรองของ "สุราษฎร์พอร์ท" อยู่แล้ว', self.errorsOf(response)['__alias__'])

    def test_alias_repeated_in_same_form(self):
        response = self.postForm(data={'name': 'ใหม่', 'base_customer': '77-V-009'},
                                 aliases=['13-V-105', '13-V-105'])
        self.assertEqual(response.status_code, 200)
        self.assertIn('รหัสสำรอง 13-V-105 ใส่ซ้ำกัน', self.errorsOf(response)['__formset__'])

    def test_alias_same_as_own_primary(self):
        response = self.postForm(data={'name': 'ใหม่', 'base_customer': '77-V-009'}, aliases=['77-V-009'])
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('อยู่ในรายการรหัสสำรองของแถวนี้ด้วย' in e
                            for e in self.errorsOf(response)['base_customer']))
        self.assertFalse(BaseCompanyMapBaseCustomer.objects.filter(name='ใหม่').exists())

    # ---------- ลบ ----------

    def test_delete_row_and_its_aliases(self):
        response = self.client.post(reverse('deleteCompanyMap', args=[self.surat.id]))
        self.assertRedirects(response, reverse('settingCompanyMap'))
        self.assertFalse(BaseCompanyMapBaseCustomer.objects.filter(id=self.surat.id).exists())
        self.assertFalse(BaseCompanyMapCustomerAlias.objects.filter(base_customer_id='77-V-007').exists())

    def test_delete_blocked_when_freight_rate_uses_row(self):
        InternationalFreightRate.objects.create(origin=self.mine, destination=self.surat)
        page = self.client.get(reverse('deleteCompanyMap', args=[self.surat.id]))
        self.assertContains(page, 'ลบไม่ได้')
        self.assertNotContains(page, 'ยืนยันลบ')
        self.client.post(reverse('deleteCompanyMap', args=[self.surat.id]))
        self.assertTrue(BaseCompanyMapBaseCustomer.objects.filter(id=self.surat.id).exists())

    # ---------- ค้นลูกค้า ----------

    def test_customer_search_marks_codes_in_use(self):
        response = self.client.get(reverse('companyMapCustomerSearch'), {'term': '77-V'})
        results = {r['id']: r['text'] for r in response.json()['results']}
        self.assertEqual(set(results), {'77-V-007', '77-V-009'})
        self.assertIn('ใช้อยู่ที่ "สุราษฎร์พอร์ท"', results['77-V-007'])
        self.assertNotIn('ใช้อยู่ที่', results['77-V-009'])

    def test_customer_search_pages_through_all_customers(self):
        """ไม่หยุดที่ 30 รายแรก : เลื่อนลงแล้วต้องขอหน้าถัดไปได้จนครบ"""
        for i in range(70):
            BaseCustomer.objects.create(customer_id='99-V-%03d' % i, customer_name='ลูกค้าทดสอบ %d' % i)
        url = reverse('companyMapCustomerSearch')
        seen = []
        for page in (1, 2, 3):
            data = self.client.get(url, {'term': '99-V', 'page': page}).json()
            seen += [r['id'] for r in data['results']]
            self.assertEqual(data['pagination']['more'], page < 3, page)
        self.assertEqual(len(seen), 70)
        self.assertEqual(len(set(seen)), 70)
        self.assertEqual(seen[:2], ['99-V-000', '99-V-001'])
