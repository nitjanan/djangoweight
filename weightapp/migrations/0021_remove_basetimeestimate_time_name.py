# Generated by Django 4.1.4 on 2023-07-31 04:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0020_basetimeestimate_time_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basetimeestimate',
            name='time_name',
        ),
    ]
