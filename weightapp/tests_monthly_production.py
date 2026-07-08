import re
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from weightapp.models import (
    BaseCompany, BaseSite, BaseStoneType, UserProfile,
    StoneEstimate, StoneEstimateItem, Production,
)


def add_estimate(company, site, created, stone, total):
    se = StoneEstimate.objects.create(created=created, site=site, company=company)
    return StoneEstimateItem.objects.create(
        se=se, stone_type=stone, percent=Decimal('10.0000'), total=Decimal(total),
    )


#ปิด whitenoise manifest ใน test เพราะไม่ได้รัน collectstatic
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class MonthlyProductionAlignmentTests(TestCase):
    """ทุกแถวในตารางต้องมีจำนวนคอลัมน์เท่ากัน แม้ปีเก่าไม่มีข้อมูลของหิน/โรงโม่นั้น"""
    # โครงคอลัมน์: ลำดับ, ชื่อ, รวมปีเก่า, เฉลี่ยปีเก่า, เดือน ม.ค.-มี.ค., รวม, เฉลี่ย
    EXPECTED_CELLS = 9

    def setUp(self):
        self.client = Client()
        self.company = BaseCompany.objects.create(name="Test Company", code="TEST_COMP")
        self.site = BaseSite.objects.create(
            base_site_id="S01", base_site_name="โรงโม่หนึ่ง", s_comp=self.company)
        self.stone_old = BaseStoneType.objects.create(
            base_stone_type_id="01ST", base_stone_type_name="หิน 3/4")
        self.stone_new = BaseStoneType.objects.create(
            base_stone_type_id="09ST", base_stone_type_name="หินใหญ่ขนาด 30-80 มม.")
        self.user = User.objects.create_user('tester', 't@t.com', 'pw12345!')
        profile = UserProfile.objects.create(user=self.user)
        profile.company.add(self.company)
        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'TEST_COMP'
        session['company'] = 'Test Company'
        session['db_start_date'] = '2026-01-01'
        session['db_end_date'] = '2026-03-15'
        session.save()

    def row_cell_counts(self, html, label):
        """จำนวน cell ของทุก <tr> ที่มีข้อความ label (มีทั้งใน tbody โรงโม่และ Total)"""
        rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.S)
        counts = [len(re.findall(r'<t[dh][\s>]', row)) for row in rows if label in row]
        self.assertTrue(counts, 'ไม่พบแถว ' + label)
        return counts

    def get_html(self):
        response = self.client.get(reverse('monthlyProduction'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        #แท็ก {{ ... }} ที่โดน formatter ตัดขึ้นบรรทัดใหม่ Django จะไม่ render และหลุดออกมาเป็นข้อความดิบ
        self.assertNotIn('{{', html, 'มี template tag ไม่ถูก render (แท็กโดนตัดบรรทัด?)')
        return html

    def test_stone_row_without_old_year_data_keeps_column_count(self):
        #หิน 3/4 มีข้อมูลทั้งปี 2025 และ 2026 แต่หินใหญ่ฯ มีเฉพาะ 2026
        add_estimate(self.company, self.site, '2025-05-15', self.stone_old, '100.000')
        add_estimate(self.company, self.site, '2026-01-15', self.stone_old, '10.000')
        add_estimate(self.company, self.site, '2026-01-15', self.stone_new, '20.000')

        html = self.get_html()

        for count in self.row_cell_counts(html, 'หิน 3/4'):
            self.assertEqual(count, self.EXPECTED_CELLS, 'แถวหินที่มีข้อมูลปีเก่าเพี้ยน')
        for count in self.row_cell_counts(html, 'หินใหญ่ขนาด 30-80 มม.'):
            self.assertEqual(count, self.EXPECTED_CELLS, 'แถวหินที่ไม่มีข้อมูลปีเก่าต้องไม่เลื่อนคอลัมน์')

    def test_production_rows_for_site_without_old_year_keep_column_count(self):
        #ปีเก่ามี production เฉพาะโรงโม่หนึ่ง ส่วนโรงโม่สองเพิ่งเปิดปี 2026
        site2 = BaseSite.objects.create(
            base_site_id="S02", base_site_name="โรงโม่สอง", s_comp=self.company)
        #Production.save() คำนวณ run_time/actual_time จากเวลาเริ่ม-สิ้นสุดเสมอ
        Production.objects.create(
            company=self.company, site=self.site, created='2025-05-15',
            run_start_time=timedelta(hours=8), run_end_time=timedelta(hours=16),
            actual_start_time=timedelta(hours=8), actual_end_time=timedelta(hours=18),
            total_loss_time=timedelta(hours=1), capacity_per_hour=Decimal('100.00'))
        add_estimate(self.company, self.site, '2026-01-15', self.stone_old, '10.000')
        add_estimate(self.company, site2, '2026-01-15', self.stone_old, '20.000')

        html = self.get_html()

        for label in ('ชม.โม่', 'กำลังการผลิต', 'วันทำงาน', 'ชม.ต่อวัน'):
            counts = self.row_cell_counts(html, label)
            self.assertEqual(len(counts), 2, 'ต้องมีแถว ' + label + ' ของทั้งสองโรงโม่')
            for count in counts:
                self.assertEqual(count, self.EXPECTED_CELLS,
                                 'แถว ' + label + ' ของโรงโม่ที่ไม่มีข้อมูลปีเก่าต้องไม่เลื่อนคอลัมน์')
