# Generated by Django 4.1.4 on 2023-11-14 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0117_remove_basetimeestimate_mill_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stoneestimateitem',
            name='percent',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
