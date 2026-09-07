from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0271_alter_internationalfreightratelog_options_and_more'),
    ]

    operations = [
        # ตาราง international_freight_rate_team ยังไม่มีข้อมูล (0 แถว)
        # default=1 จึงไม่ถูกใช้จริง ใส่ไว้เพราะ MySQL ต้องการค่าตอนเพิ่มคอลัมน์ NOT NULL
        migrations.AddField(
            model_name='internationalfreightrateteam',
            name='international_freight_rate_id',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='teams',
                to='weightapp.internationalfreightrate',
                verbose_name='อัตราค่าขนส่งไปนอกประเทศ',
            ),
            preserve_default=False,
        ),
    ]
