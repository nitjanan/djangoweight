# Generated by Django 4.1.4 on 2024-01-31 14:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0130_basesite_s_comp'),
    ]

    operations = [
        migrations.AddField(
            model_name='basesite',
            name='step',
            field=models.IntegerField(blank=True, null=True, verbose_name='ลำดับโรงโม่ของบริษัท'),
        ),
        migrations.AlterField(
            model_name='basesite',
            name='s_comp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecompany', verbose_name='โรงโม่ของบริษัท'),
        ),
    ]
