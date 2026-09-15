# ค่าขนส่ง บาท/ตัน/กม. เปลี่ยนเป็นคำนวณอัตโนมัติ = ค่าขนส่ง / ระยะทางของใบ
# เติมให้แถวเดิมที่ยังว่าง จะได้เห็นค่าในหน้าเว็บและในไฟล์ export ทันที ไม่ต้องรอกดบันทึกใหม่
# แถวที่เคยกรอกเองไว้แล้วไม่แตะ เพราะอาจเป็นตัวเลขที่ตกลงกันจริงในเอกสารเดิม
# แถวพวกนั้นจะถูกคิดใหม่เองเมื่อมีการแก้ไขใบนั้นครั้งถัดไป

from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations


def backfill(apps, schema_editor):
    Team = apps.get_model('weightapp', 'InternationalFreightRateTeam')
    rows = (Team.objects.select_related('international_freight_rate')
            .filter(freight_rate_per_ton_km__isnull=True, freight_rate__isnull=False))
    for team in rows:
        distance = team.international_freight_rate.distance
        if not distance:
            continue
        team.freight_rate_per_ton_km = (Decimal(team.freight_rate) / Decimal(distance)).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP)
        team.save(update_fields=['freight_rate_per_ton_km'])


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0299_ifr_team_credit_days'),
    ]

    operations = [
        # ย้อนกลับไม่ต้องทำอะไร ค่าที่เติมเป็นค่าที่คำนวณได้ ไม่ได้ทับข้อมูลเดิม
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
