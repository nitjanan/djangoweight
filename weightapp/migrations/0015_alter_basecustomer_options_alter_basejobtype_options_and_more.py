# Generated by Django 4.1.4 on 2023-07-14 06:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0014_basecustomer'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basecustomer',
            options={'verbose_name': 'ลูกค้า', 'verbose_name_plural': 'ข้อมูลลูกค้า'},
        ),
        migrations.AlterModelOptions(
            name='basejobtype',
            options={'verbose_name': 'ประเภทงานของลูกค้า', 'verbose_name_plural': 'ข้อมูลประเภทงานของลูกค้า'},
        ),
        migrations.AlterModelOptions(
            name='basevattype',
            options={'verbose_name': 'ชนิดvat', 'verbose_name_plural': 'ข้อมูลชนิดvat'},
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ที่อยู่'),
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='base_job_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basejobtype', verbose_name='ประเภทงานของลูกค้า'),
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='base_vat_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basevattype', verbose_name='ชนิดvat'),
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='customer_id',
            field=models.CharField(max_length=120, primary_key=True, serialize=False, verbose_name='รหัสลูกค้า'),
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='customer_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ชื่อลูกค้า'),
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='customer_type',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ประเภทลูกค้า'),
        ),
        migrations.AlterField(
            model_name='basecustomer',
            name='send_to',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ส่งที่'),
        ),
        migrations.AlterField(
            model_name='basejobtype',
            name='base_job_type_id',
            field=models.CharField(max_length=120, primary_key=True, serialize=False, verbose_name='รหัสประเภทงานของลูกค้า'),
        ),
        migrations.AlterField(
            model_name='basejobtype',
            name='base_job_type_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ชื่อประเภทงานของลูกค้า'),
        ),
        migrations.AlterField(
            model_name='basevattype',
            name='base_vat_type_des',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='คำอธิบาย'),
        ),
        migrations.AlterField(
            model_name='basevattype',
            name='base_vat_type_id',
            field=models.CharField(max_length=120, primary_key=True, serialize=False, verbose_name='รหัสชนิดvat'),
        ),
        migrations.AlterField(
            model_name='basevattype',
            name='base_vat_type_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ชื่อชนิดvat'),
        ),
    ]
