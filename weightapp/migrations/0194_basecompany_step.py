# Generated by Django 4.1.4 on 2025-06-10 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0193_basecompany_biz'),
    ]

    operations = [
        migrations.AddField(
            model_name='basecompany',
            name='step',
            field=models.IntegerField(blank=True, null=True, verbose_name='ลำดับแท็ปบริษัท'),
        ),
    ]
