# Generated by Django 4.1.4 on 2023-08-09 04:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0032_weighthistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weighthistory',
            name='update',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
