import re

from django.db import migrations, models
import django.db.models.deletion


# ทำให้ team_id เป็น NULL ได้ (NULL = ทุกทีม)
#
# ต้องเขียน SQL เอง เพราะถ้าปล่อยให้ Django gen AlterField มันจะสร้างคอลัมน์ใหม่ด้วย
# collation default ของ DB ซึ่งอาจไม่ตรงกับ base_car_team.car_team_id แล้ว FK ที่สร้างไว้
# ใน migration 0274 จะพัง (MySQL error 3780)
#
# ห้าม fix ชื่อ collation ไว้ในโค้ด เพราะ base_car_team มี collation ไม่เหมือนกันในแต่ละเครื่อง
# (เครื่องที่ restore จาก dump เก่าเป็น general_ci ส่วน DB ที่สร้างใหม่เป็น unicode_ci)
# ต้องอ่านของจริงตอนรันแล้วทำตาม เหมือนที่ 0274 ทำ
#
# MySQL ไม่ยอมให้แก้ชนิดคอลัมน์ที่มี FK ค้างอยู่ จึง drop -> modify -> add ใหม่

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
    if not (SAFE_NAME.match(charset or '') and SAFE_NAME.match(collation or '')):
        raise RuntimeError('ชื่อ charset/collation ไม่ปลอดภัย : %r / %r' % (charset, collation))
    return charset, collation


def _rebuildTeamId(schema_editor, null_clause):
    with schema_editor.connection.cursor() as cursor:
        charset, collation = _teamIdCollation(cursor)
        cursor.execute('ALTER TABLE `international_freight_rate_team` '
                       'DROP FOREIGN KEY `%s`' % FK_NAME)
        cursor.execute(
            'ALTER TABLE `international_freight_rate_team` '
            'MODIFY `team_id` varchar(120) CHARACTER SET %s COLLATE %s %s'
            % (charset, collation, null_clause))
        cursor.execute(
            'ALTER TABLE `international_freight_rate_team` '
            'ADD CONSTRAINT `%s` FOREIGN KEY (`team_id`) '
            'REFERENCES `base_car_team` (`car_team_id`)' % FK_NAME)


def makeNullable(apps, schema_editor):
    _rebuildTeamId(schema_editor, 'NULL')


def makeNotNull(apps, schema_editor):
    _rebuildTeamId(schema_editor, 'NOT NULL')


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0279_rename_used_payload_weight_to_fuel_used_per_trip'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(makeNullable, makeNotNull),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='internationalfreightrateteam',
                    name='team',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='weightapp.basecarteam',
                        verbose_name='ทีมขนส่ง (ว่าง = ทุกทีม)',
                    ),
                ),
            ],
        ),
    ]
