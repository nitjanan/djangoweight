# Generated by Django 4.1.4 on 2024-11-08 09:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0166_approveweight'),
    ]

    operations = [
        migrations.AddField(
            model_name='weight',
            name='apw',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.approveweight'),
        ),
    ]
