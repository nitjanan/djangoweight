from django.db import migrations


class Migration(migrations.Migration):
    """
    เปลี่ยนชื่อ average_price เป็น average_fuel_price

    ใช้ RenameField (ALTER TABLE ... CHANGE) แทน remove+add ที่ makemigrations
    เสนอมา เพราะ remove+add จะ DROP COLUMN ทิ้งข้อมูลเดิม
    """

    dependencies = [
        ('weightapp', '0276_alter_internationalfreightrateteam_team_nullable'),
    ]

    operations = [
        migrations.RenameField(
            model_name='internationalfreightrate',
            old_name='average_price',
            new_name='average_fuel_price',
        ),
        migrations.RenameField(
            model_name='internationalfreightratelog',
            old_name='average_price',
            new_name='average_fuel_price',
        ),
    ]
