# -*- coding: utf-8 -*-
"""โหมด "ดูข้อมูลอย่างเดียว" ของหน้าแก้ไขข้อมูลพื้นฐาน (editBase*)

เปิดด้วย ?view=1 ต่อท้าย url หน้าแก้ไข (เช่น ปุ่ม "ดูข้อมูล" ในกล่องเสนอชื่อคล้ายของหน้าเพิ่มข้อมูล)
- template (manage/formBaseLayout.html) ปิดทุกช่องกรอกและไม่แสดงปุ่มบันทึก
- ฝั่ง server ปฏิเสธการบันทึก (POST) ในโหมดนี้ กันกรณีแก้ HTML แล้วกดส่งเอง
"""
from functools import wraps

from django.http import HttpResponseForbidden

VIEW_ONLY_PARAM = 'view'


def isViewOnly(request):
    return request.GET.get(VIEW_ONLY_PARAM) == '1'


def viewOnlyUrl(url):
    return url + ('&' if '?' in url else '?') + VIEW_ONLY_PARAM + '=1'


def blockSaveInViewMode(view_func):
    """ใส่ให้ view หน้าแก้ไข : POST ที่มาจากโหมดดูข้อมูลจะไม่ถูกบันทึก"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST' and isViewOnly(request):
            return HttpResponseForbidden('โหมดดูข้อมูลอย่างเดียว ไม่สามารถบันทึกได้')
        return view_func(request, *args, **kwargs)
    return wrapper
