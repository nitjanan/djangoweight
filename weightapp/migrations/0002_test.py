# Generated by Django 4.1.4 on 2024-02-22 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
    ]
