# Generated by Django 4.1.4 on 2024-01-31 14:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0129_productiongoal_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='basesite',
            name='s_comp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecompany', verbose_name='บริษัท'),
        ),
    ]
