# Generated by Django 4.1.4 on 2023-10-04 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0073_weighthistory_v_stamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='weight',
            name='v_stamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
