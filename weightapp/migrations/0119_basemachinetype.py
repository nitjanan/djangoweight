# Generated by Django 4.1.4 on 2023-11-24 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0118_alter_stoneestimateitem_percent'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseMachineType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True, unique=True)),
            ],
            options={
                'db_table': 'base_machine_type',
                'ordering': ['id'],
            },
        ),
    ]