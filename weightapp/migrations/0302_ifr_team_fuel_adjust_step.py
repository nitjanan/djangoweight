# ขั้นการปรับตามราคาน้ำมันรายทีม
# 0 = คิดทุกบาททุกสตางค์ (เท่ากับที่ระบบคิดอยู่ก่อนหน้านี้) / มากกว่า 0 = ปรับเป็นขั้น
# แถวเดิมได้ 0 จาก default จึงไม่ต้อง backfill และเงินของใบเก่าไม่เปลี่ยน

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0301_ifr_team_per_ton_km_2dp'),
    ]

    operations = [
        migrations.AddField(
            model_name='internationalfreightrateteam',
            name='fuel_adjust_step',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5,
                                      verbose_name='ขั้นการปรับน้ำมัน (บาท/ลิตร) 0 = ทุกบาททุกสตางค์'),
        ),
    ]
