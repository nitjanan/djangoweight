# Generated by Django 4.1.4 on 2024-01-10 14:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0123_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseweightstation',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecompany'),
        ),
    ]
