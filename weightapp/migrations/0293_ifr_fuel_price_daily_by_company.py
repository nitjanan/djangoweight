# -*- coding: utf-8 -*-
"""ราคาน้ำมันเฉลี่ย : ย้ายจาก "รายเดือน ต่อเส้นทาง" เป็น "รายวัน ต่อบริษัท"

ตารางเปลี่ยนคีย์ทั้งหมด (root+month -> base_comp+date) ข้อมูลเดิม 5 แถวย้ายไม่ได้
เพราะเส้นทางหลายเส้นออกจากบริษัทเดียวกัน ถ้าย้ายตรง ๆ จะได้ราคาชนกันเองในวันเดียวกัน
เจ้าของงานยืนยันให้ลบทิ้งแล้วกรอกใหม่ในหน้าใหม่ จึงใช้ DeleteModel + CreateModel
(= DROP TABLE แล้ว CREATE ใหม่) ซึ่งอ่านง่ายกว่าไล่ RemoveField/AddField ทีละช่อง

ย้อนกลับได้ถึงแค่ "โครงเดิม" ข้อมูลไม่กลับมา จึงห้ามใช้ migrate ย้อนเป็นวิธีกู้ข้อมูล
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0288_ifr_effective_date'),
    ]

    operations = [
        migrations.DeleteModel(name='InternationalFreightRateFuelPrice'),
        migrations.CreateModel(
            name='InternationalFreightRateFuelPrice',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField(verbose_name='ประจำวันที่')),
                ('average_fuel_price', models.DecimalField(
                    decimal_places=2, max_digits=10,
                    verbose_name='ราคาน้ำมันเฉลี่ย (บาท/ลิตร)')),
                ('note', models.CharField(blank=True, max_length=255, null=True,
                                          verbose_name='หมายเหตุ')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now,
                                                    verbose_name='วันที่สร้าง')),
                ('updated_at', models.DateTimeField(auto_now=True,
                                                    verbose_name='วันที่แก้ไขล่าสุด')),
                ('base_comp', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='fuel_prices', to='weightapp.basecompany',
                    verbose_name='บริษัท')),
            ],
            options={
                'verbose_name': 'ราคาน้ำมันเฉลี่ยรายวัน',
                'verbose_name_plural': 'ราคาน้ำมันเฉลี่ยรายวัน',
                'db_table': 'international_freight_rate_fuel_price',
                'ordering': ['-date', 'base_comp_id'],
                'unique_together': {('base_comp', 'date')},
            },
        ),
        migrations.AddIndex(
            model_name='internationalfreightratefuelprice',
            index=models.Index(fields=['base_comp', '-date'], name='ifr_fuel_comp_date_idx'),
        ),
    ]
