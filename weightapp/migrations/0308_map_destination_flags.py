# ธงบอกว่าแถว map ถูกใช้เป็นปลายทางของงานแบบไหน (ส่งออก / ในประเทศ)
#
# แถวเดิมทั้งหมดตั้งเป็น "ปลายทางส่งออก" เพราะหน้า /exportDocument/ เพิ่งเปลี่ยนมาถือว่า
# ทุกแถวใน map = ปลายทางส่งออก ถ้าตั้งเป็นไม่ติ๊ก เที่ยวจะหายทั้งหมดทันทีที่ deploy
# ตั้งค่าเริ่มต้นแบบ "ของเกิน" ปลอดภัยกว่า "ของหาย" เพราะของเกินเห็นได้จากแถบเตือนในหน้านั้น
# แถวที่ไม่ใช่ปลายทางส่งออก (เหมืองในเครือที่ใช้แถว map เป็นต้นทาง) ค่อยเอาติ๊กออกในหน้า admin
#
# แถวที่สร้างใหม่หลังจากนี้ไม่ติ๊กทั้งคู่ (ดู default ของฟิลด์ในโมเดล)

from django.db import migrations, models


def tickExportForExistingRows(apps, schema_editor):
    model = apps.get_model('weightapp', 'BaseCompanyMapBaseCustomer')
    model.objects.update(is_export_destination=True)


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0307_ifr_team_contract_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='basecompanymapbasecustomer',
            name='is_domestic_destination',
            field=models.BooleanField(default=False, verbose_name='ใช้เป็นปลายทางในประเทศ'),
        ),
        migrations.AddField(
            model_name='basecompanymapbasecustomer',
            name='is_export_destination',
            field=models.BooleanField(default=False, verbose_name='ใช้เป็นปลายทางส่งออก'),
        ),
        # ย้อนกลับไม่ต้องทำอะไร ฟิลด์ถูกลบไปพร้อมกันอยู่แล้ว
        migrations.RunPython(tickExportForExistingRows, migrations.RunPython.noop),
    ]
