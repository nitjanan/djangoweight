# Generated by Django 4.1.4 on 2024-09-27 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0164_basemachinetype_kind_alter_basemachinetype_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basemachinetype',
            name='kind',
            field=models.CharField(blank=True, choices=[('M', 'main'), ('S', 'second')], max_length=1, null=True, verbose_name='ประเภทเครื่องจักร'),
        ),
    ]