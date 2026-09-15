# เงื่อนไขการชำระเงินของแต่ละทีม เก็บช่องเดียวแบบ paytrm ของ Express
# 0 = เงินสด / 1 ขึ้นไป = เครดิตกี่วัน / NULL = ยังไม่ระบุ
# แถวเดิมทั้งหมดเป็น NULL ไม่ backfill เพราะไม่มีใครบอกว่าทีมไหนเงื่อนไขอะไร

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0298_ifr_base_fuel_price_range'),
    ]

    operations = [
        migrations.AddField(
            model_name='internationalfreightrateteam',
            name='credit_days',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='เครดิต (วัน) 0 = เงินสด'),
        ),
    ]
