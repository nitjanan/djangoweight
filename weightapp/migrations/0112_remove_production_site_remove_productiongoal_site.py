# Generated by Django 4.1.4 on 2023-11-10 13:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0111_production_site_productiongoal_site'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='production',
            name='site',
        ),
        migrations.RemoveField(
            model_name='productiongoal',
            name='site',
        ),
    ]