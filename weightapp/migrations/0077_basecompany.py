# Generated by Django 4.1.4 on 2023-10-09 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0076_alter_basemill_options_alter_basemill_mill_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseCompany',
            fields=[
                ('c_id', models.CharField(max_length=120, primary_key=True, serialize=False, verbose_name='รหัสบริษัท')),
                ('c_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='ชื่อบริษัท')),
            ],
        ),
    ]