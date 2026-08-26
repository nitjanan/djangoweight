import datetime

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def move_average_fuel_price(apps, schema_editor):
    """ย้ายค่าที่มีอยู่เดิมไปเป็นราคาของ 'เดือนปัจจุบัน'

    ข้อมูลเดิมไม่ได้เก็บว่าราคานั้นเป็นของเดือนไหน จึงเดาได้แค่เดือนที่รัน migration
    ถ้าที่จริงเป็นราคาของเดือนอื่น ต้องไปแก้เดือนในหน้าเว็บเอง
    """
    InternationalFreightRate = apps.get_model('weightapp', 'InternationalFreightRate')
    FuelPrice = apps.get_model('weightapp', 'InternationalFreightRateFuelPrice')

    today = datetime.date.today().replace(day=1)
    moved = 0
    for rate in InternationalFreightRate.objects.exclude(average_fuel_price__isnull=True):
        FuelPrice.objects.create(
            international_freight_rate=rate,
            month=today,
            average_fuel_price=rate.average_fuel_price,
            note='ย้ายมาจากคอลัมน์เดิมตอน migrate (เดือนอาจไม่ตรงของจริง)',
        )
        moved += 1
    if moved:
        print("  ย้ายราคาน้ำมันเฉลี่ย %s แถว ไปเป็นเดือน %s" % (moved, today.strftime('%Y-%m')))


def restore_average_fuel_price(apps, schema_editor):
    """ย้อนกลับ : เอาราคาของเดือนล่าสุดของแต่ละเส้นทางกลับเข้าคอลัมน์เดิม"""
    InternationalFreightRate = apps.get_model('weightapp', 'InternationalFreightRate')
    FuelPrice = apps.get_model('weightapp', 'InternationalFreightRateFuelPrice')

    for rate in InternationalFreightRate.objects.all():
        latest = (FuelPrice.objects
                  .filter(international_freight_rate=rate)
                  .order_by('-month').first())
        if latest:
            rate.average_fuel_price = latest.average_fuel_price
            rate.save(update_fields=['average_fuel_price'])


class Migration(migrations.Migration):
    """แยกราคาน้ำมันเฉลี่ยออกจาก InternationalFreightRate มาเป็นตารางรายเดือน

    ทำ 3 ขั้นในไฟล์เดียว : สร้างตาราง -> ย้ายข้อมูล -> ลบคอลัมน์เดิม
    เรียงลำดับแบบนี้เพื่อไม่ให้ข้อมูลเดิมหายระหว่างทาง
    """

    dependencies = [
        ('weightapp', '0282_add_weight_export_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternationalFreightRateFuelPrice',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('month', models.DateField(verbose_name='ประจำเดือน')),
                ('average_fuel_price', models.DecimalField(
                    decimal_places=2, max_digits=10, verbose_name='ราคาน้ำมันเฉลี่ย (บาท/ลิตร)')),
                ('note', models.CharField(blank=True, max_length=255, null=True,
                                          verbose_name='หมายเหตุ')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now,
                                                    verbose_name='วันที่สร้าง')),
                ('updated_at', models.DateTimeField(auto_now=True,
                                                    verbose_name='วันที่แก้ไขล่าสุด')),
                ('international_freight_rate', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fuel_prices',
                    to='weightapp.internationalfreightrate',
                    verbose_name='อัตราค่าขนส่งไปนอกประเทศ')),
            ],
            options={
                'verbose_name': 'ราคาน้ำมันเฉลี่ยรายเดือน',
                'verbose_name_plural': 'ราคาน้ำมันเฉลี่ยรายเดือน',
                'db_table': 'international_freight_rate_fuel_price',
                'ordering': ['-month'],
                'unique_together': {('international_freight_rate', 'month')},
            },
        ),
        migrations.RunPython(move_average_fuel_price, restore_average_fuel_price),
        migrations.RemoveField(
            model_name='internationalfreightrate',
            name='average_fuel_price',
        ),
    ]
