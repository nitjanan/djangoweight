# รหัสลูกค้าสำรองของแถว map (base_company_map_base_customer)
# ที่เดียวกันบางแห่งมีรหัสลูกค้าหลายตัว เช่น สุราษฎร์พอร์ท แอนด์ เทอร์มินอล 06-V-024 กับ 77-V-007
# ตารางใหม่ล้วน เริ่มว่าง ไม่แตะข้อมูลเดิม
#
# คอลัมน์ base_customer_id ต้องมี collation ตรงกับ base_customer.customer_id
# ไม่งั้น join สองตารางนี้ (เช่นช่องค้นหาในหน้า admin) จะเจอ error 1267 Illegal mix of collations
# collation ของ base_customer ไม่เหมือนกันในแต่ละ DB (dump เก่า = general_ci / สร้างใหม่ = unicode_ci)
# จึงอ่านค่าจริงตอนรันแล้วทำตาม แบบเดียวกับ 0278

import re

from django.db import migrations, models
import django.db.models.deletion

SAFE_NAME = re.compile(r'^[A-Za-z0-9_]+$')


def matchCustomerCollation(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT character_set_name, collation_name, column_type
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'base_customer'
              AND column_name = 'customer_id'
        """)
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError('ไม่พบคอลัมน์ base_customer.customer_id')
        charset, collation, column_type = row
        # ค่าที่ได้มาจาก information_schema อยู่แล้ว แต่กันไว้อีกชั้นเพราะต้องต่อเป็น SQL
        if not (SAFE_NAME.match(charset or '') and SAFE_NAME.match(collation or '')
                and re.match(r'^varchar\(\d+\)$', column_type or '')):
            raise RuntimeError('ค่าคอลัมน์ไม่ปลอดภัย : %r / %r / %r' % (charset, collation, column_type))
        cursor.execute(
            'ALTER TABLE `base_company_map_customer_alias` '
            'MODIFY `base_customer_id` %s CHARACTER SET %s COLLATE %s NOT NULL'
            % (column_type, charset, collation))


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0305_ifr_team_contract_values'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseCompanyMapCustomerAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_customer', models.OneToOneField(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='map_alias', to='weightapp.basecustomer', verbose_name='รหัสลูกค้าสำรอง')),
                ('map_row', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_aliases', to='weightapp.basecompanymapbasecustomer', verbose_name='แถว map')),
            ],
            options={
                'verbose_name': 'รหัสลูกค้าสำรอง',
                'verbose_name_plural': 'รหัสลูกค้าสำรอง',
                'db_table': 'base_company_map_customer_alias',
                'ordering': ['id'],
            },
        ),
        migrations.RunPython(matchCustomerCollation, migrations.RunPython.noop),
    ]
