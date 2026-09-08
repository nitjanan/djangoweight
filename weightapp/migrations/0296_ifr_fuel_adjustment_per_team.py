# -*- coding: utf-8 -*-
"""ย้าย "ปรับค่าขนส่งตามน้ำมัน (ลิตรละ 1 บาท)" จากตัวใบ ลงไปเป็นรายแถวทีม

เดิมเก็บค่าเดียวทั้งใบ (international_freight_rate.fuel_freight_adjustment) ซึ่งกรอกค่าจริง
ไม่ได้ เพราะอัตราปรับตามน้ำมันต่อรองกันรายทีม และทีมเดียวกันคนละช่วงแบก นน. ก็คนละอัตรา
คอลัมน์ใหม่จึงอยู่ระดับเดียวกับ freight_rate คือ 1 แถว = (ใบ, ทีม, ช่วงแบก นน.)

migration นี้ทำแค่ "เพิ่มคอลัมน์ + คัดลอกค่าลงมา" ยังไม่ลบคอลัมน์เก่า
ส่วนการลบอยู่ใน 0297 แยกไฟล์เพื่อให้ deploy ได้ 2 จังหวะ (รัน 0296 -> ขึ้นโค้ดใหม่ -> รัน 0297)
จะได้ไม่มีช่วงที่ schema กับโค้ดไม่ตรงกัน
"""
from django.db import migrations, models


def copyAdjustmentDownToTeams(apps, schema_editor):
    """คัดค่าจากใบ ลงทุกแถวทีมของใบนั้น — ทุกแถวได้ค่าเท่ากันหมด ตรงกับพฤติกรรมเดิม

    วนทีละใบแล้ว update ทีเดียวต่อใบ ไม่ใช้ F() ข้ามความสัมพันธ์
    เพราะ UPDATE ... JOIN แบบนั้น Django ไม่รองรับ (FieldError)
    """
    InternationalFreightRate = apps.get_model('weightapp', 'InternationalFreightRate')
    InternationalFreightRateTeam = apps.get_model('weightapp', 'InternationalFreightRateTeam')
    for rate_id, adjustment in (InternationalFreightRate.objects
                                .exclude(fuel_freight_adjustment=None)
                                .values_list('id', 'fuel_freight_adjustment')
                                .iterator()):
        (InternationalFreightRateTeam.objects
         .filter(international_freight_rate_id=rate_id)
         .update(fuel_freight_adjustment=adjustment))


def copyAdjustmentBackUpToRate(apps, schema_editor):
    """ย้อนกลับ : เอาค่าจากแถวทีมแถวแรกของแต่ละใบ กลับขึ้นไปไว้ที่ใบ

    ย้อนทันทีหลัง 0292 จะได้ค่าเดิมเป๊ะ เพราะตอนนั้นทุกแถวของใบเดียวกันยังเท่ากันหมด
    แต่ถ้ามีคนแก้ให้แต่ละทีมต่างกันไปแล้วค่อยย้อน ค่าที่ต่างกันจะหายไป เหลือค่าเดียว
    """
    InternationalFreightRate = apps.get_model('weightapp', 'InternationalFreightRate')
    InternationalFreightRateTeam = apps.get_model('weightapp', 'InternationalFreightRateTeam')
    for rate in InternationalFreightRate.objects.all().iterator():
        first = (InternationalFreightRateTeam.objects
                 .filter(international_freight_rate=rate)
                 .exclude(fuel_freight_adjustment=None)
                 .order_by('id')
                 .first())
        if first is not None:
            rate.fuel_freight_adjustment = first.fuel_freight_adjustment
            rate.save(update_fields=['fuel_freight_adjustment'])


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0295_exoeinvd_exoeinvh'),
    ]

    operations = [
        migrations.AddField(
            model_name='internationalfreightrateteam',
            name='fuel_freight_adjustment',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True,
                verbose_name='ปรับค่าขนส่งตามน้ำมัน (บาท/ตัน ต่อน้ำมัน 1 บาท/ลิตร)'),
        ),
        migrations.RunPython(copyAdjustmentDownToTeams, copyAdjustmentBackUpToRate),
    ]
