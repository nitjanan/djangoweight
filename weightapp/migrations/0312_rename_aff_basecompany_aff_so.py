from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0311_basecompany_aff'),
    ]

    operations = [
        # rename (ไม่ใช่ลบแล้วเพิ่มใหม่) เพื่อเก็บค่าสังกัดที่ตั้งไว้แล้ว: คอลัมน์ aff_id -> aff_so_id
        migrations.RenameField(
            model_name='basecompany',
            old_name='aff',
            new_name='aff_so',
        ),
        migrations.AlterField(
            model_name='basecompany',
            name='aff_so',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branch_affiliated', to='weightapp.baseaffiliatedcompany', verbose_name='นามบริษัทที่ออกใบสั่งขาย'),
        ),
    ]
