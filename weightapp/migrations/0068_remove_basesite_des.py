# Generated by Django 4.1.4 on 2023-10-02 10:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0067_alter_basecustomersite_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basesite',
            name='des',
        ),
    ]
