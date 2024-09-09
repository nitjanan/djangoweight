# Generated by Django 4.1.4 on 2024-08-30 09:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0156_stock'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockStoneB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='รวมทั้งหมด')),
                ('stk', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.stock', verbose_name='stock')),
                ('stone', models.ForeignKey(blank=True, max_length=120, null=True, on_delete=django.db.models.deletion.CASCADE, to='weightapp.basestonetype', verbose_name='ชนิดหิน')),
            ],
            options={
                'db_table': 'stock_stone_b',
            },
        ),
    ]
