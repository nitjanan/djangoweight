from django.db import migrations, models
import django.db.models.deletion


# ทำให้ team_id เป็น NULL ได้ (NULL = ทุกทีม)
#
# ต้องเขียน SQL เอง เพราะถ้าปล่อยให้ Django gen AlterField มันจะสร้างคอลัมน์ใหม่ด้วย
# collation default ของ DB (utf8mb4_unicode_ci) ซึ่งไม่ตรงกับ base_car_team.car_team_id
# (utf8mb4_general_ci) แล้ว FK ที่สร้างไว้ใน migration 0274 จะพัง (MySQL error 3780)
#
# MySQL ไม่ยอมให้แก้ชนิดคอลัมน์ที่มี FK ค้างอยู่ จึง drop -> modify -> add ใหม่
FORWARD_SQL = """
ALTER TABLE `international_freight_rate_team`
    DROP FOREIGN KEY `ifr_team_team_id_fk_base_car_team_car_team_id`;

ALTER TABLE `international_freight_rate_team`
    MODIFY `team_id` varchar(120)
    CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL;

ALTER TABLE `international_freight_rate_team`
    ADD CONSTRAINT `ifr_team_team_id_fk_base_car_team_car_team_id`
    FOREIGN KEY (`team_id`) REFERENCES `base_car_team` (`car_team_id`);
"""

REVERSE_SQL = """
ALTER TABLE `international_freight_rate_team`
    DROP FOREIGN KEY `ifr_team_team_id_fk_base_car_team_car_team_id`;

ALTER TABLE `international_freight_rate_team`
    MODIFY `team_id` varchar(120)
    CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL;

ALTER TABLE `international_freight_rate_team`
    ADD CONSTRAINT `ifr_team_team_id_fk_base_car_team_car_team_id`
    FOREIGN KEY (`team_id`) REFERENCES `base_car_team` (`car_team_id`);
"""


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0275_rename_used_payload_weight_to_fuel_used_per_trip'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
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
