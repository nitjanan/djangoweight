# Generated by Django 4.1.4 on 2024-02-06 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0128_production_company_stoneestimate_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='productiongoal',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecompany', verbose_name='บริษัท'),
        ),
    ]
