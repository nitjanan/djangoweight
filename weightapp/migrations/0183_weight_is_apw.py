# Generated by Django 4.1.4 on 2025-05-08 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0182_basemill_mill_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='weight',
            name='is_apw',
            field=models.BooleanField(default=False, verbose_name='สถานะตรวจสอบรายการชั่งแล้ว'),
        ),
    ]
