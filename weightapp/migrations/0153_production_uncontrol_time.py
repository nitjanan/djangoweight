# Generated by Django 4.1.4 on 2024-07-10 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0152_alter_setpatterncode_end_alter_setpatterncode_m_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='production',
            name='uncontrol_time',
            field=models.DurationField(blank=True, null=True),
        ),
    ]