# Generated by Django 4.1.4 on 2023-08-09 03:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0029_basestonetype_is_stone_estimate'),
    ]

    operations = [
        migrations.AddField(
            model_name='weight',
            name='stone_type_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
