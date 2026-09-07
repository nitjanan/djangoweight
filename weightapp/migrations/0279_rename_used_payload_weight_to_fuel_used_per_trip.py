from django.db import migrations, models


class Migration(migrations.Migration):
    """
    เปลี่ยน used_payload_weight (ใช้น้ำหนักบรรทุกเท่าไหร่) เป็น
    fuel_used_per_trip (ใช้น้ำมัน ลิตร/เที่ยว)

    ใช้ RenameField แทนที่จะ remove+add ตามที่ makemigrations เสนอ
    เพราะ remove+add จะ DROP COLUMN ทิ้งข้อมูลเดิม ส่วน RenameField ใช้
    ALTER TABLE ... CHANGE ซึ่งเก็บค่าเดิมไว้
    """

    dependencies = [
        ('weightapp', '0274_alter_internationalfreightrateteam_team'),
    ]

    operations = [
        migrations.RenameField(
            model_name='internationalfreightrate',
            old_name='used_payload_weight',
            new_name='fuel_used_per_trip',
        ),
        migrations.RenameField(
            model_name='internationalfreightratelog',
            old_name='used_payload_weight',
            new_name='fuel_used_per_trip',
        ),
        migrations.AlterField(
            model_name='internationalfreightrate',
            name='fuel_used_per_trip',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='ใช้น้ำมัน (ลิตร/เที่ยว)'),
        ),
        migrations.AlterField(
            model_name='internationalfreightratelog',
            name='fuel_used_per_trip',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='ใช้น้ำมัน (ลิตร/เที่ยว)'),
        ),
    ]
