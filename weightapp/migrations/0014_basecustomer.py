# Generated by Django 4.1.4 on 2023-07-12 06:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0013_basejobtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseCustomer',
            fields=[
                ('customer_id', models.CharField(max_length=120, primary_key=True, serialize=False)),
                ('customer_name', models.CharField(blank=True, max_length=255, null=True)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('send_to', models.CharField(blank=True, max_length=255, null=True)),
                ('customer_type', models.CharField(blank=True, max_length=255, null=True)),
                ('base_job_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basejobtype')),
                ('base_vat_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basevattype')),
            ],
            options={
                'db_table': 'base_customer',
            },
        ),
    ]
