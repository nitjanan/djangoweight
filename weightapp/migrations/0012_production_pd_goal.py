# Generated by Django 4.1.4 on 2023-07-10 03:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0011_rename_ccumulated_goal_productiongoal_accumulated_goal'),
    ]

    operations = [
        migrations.AddField(
            model_name='production',
            name='pd_goal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.productiongoal'),
        ),
    ]
