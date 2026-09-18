# เก็บค่าที่ตกลงกันตอนทำสัญญาไว้ในแถวทีม : ค่าขนส่งตามสัญญา กับ ราคาน้ำมันฐานวันทำสัญญา
# ยังไม่มีสูตรไหนเอาไปคิดเงิน เก็บไว้อ้างอิงอย่างเดียว
# แถวเดิมปล่อยเป็น NULL (ยังไม่ได้กรอก) ไม่ยกค่าปัจจุบันไปเติมแทน เพราะจะกลายเป็นระบบเดาแทนผู้ใช้

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0304_ifr_team_drop_fuel_adjust_step'),
    ]

    operations = [
        migrations.AddField(
            model_name='internationalfreightrateteam',
            name='contract_base_fuel_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='ราคาน้ำมันฐานวันทำสัญญา (บาท/ลิตร)'),
        ),
        migrations.AddField(
            model_name='internationalfreightrateteam',
            name='contract_freight_rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='ค่าขนส่งตามสัญญา (บาท/ตัน)'),
        ),
    ]
