# Generated by Django 4.1.4 on 2024-03-12 13:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0142_basesite_target'),
    ]

    operations = [
        migrations.CreateModel(
            name='SetWeightOY',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.TextField(blank=True, null=True, verbose_name='ตั้งค่าน้ำหนัก')),
                ('prod', models.TextField(blank=True, null=True, verbose_name='ตั้งค่าผลิต')),
                ('comp', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecompany', verbose_name='บริษัท')),
            ],
            options={
                'verbose_name': 'ผู้ชั่ง',
                'verbose_name_plural': 'ข้อมูลผู้ชั่ง',
            },
        ),
    ]
