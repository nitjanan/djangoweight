# Generated by Django 4.1.4 on 2023-07-10 03:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0010_alter_production_created_productiongoal'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productiongoal',
            old_name='ccumulated_goal',
            new_name='accumulated_goal',
        ),
    ]
