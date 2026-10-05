# -*- coding: utf-8 -*-
"""settings สำหรับ GitHub Actions (.github/workflows/django-checks.yml)

ใช้ทุกอย่างจาก settings.py เปลี่ยนแค่ฐานข้อมูล
- default : MySQL ใน service container ของ workflow อ่านค่าจาก env DB_*
  ต้องเป็นฐานจริงที่ migrate แล้ว เพราะ weightapp/forms.py ยิง query ตอน import
  (ProductionLossItemFormset นับ BaseLossType) ทุกคำสั่งที่โหลด urls จึงต้องมีตารางอยู่ก่อน
- pg_db (Express) : ตัดทิ้ง CI ห้ามพยายามต่อเครื่อง Express จริง

ลองแบบเดียวกับ CI บนเครื่องตัวเองได้ (ชี้ DB_NAME ไปฐานว่างที่สร้างไว้ลองเท่านั้น) :
    DJANGO_SETTINGS_MODULE=weight.settings_ci DB_NAME=... DB_PORT=13306 python manage.py migrate --skip-checks
"""
import os

from weight.settings import *  # noqa: F401,F403
from weight.settings import DATABASES as _BASE_DATABASES

DATABASES = {
    'default': dict(
        _BASE_DATABASES['default'],
        NAME=os.environ.get('DB_NAME', 'djangoweightdb'),
        USER=os.environ.get('DB_USER', 'root'),
        PASSWORD=os.environ.get('DB_PASSWORD', ''),
        HOST=os.environ.get('DB_HOST', '127.0.0.1'),
        PORT=os.environ.get('DB_PORT', '3306'),
    ),
}
