# -*- coding: utf-8 -*-
"""ลบคอลัมน์ที่ไม่ใช้แล้วออกจากตัวใบอัตราค่าขนส่ง

payload_weight (น้ำหนักบรรทุก ตัน/เที่ยว) : เจ้าของงานยืนยันว่าไม่ได้ใช้แล้ว
และไม่เคยมีสูตรไหนคำนวณจากมัน มีแต่ช่องกรอกกับช่องแสดงผล

fuel_freight_adjustment : ย้ายลงไปเป็นรายแถวทีมแล้วใน 0296 คัดลอกค่าครบแล้ว

ย้อนกลับได้ถึงแค่ "โครงเดิม" — คอลัมน์กลับมาเป็น NULL ทั้งหมด
ถ้าต้องการค่า fuel_freight_adjustment กลับด้วย ให้ย้อน 0296 ต่ออีกขั้น (reverse ของมันเขียนค่าคืนให้)
ส่วน payload_weight ไม่มีทางกู้จาก migration ต้องไปหาใน binlog / backup
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0296_ifr_fuel_adjustment_per_team'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='internationalfreightrate',
            name='payload_weight',
        ),
        migrations.RemoveField(
            model_name='internationalfreightrate',
            name='fuel_freight_adjustment',
        ),
    ]
