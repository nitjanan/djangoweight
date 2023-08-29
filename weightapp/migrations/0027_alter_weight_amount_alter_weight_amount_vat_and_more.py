# Generated by Django 4.1.4 on 2023-08-07 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0026_alter_weight_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weight',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='amount_vat',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='freight_cost',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='freight_cost_total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='oil_content',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='origin_q',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='origin_weight',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='price_down',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='price_down_total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='price_per_ton',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='price_up',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='price_up_total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='q',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='sack',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='ton',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='vat',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='weight_in',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='weight_out',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='weight',
            name='weight_total',
            field=models.DecimalField(blank=True, decimal_places=3, default=0.0, max_digits=10, null=True),
        ),
    ]
