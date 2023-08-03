# Generated by Django 4.1.4 on 2023-08-02 06:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0023_alter_weight_approve_id_alter_weight_approve_name_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='weight',
            options={'ordering': ['weight_id']},
        ),
        migrations.CreateModel(
            name='BaseSite',
            fields=[
                ('base_site_id', models.CharField(max_length=120, primary_key=True, serialize=False, verbose_name='รหัสหน้างาน')),
                ('base_site_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='ชื่อหน้างาน')),
                ('base_customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecustomer', verbose_name='ลูกค้า')),
            ],
            options={
                'verbose_name': 'หน้างาน',
                'verbose_name_plural': 'ข้อมูลหน้างาน',
                'db_table': 'base_site',
            },
        ),
    ]
