# -*- coding: utf-8 -*-
"""เติมบทสนทนาการอนุมัติย้อนหลังให้ใบที่มีอยู่ก่อนเปิดระบบ

ไม่งั้นใบเก่าจะไม่มีประวัติเลย พอเปิดหน้าอนุมัติจริงจะดูเหมือนข้อมูลขาด
เขียนเป็น 2 แถวเหมือนใบใหม่ (ขอ + อนุมัติ) แต่ระบุชัดว่าเป็นการเติมย้อนหลัง
"""
from django.db import migrations


def backfill_trail(apps, schema_editor):
    Rate = apps.get_model('weightapp', 'InternationalFreightRate')
    Approval = apps.get_model('weightapp', 'InternationalFreightRateApproval')

    for rate in Rate.objects.all():
        if Approval.objects.filter(international_freight_rate=rate).exists():
            continue
        Approval.objects.create(
            international_freight_rate=rate, action='submit',
            comment='บันทึกก่อนเปิดระบบอนุมัติ', user=rate.user_created,
            created_at=rate.created_at)
        Approval.objects.create(
            international_freight_rate=rate, action='approve',
            comment='ถือว่าอนุมัติแล้ว (ข้อมูลที่ใช้งานอยู่ก่อนเปิดระบบ)', user=None,
            created_at=rate.created_at)
        Rate.objects.filter(id=rate.id).update(
            submitted_at=rate.created_at, approved_at=rate.created_at)


def unbackfill_trail(apps, schema_editor):
    Approval = apps.get_model('weightapp', 'InternationalFreightRateApproval')
    Approval.objects.filter(comment__in=[
        'บันทึกก่อนเปิดระบบอนุมัติ',
        'ถือว่าอนุมัติแล้ว (ข้อมูลที่ใช้งานอยู่ก่อนเปิดระบบ)',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('weightapp', '0286_international_freight_rate_approval'),
    ]

    operations = [
        migrations.RunPython(backfill_trail, unbackfill_trail),
    ]
