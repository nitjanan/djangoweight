# Generated by Django 4.1.4 on 2023-06-23 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0005_alter_baselosstype_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productionlossitem',
            name='loss_time',
            field=models.DurationField(blank=True, null=True),
        ),
    ]
