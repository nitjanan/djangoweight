# -*- coding: utf-8 -*-
"""effective_month -> effective_date : เก็บวันที่จริง ไม่บังคับวันที่ 1 ของเดือนอีกต่อไป

ต้องใช้ RenameField ไม่ใช่ RemoveField + AddField (ซึ่งเป็นสิ่งที่ makemigrations สร้างให้)
เพราะ remove+add จะ DROP คอลัมน์ทิ้ง ข้อมูลวันที่เริ่มใช้ของทุกใบจะหายหมด
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0287_backfill_approval_trail'),
    ]

    operations = [
        # ต้องถอด index ก่อน เพราะมันอ้างชื่อคอลัมน์เดิมอยู่
        migrations.RemoveIndex(
            model_name='internationalfreightrate',
            name='ifr_root_status_month_idx',
        ),
        migrations.RenameField(
            model_name='internationalfreightrate',
            old_name='effective_month',
            new_name='effective_date',
        ),
        migrations.AlterField(
            model_name='internationalfreightrate',
            name='effective_date',
            field=models.DateField(blank=True, null=True, verbose_name='วันที่เริ่มใช้'),
        ),
        migrations.AddIndex(
            model_name='internationalfreightrate',
            index=models.Index(fields=['root', 'status', '-effective_date', '-id'],
                               name='ifr_root_status_month_idx'),
        ),
    ]
