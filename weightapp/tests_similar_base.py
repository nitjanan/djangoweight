# -*- coding: utf-8 -*-
"""เสนอรหัส/ชื่อที่คล้ายกันในหน้าเพิ่มข้อมูลพื้นฐาน (views_similar_base.py)"""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from weightapp import forms as base_forms
from weightapp.models import BaseCompany, BaseCustomer, BaseDriver, BaseJobType, BaseWeightType, SetPatternCode
from weightapp.views_similar_base import (SIMILAR_BASE_DETAILS, SIMILAR_BASE_MODELS, findSimilarBase,
                                          normalizeBaseName)


class NormalizeTests(TestCase):

    def test_strips_company_affixes_and_spaces(self):
        self.assertEqual(normalizeBaseName('บริษัท ศิลาชัย จำกัด'), 'ศิลาชัย')
        self.assertEqual(normalizeBaseName('บจก. ศิลาชัย'), 'ศิลาชัย')
        self.assertEqual(normalizeBaseName('หจก.ศิลา-ชัย'), 'ศิลาชัย')

    def test_keeps_name_made_only_of_affix(self):
        self.assertEqual(normalizeBaseName('บริษัท'), 'บริษัท')


class FindSimilarTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        for code, name in (('01-V-001', 'บริษัท ศิลาชัย จำกัด'), ('01-V-002', 'ผาทองทุ่งสง'),
                           ('01-V-003', 'สุราษฎร์พอร์ท'), ('01-V-004', None)):
            BaseCustomer.objects.create(customer_id=code, customer_name=name)

    def test_affix_variant_is_exact(self):
        results = findSimilarBase('BaseCustomer', 'บจก. ศิลาชัย')
        self.assertEqual(results[0]['id'], '01-V-001')
        self.assertTrue(results[0]['exact'])

    def test_partial_and_typo_match(self):
        self.assertEqual([r['id'] for r in findSimilarBase('BaseCustomer', 'ผาทอง')], ['01-V-002'])
        self.assertEqual([r['id'] for r in findSimilarBase('BaseCustomer', 'สุราษฏร์พอร์ต')], ['01-V-003'])

    def test_unrelated_and_too_short(self):
        self.assertEqual(findSimilarBase('BaseCustomer', 'เชียงใหม่คอนกรีต'), [])
        self.assertEqual(findSimilarBase('BaseCustomer', 'ศ'), [])


