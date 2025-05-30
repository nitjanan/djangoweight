# Generated by Django 4.1.4 on 2025-05-22 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0183_weight_is_apw'),
    ]

    operations = [
        migrations.AddField(
            model_name='stoneestimate',
            name='other',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True, verbose_name='จากโรงโม่อื่น'),
        ),
        migrations.AddField(
            model_name='stoneestimate',
            name='scale',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True, verbose_name='จากตาชั่ง'),
        ),
        migrations.AddField(
            model_name='stoneestimate',
            name='topup',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True, verbose_name='top up ไม่ผ่านตาชั่ง'),
        ),
        migrations.AddField(
            model_name='stoneestimate',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True, verbose_name='รวม'),
        ),
    ]
