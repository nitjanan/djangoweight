# Generated by Django 4.1.4 on 2023-10-03 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0070_basecustomer_v_stamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='basecarteam',
            name='v_stamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
