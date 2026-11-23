# -*- coding: utf-8 -*-
"""หน้าแก้ไขข้อมูลพื้นฐาน : บริษัทที่ใช้ข้อมูลนี้ในตาราง weight (views_base_usage.py)"""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from weightapp.models import (BaseCompany, BaseCustomer, BaseCustomerSite, BaseDriver, BaseJobType, BaseSite,
                              BaseWeightStation, UserProfile, Weight)
from weightapp.views_base_usage import weightUsageByCompany


class WeightUsageTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.slc = BaseCompany.objects.create(name='ศิลาชัย', code='SLC', step=1)
        cls.cks = BaseCompany.objects.create(name='ชัยกิจ', code='CKS', step=2)
        BaseWeightStation.objects.create(id='S1', company=cls.slc)
        BaseWeightStation.objects.create(id='S2', company=cls.slc)
        BaseWeightStation.objects.create(id='C1', company=cls.cks)
        BaseWeightStation.objects.create(id='X1')  # ตาชั่งที่ไม่ได้ผูกบริษัท
        cls.job = BaseJobType.objects.create(base_job_type_id='01', base_job_type_name='งานถนน')
        BaseCustomer.objects.create(customer_id='01-V-001', customer_name='ลูกค้า ก', base_job_type=cls.job)
        BaseCustomer.objects.create(customer_id='01-V-002', customer_name='ลูกค้า ข')
        BaseSite.objects.create(base_site_id='P01', base_site_name='หน้างาน 1')
        BaseDriver.objects.create(driver_id='D001', driver_name='คนขับไม่เคยชั่ง')

        rows = [(1, 'S1', '01-V-001', 'P01', date(2026, 10, 1)),
                (2, 'S2', '01-V-001', None, date(2026, 10, 5)),
                (3, 'C1', '01-V-001', 'P01', date(2026, 9, 1)),
                (4, 'X1', '01-V-001', None, date(2026, 8, 1)),
                (5, 'C1', '01-V-002', 'P01', date(2026, 11, 1))]
        for wid, bws, customer, site, day in rows:
            Weight.objects.create(weight_id=wid, bws_id=bws, customer_id=customer, site_id=site, date=day)

    def test_groups_by_company_in_tab_order(self):
        usage = weightUsageByCompany('BaseCustomer', '01-V-001')
        self.assertEqual([(u['code'], u['count'], u['last_date']) for u in usage],
                         [('SLC', 2, date(2026, 10, 5)), ('CKS', 1, date(2026, 9, 1)), (None, 1, date(2026, 8, 1))])
        self.assertEqual(usage[-1]['name'], 'ไม่ระบุบริษัท')

    def test_job_type_goes_through_customer(self):
        usage = weightUsageByCompany('BaseJobType', '01')
        self.assertEqual(sum(u['count'] for u in usage), 4)

    def test_customer_site_matches_pair(self):
        pair = BaseCustomerSite.objects.create(customer_id='01-V-001', site_id='P01')
        usage = weightUsageByCompany('BaseCustomerSite', pair.pk)
        self.assertEqual([(u['code'], u['count']) for u in usage], [('SLC', 1), ('CKS', 1)])

    def test_unused(self):
        self.assertEqual(weightUsageByCompany('BaseDriver', 'D001'), [])


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class EditPageShowsUsageTests(TestCase):

    def setUp(self):
        company = BaseCompany.objects.create(name='ศิลาชัย', code='SLC', step=1)
        BaseWeightStation.objects.create(id='S1', company=company)
        BaseDriver.objects.create(driver_id='D001', driver_name='สมชาย')
        BaseDriver.objects.create(driver_id='D002', driver_name='สมศรี')
        Weight.objects.create(weight_id=1, bws_id='S1', driver_id='D001', date=date(2026, 10, 1))

        user = User.objects.create_superuser('admin1', 'a@t.com', 'pw12345!')
        UserProfile.objects.create(user=user).company.add(company)
        self.client.force_login(user)
        session = self.client.session
        session['company_code'] = 'SLC'
        session.save()

    def test_edit_page_lists_company(self):
        html = self.client.get(reverse('editBaseDriver', args=['D001'])).content.decode()
        self.assertIn('ข้อมูลนี้ถูกใช้ในตาชั่งแล้ว 1 บริษัท', html)
        self.assertIn('ศิลาชัย', html)

    def test_edit_page_unused(self):
        html = self.client.get(reverse('editBaseDriver', args=['D002'])).content.decode()
        self.assertIn('ยังไม่มีบริษัทใดใช้ข้อมูลนี้ในตาชั่ง', html)

    def test_create_page_has_no_usage_box(self):
        html = self.client.get(reverse('createBaseDriver')).content.decode()
        self.assertNotIn('wu-box', html)
