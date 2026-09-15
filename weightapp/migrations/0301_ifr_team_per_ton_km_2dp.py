# ค่าขนส่ง บาท/ตัน/กม. เปลี่ยนจาก 4 เป็น 2 ตำแหน่งทศนิยม
#
# ต้องคิดใหม่จากต้นทาง (ค่าขนส่ง / ระยะทาง) ก่อนย่อคอลัมน์ ไม่ปล่อยให้ MySQL ปัดจากค่า 4 ตำแหน่ง
# เพราะปัดสองรอบอาจเพี้ยน 0.01 เช่นค่าจริง 1.004999 -> 1.0050 -> 1.01 แต่ที่ถูกคือ 1.00
# แตะเฉพาะแถวที่ค่าเดิมตรงกับสูตร (คือแถวที่ระบบคิดให้) แถวที่คนกรอกเองไว้ไม่แก้
# แถวพวกนั้นจะถูกปัดโดย MySQL ตอน AlterField ตามปกติ

from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models


def _calc(freight_rate, distance, places):
    return (Decimal(freight_rate) / Decimal(distance)).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def recompute_derived(apps, schema_editor):
    Team = apps.get_model('weightapp', 'InternationalFreightRateTeam')
    rows = (Team.objects.select_related('international_freight_rate')
            .filter(freight_rate_per_ton_km__isnull=False, freight_rate__isnull=False))
    for team in rows:
        distance = team.international_freight_rate.distance
        if not distance:
            continue
        if Decimal(team.freight_rate_per_ton_km) != _calc(team.freight_rate, distance, '0.0001'):
            continue
        team.freight_rate_per_ton_km = _calc(team.freight_rate, distance, '0.01')
        team.save(update_fields=['freight_rate_per_ton_km'])


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0300_ifr_team_backfill_per_ton_km'),
    ]

    operations = [
        migrations.RunPython(recompute_derived, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='internationalfreightrateteam',
            name='freight_rate_per_ton_km',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='ค่าขนส่ง บาท/ตัน/กม.'),
        ),
    ]
