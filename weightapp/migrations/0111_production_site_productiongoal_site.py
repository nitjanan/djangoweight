# Generated by Django 4.1.4 on 2023-11-10 13:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0110_remove_productiongoal_site'),
    ]

    operations = [
        migrations.AddField(
            model_name='production',
            name='site',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basesite'),
        ),
        migrations.AddField(
            model_name='productiongoal',
            name='site',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basesite'),
        ),
    ]
