# Generated by Django 4.1.4 on 2024-12-18 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0169_alter_basecar_created_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test', models.CharField(blank=True, max_length=255, null=True, verbose_name='รหัสผู้ชั่ง')),
            ],
        ),
    ]
