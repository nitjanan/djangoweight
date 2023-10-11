# Generated by Django 4.1.4 on 2023-09-29 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0064_rename_customersite_baescustomersite_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baescustomersite',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecustomer', verbose_name='ลูกค้า'),
        ),
        migrations.AlterField(
            model_name='baescustomersite',
            name='site',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basesite', verbose_name='หน้างาน'),
        ),
    ]