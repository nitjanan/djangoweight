# -*- coding: utf-8 -*-
"""โหมดดูข้อมูลอย่างเดียวของหน้าแก้ไขข้อมูลพื้นฐาน (?view=1)  ดู weightapp/base_view_mode.py"""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from weightapp.models import BaseCompany, BaseDriver, BaseMill, BaseWeightType, SetPatternCode, UserProfile


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class BaseViewModeTests(TestCase):

    def setUp(self):
        self.company = BaseCompany.objects.create(code='SLC', name='ศิลาชัย', step=1)
        user = User.objects.create_superuser('a', 'a@t.com', 'pw12345!')
        UserProfile.objects.create(user=user).company.add(self.company)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'SLC'
        session.save()
        sell = BaseWeightType.objects.create(id=1, name='ขาย')
        SetPatternCode.objects.create(m_name='BaseMill', pattern='M', end=3)  # ฟอร์มต้นทางต้องมีรูปแบบรหัส
        BaseMill.objects.create(mill_id='001M', mill_name='โรงโม่ ก', weight_type=sell)
        self.url = reverse('editBaseMill', args=['001M'])

    def test_view_mode_is_read_only(self):
        html = self.client.get(self.url, {'view': '1'}).content.decode()
        self.assertIn('ดูข้อมูลต้นทาง', html)
        self.assertIn('<fieldset class="bf-fieldset" disabled>', html)
        self.assertNotIn('bf-save-btn', html)

    def test_normal_edit_still_saves(self):
        html = self.client.get(self.url).content.decode()
        self.assertIn('bf-save-btn', html)
        self.assertNotIn('<fieldset class="bf-fieldset" disabled>', html)
        # POST ปกติ (ไม่มี ?view=1) ต้องผ่านด่านไปถึงฟอร์ม ไม่ถูกปฏิเสธ
        res = self.client.post(self.url, {'mill_id': '001M', 'mill_name': 'โรงโม่ ข', 'weight_type': 1})
        self.assertNotEqual(res.status_code, 403)

    def test_post_in_view_mode_is_rejected(self):
        res = self.client.post(self.url + '?view=1', {'mill_id': '001M', 'mill_name': 'แก้แอบ', 'weight_type': 1})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(BaseMill.objects.get(pk='001M').mill_name, 'โรงโม่ ก')

    def test_every_edit_view_rejects_post_in_view_mode(self):
        BaseDriver.objects.create(driver_id='D1', driver_name='สมชาย', company=self.company)
        res = self.client.post(reverse('editBaseDriver', args=['D1']) + '?view=1',
                               {'driver_id': 'D1', 'driver_name': 'แก้แอบ', 'company': self.company.pk})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(BaseDriver.objects.get(pk='D1').driver_name, 'สมชาย')
