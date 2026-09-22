# สำเนาบิลเติมน้ำมันจาก Express เก็บไว้ในฐานข้อมูลของเรา
# ใช้แทนตอนต่อ Express ไม่ได้ ราคาน้ำมันเฉลี่ยและยอดหักค่าน้ำมัน (sheet oil) จะได้ไม่หายทั้งก้อน
# ตารางใหม่ล้วน ไม่แตะข้อมูลเดิม เริ่มว่างเปล่า จะถูกเติมเองครั้งแรกที่อ่าน Express ได้

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0302_ifr_team_fuel_adjust_step'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpressFuelBillSync',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.DateField(unique=True, verbose_name='เดือน (วันที่ 1)')),
                ('synced_at', models.DateTimeField(verbose_name='ดึงจาก Express เมื่อ')),
                ('bills', models.PositiveIntegerField(default=0, verbose_name='บิลทั้งหมดที่เจอ')),
                ('no_team', models.PositiveIntegerField(default=0, verbose_name='ไม่ใช่ทีมรถร่วม')),
                ('no_branch', models.PositiveIntegerField(default=0, verbose_name='ระบุสาขาไม่ได้')),
                ('duplicate', models.PositiveIntegerField(default=0, verbose_name='ซ้ำที่ตัดออก')),
                ('lines', models.PositiveIntegerField(default=0, verbose_name='บรรทัดที่เก็บ')),
            ],
            options={
                'verbose_name': 'ประวัติสำเนาบิลเติมน้ำมัน',
                'verbose_name_plural': 'ประวัติสำเนาบิลเติมน้ำมัน',
                'db_table': 'express_fuel_bill_sync',
            },
        ),
        migrations.CreateModel(
            name='ExpressFuelBillLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.DateField(db_index=True, verbose_name='เดือน (วันที่ 1)')),
                ('docnum', models.CharField(max_length=20, verbose_name='เลขที่บิล')),
                ('seqnum', models.IntegerField(blank=True, null=True, verbose_name='ลำดับรายการ')),
                ('docdate', models.DateField(blank=True, null=True, verbose_name='วันที่เติม')),
                ('cuscod', models.CharField(blank=True, default='', max_length=20, verbose_name='รหัสลูกค้า (ทีม)')),
                ('comcod', models.CharField(blank=True, default='', max_length=10, verbose_name='comcod')),
                ('stkdes', models.CharField(blank=True, default='', max_length=100, verbose_name='สินค้า')),
                ('ordqty', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='ลิตร')),
                ('unitpr', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='ราคา/ลิตร หน้าปั๊ม')),
                ('trnval', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='จำนวนเงิน')),
            ],
            options={
                'verbose_name': 'สำเนาบิลเติมน้ำมันจาก Express',
                'verbose_name_plural': 'สำเนาบิลเติมน้ำมันจาก Express',
                'db_table': 'express_fuel_bill_line',
                'unique_together': {('month', 'docnum', 'seqnum')},
            },
        ),
    ]
