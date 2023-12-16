# Generated by Django 4.1.4 on 2023-12-15 10:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('weightapp', '0122_basevisible'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='ผู้ใช้')),
                ('visible', models.ManyToManyField(to='weightapp.basevisible', verbose_name='การมองเห็นแท็ปการใช้งาน')),
            ],
            options={
                'verbose_name': 'ผู้ใช้และตำแหน่งงาน',
                'verbose_name_plural': 'ข้อมูลผู้ใช้และตำแหน่งงาน',
            },
        ),
    ]