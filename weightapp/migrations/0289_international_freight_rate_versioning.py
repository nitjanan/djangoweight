# -*- coding: utf-8 -*-
"""ทำระบบเวอร์ชันให้อัตราค่าขนส่งไปนอกประเทศ

แนวคิด : แก้ราคาแล้วไม่ทับของเดิม แต่ออกใบใหม่ทั้งใบ ใบเก่าอยู่ครบ
เอกสารเดือนเก่าจึงได้ตัวเลขเดิมเสมอ

จุดที่ต้องระวังตอน backfill : แถวอัตราที่มีอยู่ถูกสร้างปี 2026 แต่ข้อมูลการชั่ง
มีย้อนหลังหลายปี ถ้าตั้ง effective_month = เดือนที่สร้าง export เดือนเก่าจะหา
อัตราไม่เจอแล้วเที่ยวหายทั้งเส้นทาง จึงต้องตั้งเป็น 2000-01-01 (ตั้งแต่ต้น)
"""
import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_versions(apps, schema_editor):
    """แถวที่มีอยู่ทุกแถวกลายเป็นเวอร์ชัน 1 ของตัวเอง อนุมัติแล้ว มีผลตั้งแต่ต้น"""
    Rate = apps.get_model('weightapp', 'InternationalFreightRate')
    Rate.objects.update(
        version=1,
        status='approved',
        effective_month=datetime.date(2000, 1, 1),
    )
    # root ชี้ตัวเอง ต้องไล่ทีละแถวเพราะ MySQL อัปเดตคอลัมน์จาก id ของตัวเองใน UPDATE เดียวไม่ได้
    for rate_id in Rate.objects.values_list('id', flat=True):
        Rate.objects.filter(id=rate_id).update(root_id=rate_id)


def unbackfill_versions(apps, schema_editor):
    """ย้อนกลับ : ไม่มีอะไรต้องคืน เพราะคอลัมน์ทั้งชุดจะถูกลบอยู่แล้ว"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('weightapp', '0284_fuel_price_allow_multiple_per_month'),
    ]

    operations = [
        # --- 1. ราคาน้ำมันย้ายไปผูกกับ "เส้นทาง" (แถว root) แทนเวอร์ชันใดเวอร์ชันหนึ่ง ---
        # ใช้ RenameField ไม่ใช่ลบแล้วเพิ่มใหม่ ข้อมูล 14 แถวจึงอยู่ครบ
        # ตอนนี้ทุกแถวอัตราเป็น root ของตัวเอง ค่าที่ชี้อยู่จึงถูกต้องอยู่แล้ว ไม่ต้องแปลงข้อมูล
        migrations.RemoveIndex(
            model_name='internationalfreightratefuelprice',
            name='ifr_fuel_rate_month_idx',
        ),
        migrations.RenameField(
            model_name='internationalfreightratefuelprice',
            old_name='international_freight_rate',
            new_name='root',
        ),
        migrations.AlterField(
            model_name='internationalfreightratefuelprice',
            name='root',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='fuel_prices', to='weightapp.internationalfreightrate',
                verbose_name='เส้นทาง (ใบแรกสุด)'),
        ),
        migrations.AddIndex(
            model_name='internationalfreightratefuelprice',
            index=models.Index(fields=['root', '-month', '-id'], name='ifr_fuel_rate_month_idx'),
        ),

        # --- 2. คอลัมน์เวอร์ชัน + สถานะอนุมัติ ---
        migrations.AddField(
            model_name='internationalfreightrate',
            name='root',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='versions', to='weightapp.internationalfreightrate',
                verbose_name='เส้นทาง (ใบแรกสุด)'),
        ),
        migrations.AddField(
            model_name='internationalfreightrate',
            name='version',
            field=models.IntegerField(default=1, verbose_name='เวอร์ชัน'),
        ),
        migrations.AddField(
            model_name='internationalfreightrate',
            name='effective_month',
            field=models.DateField(blank=True, null=True, verbose_name='เริ่มใช้เดือน'),
        ),
        migrations.AddField(
            model_name='internationalfreightrate',
            name='status',
            field=models.CharField(
                choices=[('draft', 'ร่าง'), ('pending', 'รออนุมัติ'),
                         ('approved', 'อนุมัติแล้ว'), ('rejected', 'ไม่อนุมัติ')],
                default='approved', max_length=20, verbose_name='สถานะ'),
        ),
        migrations.AddField(
            model_name='internationalfreightrate',
            name='user_created',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='international_freight_rates_created',
                to=settings.AUTH_USER_MODEL, verbose_name='ผู้ออกใบ'),
        ),

        migrations.RunPython(backfill_versions, unbackfill_versions),

        migrations.AlterUniqueTogether(
            name='internationalfreightrate',
            unique_together={('root', 'version')},
        ),
        migrations.AddIndex(
            model_name='internationalfreightrate',
            index=models.Index(fields=['root', 'status', '-effective_month', '-id'],
                               name='ifr_root_status_month_idx'),
        ),

        # --- 3. ทิ้งตารางประวัติเดิมที่ไม่เคยมีใครใช้ (0 แถว ฟิลด์ล้าสมัยไปแล้ว) ---
        migrations.DeleteModel(name='InternationalFreightRateLog'),
    ]
