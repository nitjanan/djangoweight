# Generated by Django 4.1.4 on 2023-08-10 10:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0036_alter_weighthistory_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='basecustomer',
            name='weight_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.baseweighttype', verbose_name='ชนิดเครื่องชั่ง'),
        ),
    ]