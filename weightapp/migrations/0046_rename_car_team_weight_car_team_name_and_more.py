# Generated by Django 4.1.4 on 2023-08-25 11:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0045_weight_car_team_id_weight_site_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='weight',
            old_name='car_team',
            new_name='car_team_name',
        ),
        migrations.RenameField(
            model_name='weight',
            old_name='site',
            new_name='site_name',
        ),
    ]