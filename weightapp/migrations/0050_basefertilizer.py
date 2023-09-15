# Generated by Django 4.1.4 on 2023-09-11 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0049_rename_fertilizer_weight_fertilizer_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseFertilizer',
            fields=[
                ('fertilizer_id', models.CharField(max_length=120, primary_key=True, serialize=False)),
                ('fertilizer_name', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'base_fertilizer',
            },
        ),
    ]
