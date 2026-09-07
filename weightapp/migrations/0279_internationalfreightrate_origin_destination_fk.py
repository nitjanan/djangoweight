from django.db import migrations, models
import django.db.models.deletion


def text_to_fk(apps, schema_editor):
    """จับคู่ชื่อเดิม (ข้อความ) กลับไปหาแถวใน base_company_map_base_customer"""
    InternationalFreightRate = apps.get_model('weightapp', 'InternationalFreightRate')
    BaseCompanyMapBaseCustomer = apps.get_model('weightapp', 'BaseCompanyMapBaseCustomer')

    name_to_id = dict(BaseCompanyMapBaseCustomer.objects.values_list('name', 'id'))
    unmatched = []

    for rate in InternationalFreightRate.objects.all():
        origin_id = name_to_id.get(rate.origin)
        destination_id = name_to_id.get(rate.destination)

        if rate.origin and origin_id is None:
            unmatched.append((rate.id, 'origin', rate.origin))
        if rate.destination and destination_id is None:
            unmatched.append((rate.id, 'destination', rate.destination))

        rate.origin_map_id = origin_id
        rate.destination_map_id = destination_id
        rate.save(update_fields=['origin_map', 'destination_map'])

    # ชื่อที่หาไม่เจอจะกลายเป็น NULL ต้องแจ้งให้เห็น ไม่ปล่อยให้หายเงียบ
    for rate_id, field, value in unmatched:
        print("  [เตือน] rate id=%s %s=%r ไม่พบใน base_company_map_base_customer -> ตั้งเป็น NULL"
              % (rate_id, field, value))


def fk_to_text(apps, schema_editor):
    """ย้อนกลับ : เขียนชื่อจากแถว map กลับลงคอลัมน์ข้อความ"""
    InternationalFreightRate = apps.get_model('weightapp', 'InternationalFreightRate')
    for rate in InternationalFreightRate.objects.select_related('origin_map', 'destination_map'):
        rate.origin = rate.origin_map.name if rate.origin_map else None
        rate.destination = rate.destination_map.name if rate.destination_map else None
        rate.save(update_fields=['origin', 'destination'])


class Migration(migrations.Migration):
    """
    เปลี่ยน origin / destination จาก CharField เป็น FK ไป BaseCompanyMapBaseCustomer

    ทำเป็น 4 ขั้นเพื่อไม่ให้ข้อมูลเดิมหาย : เพิ่มคอลัมน์ใหม่ -> ย้ายข้อมูล ->
    ลบคอลัมน์เก่า -> เปลี่ยนชื่อคอลัมน์ใหม่มาใช้ชื่อเดิม
    """

    dependencies = [
        ('weightapp', '0278_internationalfreightrate_created_at_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='internationalfreightrate',
            name='origin_map',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='freight_rate_origins', to='weightapp.basecompanymapbasecustomer', verbose_name='ต้นทาง'),
        ),
        migrations.AddField(
            model_name='internationalfreightrate',
            name='destination_map',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='freight_rate_destinations', to='weightapp.basecompanymapbasecustomer', verbose_name='ปลายทาง'),
        ),
        migrations.RunPython(text_to_fk, fk_to_text),
        migrations.RemoveField(model_name='internationalfreightrate', name='origin'),
        migrations.RemoveField(model_name='internationalfreightrate', name='destination'),
        migrations.RenameField(
            model_name='internationalfreightrate',
            old_name='origin_map',
            new_name='origin',
        ),
        migrations.RenameField(
            model_name='internationalfreightrate',
            old_name='destination_map',
            new_name='destination',
        ),
    ]
