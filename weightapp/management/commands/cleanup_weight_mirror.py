# -*- coding: utf-8 -*-
"""ลบสำเนาข้อมูลชั่ง (weight_mirror) ที่เก่าเกินกว่าจะใช้กู้ตาชั่ง

ข้อมูลช่วงนั้นถูกอัพโหลดตอนเย็นเข้าตาราง weight จริงไปแล้ว ; ตั้ง cron/Task Scheduler วันละครั้ง :
    python manage.py cleanup_weight_mirror --days 60
"""
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from weightapp.models import WeightMirror


class Command(BaseCommand):
    help = 'ลบ weight_mirror ที่รับเข้ามานานกว่า --days วัน (ค่าเริ่มต้น 60)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=60)

    def handle(self, *args, **options):
        days = max(options['days'], 7)
        cutoff = datetime.now() - timedelta(days=days)
        deleted, _ = WeightMirror.objects.filter(received_at__lt=cutoff).delete()
        self.stdout.write('ลบ weight_mirror ที่เก่ากว่า %d วัน %d แถว' % (days, deleted))
