# ยกเลิกขั้นการปรับน้ำมันรายทีม กลับไปคิดทุกบาททุกสตางค์เหมือนก่อนหน้านี้
# ช่วงราคาน้ำมันฐาน (ขอบล่าง-ขอบบน) ยังอยู่ ตัดออกแค่การตัดส่วนต่างเป็นขั้น
# สูตรในไฟล์รายงานรายเที่ยวย้ายไป template v14 ที่ไม่มีคอลัมน์ขั้นการปรับแล้ว

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0303_express_fuel_bill_snapshot'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='internationalfreightrateteam',
            name='fuel_adjust_step',
        ),
    ]
