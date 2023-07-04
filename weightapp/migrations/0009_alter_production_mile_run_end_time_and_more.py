# Generated by Django 4.1.4 on 2023-07-04 02:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0008_production_mile_run_end_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='production',
            name='mile_run_end_time',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='production',
            name='mile_run_start_time',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
    ]
