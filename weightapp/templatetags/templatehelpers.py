from django import template
from datetime import timedelta

register = template.Library()

@register.simple_tag
def my_url(value, field_name, urlencode=None):
    url = '?{}={}'.format(field_name, value)
    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        url = '{}&{}'.format(url, encoded_querystring)
    return url

@register.filter
def format_duration(duration):
    result = None
    if duration:
        hours = duration // timedelta(hours=1)
        minutes = (duration % timedelta(hours=1)) // timedelta(minutes=1)
        result = f"{hours:02d}:{minutes:02d}"
    else:
        result = f"{0}:{0:02d}"
    return result

@register.filter
def format_duration_substring(tmpStr):
    return str(tmpStr)[:-3]

@register.filter
def dict_keys(input_dict):
    return input_dict.keys()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "0.00")

@register.filter
def is_negative(value):
    try:
        return float(value) < 0
    except (TypeError, ValueError):
        return False

@register.filter
def do_doc_no_lines(value):
    """เลขที่ใบส่งของ เช่น DO2606-000001 -> แยกเป็น 2 ส่วนที่ขีดแรก
    <span class="do-head">DO2606-</span><span class="do-tail">000001</span>
    หน้าเว็บใช้ CSS เลือกเองว่าจะแสดงบรรทัดเดียวหรือ 2 บรรทัด (จอ notebook ลงไปแสดง 2 บรรทัด)
    ไม่มีค่า -> '-' / ไม่มีขีด -> แสดงทั้งก้อนเหมือนเดิม"""
    from django.utils.html import format_html
    if value is None or value == '':
        return '-'
    value = str(value)
    head, sep, tail = value.partition('-')
    if not sep or not tail:
        return value
    return format_html('<span class="do-head">{}{}</span><span class="do-tail">{}</span>', head, sep, tail)
