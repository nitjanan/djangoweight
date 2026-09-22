# วันทำสัญญาของแถวทีม (ทีม + ช่วงแบก นน.) ทีมเดียวกันคนละช่วงทำสัญญาคนละวันได้
# ว่างได้ แถวเดิมปล่อยว่าง ไม่เดาให้ ยังไม่มีสูตรไหนเอาไปคิดเงิน

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0306_base_company_map_customer_alias'),
    ]

    operations = [
        migrations.AddField(
            model_name='internationalfreightrateteam',
            name='contract_date',
            field=models.DateField(blank=True, null=True, verbose_name='วันทำสัญญา'),
        ),
    ]
