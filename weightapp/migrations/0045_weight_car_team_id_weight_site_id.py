# Generated by Django 4.1.4 on 2023-08-25 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0044_basecustomer_is_stone_estimate'),
    ]

    operations = [
        migrations.AddField(
            model_name='weight',
            name='car_team_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='weight',
            name='site_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]