class SimilarDetailsTests(TestCase):
    """กล่องเสนอแสดงค่าช่องบังคับกรอกด้วย ให้แยกได้ว่าชื่อซ้ำแต่คนละประเภท/บริษัท"""

    def test_customer_shows_weight_type_and_job_type(self):
        sell = BaseWeightType.objects.create(id=1, name='ขาย')
        BaseJobType.objects.create(base_job_type_id='01', base_job_type_name='งานถนน')
        BaseCustomer.objects.create(customer_id='01-V-001', customer_name='ศิลาชัย', weight_type=sell,
                                    base_job_type_id='01')
        BaseCustomer.objects.create(customer_id='01RM', customer_name='ศิลาชัยผลิต')
        by_id = {r['id']: r['details'] for r in findSimilarBase('BaseCustomer', 'ศิลาชัย')}
        self.assertEqual(by_id['01-V-001'], [{'label': 'ชนิดเครื่องชั่ง', 'value': 'ขาย'},
                                             {'label': 'ประเภทงานของลูกค้า', 'value': '01 : งานถนน'}])
        self.assertEqual([d['value'] for d in by_id['01RM']], ['-', '-'])

    def test_company_shows_code_and_name(self):
        slc = BaseCompany.objects.create(code='SLC', name='ศิลาชัย', step=1)
        BaseDriver.objects.create(driver_id='D001', driver_name='สมชาย ใจดี', company=slc)
        results = findSimilarBase('BaseDriver', 'สมชาย')
        self.assertEqual(results[0]['details'], [{'label': 'บริษัท', 'value': 'SLC ศิลาชัย'}])

    def test_details_cover_every_required_form_field(self):
        """เพิ่มช่องบังคับในฟอร์มแล้วลืมเพิ่มใน SIMILAR_BASE_DETAILS -> เทสต์นี้ fail"""
        for model_key, (_, id_field, name_field, _, _) in SIMILAR_BASE_MODELS.items():
            form = getattr(base_forms, model_key + 'Form')()
            required = {k for k, f in form.fields.items() if f.required} - {id_field, name_field}
            shown = {f for f, _ in SIMILAR_BASE_DETAILS.get(model_key, [])}
            self.assertEqual(required - shown, set(), model_key)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SearchSimilarBaseViewTests(TestCase):

    def setUp(self):
        BaseDriver.objects.create(driver_id='D001', driver_name='สมชาย ใจดี')
        self.url = reverse('searchSimilarBase')

    def test_requires_login(self):
        res = self.client.get(self.url, {'model': 'BaseDriver', 'q': 'สมชาย'})
        self.assertEqual(res.status_code, 302)

    def test_returns_matches_and_rejects_unknown_model(self):
        self.client.force_login(User.objects.create_user('u1', 'u1@t.com', 'pw12345!'))
        res = self.client.get(self.url, {'model': 'BaseDriver', 'q': 'สมชาย'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([r['id'] for r in res.json()['results']], ['D001'])

        res = self.client.get(self.url, {'model': 'User', 'q': 'admin'})
        self.assertEqual(res.status_code, 400)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SimilarBaseDetailTests(TestCase):
    """popup "ดูข้อมูล" : อ่านอย่างเดียว แสดงทุกช่องของฟอร์ม (ยกเว้นช่องที่ซ่อน)"""

    def setUp(self):
        self.url = reverse('similarBaseDetail')
        sell = BaseWeightType.objects.create(id=1, name='ขาย')
        BaseJobType.objects.create(base_job_type_id='01', base_job_type_name='งานถนน')
        BaseCustomer.objects.create(customer_id='01-V-001', customer_name='ศิลาชัย', weight_type=sell,
                                    base_job_type_id='01', address='ทุ่งสง')

    def test_requires_login(self):
        self.assertEqual(self.client.get(self.url, {'model': 'BaseCustomer', 'id': '01-V-001'}).status_code, 302)

    def test_returns_form_fields_as_text(self):
        self.client.force_login(User.objects.create_user('u1', 'u1@t.com', 'pw12345!'))
        data = self.client.get(self.url, {'model': 'BaseCustomer', 'id': '01-V-001'}).json()
        fields = {f['label']: f['value'] for f in data['fields']}
        self.assertEqual(fields['ชนิดเครื่องชั่ง'], 'ขาย')
        self.assertEqual(fields['ประเภทงานของลูกค้า'], '01 : งานถนน')
        self.assertEqual(fields['ที่อยู่'], 'ทุ่งสง')
        self.assertEqual(fields['ส่งที่'], '-')
        self.assertNotIn('ชนิดvat', fields)  # ซ่อนในหน้าฟอร์ม จึงไม่แสดงใน popup
        self.assertEqual(data['usage'], [])
        self.assertEqual(data['view_url'], reverse('editBaseCustomer', args=['01-V-001']) + '?view=1')

    def test_unknown_model_and_missing_record(self):
        self.client.force_login(User.objects.create_user('u1', 'u1@t.com', 'pw12345!'))
        self.assertEqual(self.client.get(self.url, {'model': 'User', 'id': '1'}).status_code, 400)
        self.assertEqual(self.client.get(self.url, {'model': 'BaseCustomer', 'id': 'nope'}).status_code, 404)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SimilarOnEditPageTests(TestCase):
    """หน้าแก้ไขก็มีกล่องเสนอชื่อคล้าย แต่ไม่เสนอรายการที่กำลังแก้อยู่"""

    def setUp(self):
        BaseCustomer.objects.create(customer_id='01-V-001', customer_name='ศิลาชัย')
        BaseCustomer.objects.create(customer_id='01-V-002', customer_name='บจก. ศิลาชัย')

    def test_exclude_skips_record_being_edited(self):
        self.assertEqual(sorted(r['id'] for r in findSimilarBase('BaseCustomer', 'ศิลาชัย')), ['01-V-001', '01-V-002'])
        self.assertEqual([r['id'] for r in findSimilarBase('BaseCustomer', 'ศิลาชัย', exclude='01-V-001')], ['01-V-002'])

    def test_search_view_passes_exclude(self):
        self.client.force_login(User.objects.create_user('u1', 'u1@t.com', 'pw12345!'))
        res = self.client.get(reverse('searchSimilarBase'), {'model': 'BaseCustomer', 'q': 'ศิลาชัย', 'exclude': '01-V-002'})
        self.assertEqual([r['id'] for r in res.json()['results']], ['01-V-001'])

    def test_edit_page_includes_box_with_exclude(self):
        company = BaseCompany.objects.create(code='SLC', name='ศิลาชัย', step=1)
        user = User.objects.create_superuser('a', 'a@t.com', 'pw12345!')
        from weightapp.models import UserProfile
        UserProfile.objects.create(user=user).company.add(company)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'SLC'
        session.save()
        html = self.client.get(reverse('editBaseCustomer', args=['01-V-001'])).content.decode()
        self.assertIn('initSimilarBase(', html)
        from django.utils.html import escapejs
        self.assertIn("exclude: '%s'" % escapejs('01-V-001'), html)  # escapejs เขียน - เป็น \u002D


class NoExactDuplicateNameTests(TestCase):
    """ชื่อตรงกับข้อมูลที่มีอยู่ (หลังตัดคำนำหน้านิติบุคคล) -> บันทึกไม่ได้ ทั้งหน้าเพิ่มและหน้าแก้ไข"""

    def setUp(self):
        self.company = BaseCompany.objects.create(code='SLC', name='ศิลาชัย', step=1)
        SetPatternCode.objects.create(m_name='BaseDriver', pattern='D', end=1)  # ฟอร์มต้องมีรูปแบบรหัส
        BaseDriver.objects.create(driver_id='D1', driver_name='บริษัท สมชาย จำกัด', company=self.company)
        BaseDriver.objects.create(driver_id='D2', driver_name='สมศรี', company=self.company)

    def _form(self, name, instance=None, driver_id='9D'):
        data = {'driver_id': driver_id, 'driver_name': name, 'company': self.company.pk}
        return base_forms.BaseDriverForm(data, instance=instance)

    def test_create_blocks_exact_name(self):
        form = self._form('บจก. สมชาย')
        form.is_valid()
        self.assertIn('driver_name', form.errors)
        self.assertIn('D1', form.errors['driver_name'][0])

    def test_create_allows_similar_but_not_exact(self):
        form = self._form('สมชาย ใจดี')
        form.is_valid()
        self.assertNotIn('driver_name', form.errors)

    def test_edit_blocks_rename_to_existing(self):
        form = self._form('สมชาย', instance=BaseDriver.objects.get(pk='D2'), driver_id='D2')
        form.is_valid()
        self.assertIn('driver_name', form.errors)

    def test_edit_does_not_match_itself_or_block_unchanged_name(self):
        # ไม่เทียบกับตัวเอง
        form = self._form('บริษัท สมชาย จำกัด', instance=BaseDriver.objects.get(pk='D1'), driver_id='D1')
        form.is_valid()
        self.assertNotIn('driver_name', form.errors)
        # ข้อมูลเก่าที่ชื่อซ้ำกันอยู่แล้ว ถ้าไม่ได้เปลี่ยนชื่อ ยังบันทึกช่องอื่นได้
        # ชื่อในฐานข้อมูลห้ามซ้ำตรงตัว แต่ซ้ำได้หลังตัดคำนำหน้า (บจก.) เช่นข้อมูลเก่า
        BaseDriver.objects.create(driver_id='D3', driver_name='บจก. สมศรี', company=self.company)
        form = self._form('บจก. สมศรี', instance=BaseDriver.objects.get(pk='D3'), driver_id='D3')
        form.is_valid()
        self.assertNotIn('driver_name', form.errors)

    def test_every_similar_form_has_the_check(self):
        for model_key in SIMILAR_BASE_MODELS:
            form_class = getattr(base_forms, model_key + 'Form')
            self.assertTrue(issubclass(form_class, base_forms.NoExactDuplicateNameMixin), model_key)
            self.assertEqual(form_class.similar_model_key, model_key)


class SoundAlikeThaiTests(TestCase):
    """สะกดต่างแต่เสียงเดียวกัน (ส/ศ/ษ, ท/ธ ...) ต้องถูกเสนอ แต่ไม่นับเป็นชื่อตรงกัน (ไม่กันบันทึก)"""

    def setUp(self):
        self.company = BaseCompany.objects.create(code='SLC', name='ศิลาชัย', step=1)
        BaseDriver.objects.create(driver_id='D1', driver_name='บริษัท ศิลาชัย จำกัด', company=self.company)
        BaseDriver.objects.create(driver_id='D2', driver_name='ธนพล', company=self.company)

    def test_s_variants_are_suggested_but_not_exact(self):
        for query in ('สิลาชัย', 'ษิลาชัย', 'บจก. ซิลาชัย'):
            results = findSimilarBase('BaseDriver', query)
            self.assertEqual([r['id'] for r in results][:1], ['D1'], query)
            self.assertFalse(results[0]['exact'], query)
            self.assertTrue(results[0]['sound_alike'], query)
            self.assertGreaterEqual(results[0]['score'], 0.9, query)

    def test_th_variant(self):
        results = findSimilarBase('BaseDriver', 'ทนพล')
        self.assertEqual(results[0]['id'], 'D2')
        self.assertTrue(results[0]['sound_alike'])

    def test_exact_spelling_stays_exact(self):
        results = findSimilarBase('BaseDriver', 'ศิลาชัย')
        self.assertTrue(results[0]['exact'])
        self.assertFalse(results[0]['sound_alike'])

    def test_sound_alike_does_not_block_save(self):
        SetPatternCode.objects.create(m_name='BaseDriver', pattern='D', end=1)
        form = base_forms.BaseDriverForm({'driver_id': '9D', 'driver_name': 'สิลาชัย', 'company': self.company.pk})
        form.is_valid()
        self.assertNotIn('driver_name', form.errors)

    def test_final_consonant_by_sound(self):
        """ตัวสะกดท้ายคำออกเสียงตามมาตรา : สต็อก / สต็อค (แม่กก), ก๊าซ / ก๊าส (แม่กด)"""
        BaseDriver.objects.create(driver_id='D3', driver_name='กองสต็อก', company=self.company)
        BaseDriver.objects.create(driver_id='D4', driver_name='หจก. ก๊าซไทย', company=self.company)
        for query, expected in (('กองสต็อค', 'D3'), ('กองสตอค', 'D3'), ('ก๊าส ไทย', 'D4')):
            results = findSimilarBase('BaseDriver', query)
            self.assertEqual(results[0]['id'], expected, query)
            self.assertTrue(results[0]['sound_alike'], query)
            self.assertFalse(results[0]['exact'], query)

    def test_initial_k_kh_are_still_different(self):
        """ต้นคำ ก / ค เป็นคนละเสียง (กาง / คาง) ไม่นับว่าเสียงเดียวกัน"""
        BaseDriver.objects.create(driver_id='D5', driver_name='กาง', company=self.company)
        results = findSimilarBase('BaseDriver', 'คาง')
        self.assertFalse(any(r['sound_alike'] and r['id'] == 'D5' and r['score'] >= 0.95 for r in results))
