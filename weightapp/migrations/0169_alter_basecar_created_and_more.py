# Generated by Django 4.1.4 on 2024-12-02 10:41

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0168_basecar_created_basecar_user_created_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basecar',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basecarregistration',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basecarteam',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basecustomersite',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basedriver',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basejobtype',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basemill',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basescoop',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basesite',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
        migrations.AlterField(
            model_name='basestonetype',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
    ]
