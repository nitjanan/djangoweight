# Generated by Django 4.1.4 on 2023-09-11 13:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0054_weight_fertilizer_weighthistory_fertilizer'),
    ]

    operations = [
        migrations.RenameField(
            model_name='weight',
            old_name='fertilizer',
            new_name='f_fertilizer',
        ),
        migrations.RenameField(
            model_name='weighthistory',
            old_name='fertilizer',
            new_name='f_fertilizer',
        ),
    ]