# Generated by Django 4.1.4 on 2023-09-11 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0056_remove_weight_f_fertilizer_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True, unique=True)),
            ],
            options={
                'db_table': 'base_test',
            },
        ),
    ]
