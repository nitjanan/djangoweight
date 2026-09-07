import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    เพิ่มวันที่สร้าง/วันที่แก้ไขล่าสุดให้ international_freight_rate

    เขียนเองแทนการรัน makemigrations เพราะ updated_at (auto_now) เป็นคอลัมน์
    NOT NULL ที่ไม่มี default ทำให้ makemigrations ถามหาค่า one-off แบบ interactive
    แถวเดิมที่มีอยู่จะได้เวลา ณ ตอน migrate ซึ่งไม่ใช่เวลาที่สร้างจริง แต่เป็นค่า
    ที่ใกล้เคียงที่สุดที่หาได้ เพราะข้อมูลเดิมไม่เคยเก็บเวลาไว้เลย
    """

    dependencies = [
        ('weightapp', '0277_rename_average_price_to_average_fuel_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='internationalfreightrate',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AddField(
            model_name='internationalfreightrate',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไขล่าสุด'),
        ),
    ]
