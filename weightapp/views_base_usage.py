# -*- coding: utf-8 -*-
"""หน้าแก้ไขข้อมูลพื้นฐาน (editBase*) : แสดงว่ามีบริษัทไหนใช้ข้อมูลนี้ในตาราง weight แล้วบ้าง

ให้ user รู้ก่อนแก้ ว่าการแก้จะกระทบตาชั่งของบริษัทไหน (edit view อัปเดตชื่อใน weight ตามด้วย)
weight ผูกกับบริษัทผ่านตาชั่ง : weight.bws -> base_weight_station.company
นับทุกแถวรวมที่ยกเลิกแล้ว เพราะตอนแก้ชื่อ edit view ก็อัปเดตแถวที่ยกเลิกไปด้วย
"""
from django.db.models import Count, Max

from weightapp.models import BaseCustomerSite, Weight

# key = model ข้อมูลพื้นฐาน -> ฟิลด์ใน weight ที่ใช้กรอง
# BaseCar (รถร่วม) ไม่มีคอลัมน์ใน weight จึงไม่มีในนี้
# BaseJobType ไม่ได้อยู่ใน weight ตรง ๆ ดูผ่านลูกค้าที่อยู่ในประเภทงานนั้น
WEIGHT_USAGE_LOOKUP = {
    'BaseMill': 'mill_id',
    'BaseJobType': 'customer__base_job_type_id',
    'BaseStoneType': 'stone_type_id',
    'BaseScoop': 'scoop_id',
    'BaseCarTeam': 'car_team_id',
    'BaseSite': 'site_id',
    'BaseCustomer': 'customer_id',
    'BaseDriver': 'driver_id',
    'BaseCarRegistration': 'car_registration_id',
}


def _weightFilter(model_key, pk):
    if model_key == 'BaseCustomerSite':
        # ลูกค้าและหน้างาน : weight ที่มีลูกค้าและปลายทางคู่นี้
        pair = BaseCustomerSite.objects.filter(pk=pk).values('customer_id', 'site_id').first()
        if not pair or not pair['customer_id'] or not pair['site_id']:
            return None
        return {'customer_id': pair['customer_id'], 'site_id': pair['site_id']}
    return {WEIGHT_USAGE_LOOKUP[model_key]: pk}


def weightUsageByCompany(model_key, pk):
    """รายการบริษัทที่มี weight ใช้ข้อมูลนี้ : [{code, name, count, last_date}] เรียงตามลำดับแท็ปบริษัท"""
    weight_filter = _weightFilter(model_key, pk)
    if weight_filter is None:
        return []
    rows = (Weight.objects.filter(**weight_filter)
            .values('bws__company__code', 'bws__company__name', 'bws__company__step')
            .annotate(count=Count('weight_id'), last_date=Max('date'))
            .order_by())
    usage = [{
        'code': r['bws__company__code'],
        'name': r['bws__company__name'] or 'ไม่ระบุบริษัท',
        'step': r['bws__company__step'],
        'count': r['count'],
        'last_date': r['last_date'],
    } for r in rows]
    # บริษัทที่ไม่มีลำดับ / ไม่ระบุบริษัท ไว้ท้าย
    usage.sort(key=lambda u: (u['code'] is None, u['step'] is None, u['step'] or 0, u['name']))
    return usage


def weightUsageContext(model_key, pk):
    usage = weightUsageByCompany(model_key, pk)
    return {'weight_usage': usage, 'weight_usage_total': sum(u['count'] for u in usage)}
