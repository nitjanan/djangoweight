# Generated by Django 4.1.4 on 2023-12-29 11:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0131_basesite_step_alter_basesite_s_comp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basesite',
            name='s_comp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basecompany', verbose_name='โรงโม่ของบริษัท'),
        ),
    ]
