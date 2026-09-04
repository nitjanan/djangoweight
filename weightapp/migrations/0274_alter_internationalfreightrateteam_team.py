import re

from django.db import migrations, models
import django.db.models.deletion


# international_freight_rate_team.team_id ต้องมี collation ตรงกับ base_car_team.car_team_id
# ไม่งั้น MySQL 8 ไม่ยอมสร้าง FK (error 3780)
#
# ห้าม fix ชื่อ collation ไว้ในโค้ด เพราะ base_car_team มี collation ไม่เหมือนกันในแต่ละเครื่อง
#   - เครื่องที่ restore จาก dump เก่าของ phpMyAdmin : utf8mb4_general_ci
#   - DB ที่สร้างใหม่จาก migration ล้วน ๆ           : utf8mb4_unicode_ci (default ของ DB)
# เดิมเขียน general_ci ตายตัว ทำให้รัน migration ตั้งแต่ศูนย์บน DB เปล่าไม่ผ่าน
# จึงต้องอ่าน collation จริงตอนรันแล้วทำตาม
#
# แปลงเฉพาะคอลัมน์ของตารางเรา ไม่แตะ base_car_team ที่มีข้อมูลจริงและมี FK จากตาราง
# base_car / weight / weight_history อ้างอิงอยู่

FK_NAME = 'ifr_team_team_id_fk_base_car_team_car_team_id'
SAFE_NAME = re.compile(r'^[A-Za-z0-9_]+$')


def _teamIdCollation(cursor):
    """(charset, collation) ของ base_car_team.car_team_id บนเครื่องที่กำลังรัน"""
    cursor.execute("""
        SELECT character_set_name, collation_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'base_car_team'
          AND column_name = 'car_team_id'
    """)
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError('ไม่พบคอลัมน์ base_car_team.car_team_id')
    charset, collation = row
    # ค่าที่ได้มาจาก information_schema อยู่แล้ว แต่กันไว้อีกชั้นเพราะต้องต่อเป็น SQL
    if not (SAFE_NAME.match(charset or '') and SAFE_NAME.match(collation or '')):
        raise RuntimeError('ชื่อ charset/collation ไม่ปลอดภัย : %r / %r' % (charset, collation))
    return charset, collation


def addFk(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        charset, collation = _teamIdCollation(cursor)
        cursor.execute(
            'ALTER TABLE `international_freight_rate_team` '
            'MODIFY `team_id` varchar(120) CHARACTER SET %s COLLATE %s NOT NULL'
            % (charset, collation))
        cursor.execute(
            'ALTER TABLE `international_freight_rate_team` '
            'ADD CONSTRAINT `%s` FOREIGN KEY (`team_id`) '
            'REFERENCES `base_car_team` (`car_team_id`)' % FK_NAME)


def dropFk(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('ALTER TABLE `international_freight_rate_team` '
                       'DROP FOREIGN KEY `%s`' % FK_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0273_rename_international_freight_rate_id_internationalfreightratelog_international_freight_rate_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # ฝั่ง DB : ทำเองด้วย SQL เพราะ Django สร้าง FK ตรงๆ ไม่ได้ (collation อาจไม่ตรง)
            database_operations=[
                migrations.RunPython(addFk, dropFk),
            ],
            # ฝั่ง state : บอก Django ว่าฟิลด์นี้มี constraint จริงแล้ว
            state_operations=[
                migrations.AlterField(
                    model_name='internationalfreightrateteam',
                    name='team',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='weightapp.basecarteam',
                        verbose_name='ทีมขนส่ง',
                    ),
                ),
            ],
        ),
    ]
