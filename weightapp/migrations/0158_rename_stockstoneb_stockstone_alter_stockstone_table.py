# Generated by Django 4.1.4 on 2024-08-30 09:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0157_stockstoneb'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StockStoneB',
            new_name='StockStone',
        ),
        migrations.AlterModelTable(
            name='stockstone',
            table='stock_stone',
        ),
    ]