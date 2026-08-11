from django.db import migrations, models
import django.db.models.deletion


# international_freight_rate_team.team_id ถูกสร้างด้วย utf8mb4_unicode_ci (default ของ DB)
# แต่ base_car_team.car_team_id เป็น utf8mb4_general_ci (ตารางเก่าจาก phpMyAdmin dump)
# MySQL 8 ไม่ยอมสร้าง FK ข้าม collation (error 3780) จึงต้องแปลง collation ฝั่งเราให้ตรงก่อน
#
# แปลงเฉพาะคอลัมน์ของตารางเรา ไม่แตะ base_car_team ที่มีข้อมูลจริงและมี FK จากตาราง
# base_car / weight / weight_history อ้างอิงอยู่
FORWARD_SQL = """
ALTER TABLE `international_freight_rate_team`
    MODIFY `team_id` varchar(120)
    CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL;

ALTER TABLE `international_freight_rate_team`
    ADD CONSTRAINT `ifr_team_team_id_fk_base_car_team_car_team_id`
    FOREIGN KEY (`team_id`) REFERENCES `base_car_team` (`car_team_id`);
"""

REVERSE_SQL = """
ALTER TABLE `international_freight_rate_team`
    DROP FOREIGN KEY `ifr_team_team_id_fk_base_car_team_car_team_id`;

ALTER TABLE `international_freight_rate_team`
    MODIFY `team_id` varchar(120)
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0273_rename_international_freight_rate_id_internationalfreightratelog_international_freight_rate_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # ฝั่ง DB : ทำเองด้วย SQL เพราะ Django สร้าง FK ตรงๆ ไม่ได้ (collation ไม่ตรง)
            database_operations=[
                migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
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
