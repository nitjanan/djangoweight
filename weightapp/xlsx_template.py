# -*- coding: utf-8 -*-
"""
ช่วยเขียนไฟล์ excel โดยใช้ไฟล์ template เดิมเป็นฐาน

ไฟล์ รายเที่ยว_template_v11.xlsx ทั้งเล่มขับด้วย sheet "บันทึกรายเที่ยว" เพียง sheet เดียว
sheet สรุปเหมือง / ปะหน้าจ่ายรถร่วม / สรุปจ่ายรถร่วม เป็นสูตรล้วนที่อ้างกลับมาที่ sheet นี้
เราจึงเติมแค่ข้อมูลดิบลงไป แล้ว excel คิดที่เหลือให้เอง ห้ามสร้าง workbook ใหม่

ปัญหาที่ต้องแก้ : dropdown ในไฟล์ template เป็น data validation ชนิด x14 (extension)
ซึ่ง openpyxl อ่านไม่ออก พอ save จะหายไปทั้งหมด 16 ตัว
วิธีแก้คือหลัง openpyxl เขียนเสร็จ ให้ก๊อปบล็อก <extLst> ของแต่ละ sheet
จากไฟล์ต้นฉบับใส่กลับเข้าไปในไฟล์ผลลัพธ์ตรง ๆ
"""
import io
import os
import re
import zipfile
# ใช้ defusedxml แทน xml.etree ของ stdlib กัน XXE / billion laughs
# ถึงไฟล์ที่อ่านจะเป็น template ของเราเองกับไฟล์ที่ openpyxl เขียน ไม่ได้มาจากผู้ใช้ก็ตาม
from defusedxml import ElementTree as ET

NS_MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

# จับบล็อก extLst ที่อยู่ท้ายสุดของ <worksheet>
_EXTLST_RE = re.compile(r'<extLst>.*?</extLst>\s*</worksheet>\s*$', re.S)
# xr:uid เป็น GUID ของ revision history ที่ประกาศ prefix ไว้บน <worksheet> ของไฟล์เดิม
# ไฟล์ที่ openpyxl เขียนไม่ได้ประกาศ prefix xr ถ้าใส่ไปด้วยจะกลายเป็น xml ที่ parse ไม่ผ่าน
_XR_UID_RE = re.compile(r'\s+xr:uid="[^"]*"')

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exceltemplate')
TRIP_REPORT_TEMPLATE = os.path.join(TEMPLATE_DIR, 'trip_report_template_v12.xlsx')
# v12 = v11 ที่ขยายพื้นที่ข้อมูลจากแถว 6-3005 (3,000 เที่ยว) เป็น 6-6005 (6,000 เที่ยว)
# ถ้าจะขยายอีกต้องขยายทั้งสามอย่างพร้อมกัน ไม่งั้นยอดในหน้าสรุปจะขาดไปเงียบ ๆ :
#   1) แถวในชีต บันทึกรายเที่ยว   2) ช่วงที่สูตรทุกชีตอ้างถึง   3) EXPORT_DOC_MAX_TRIPS ใน views.py


def _sheet_xml_by_name(zf):
    """คืน dict {ชื่อ sheet : path ของไฟล์ xml ใน zip} เพราะชื่อไฟล์ sheetN.xml
    ของไฟล์ต้นฉบับกับไฟล์ที่ openpyxl เขียน ไม่จำเป็นต้องตรงกัน ต้องจับคู่ด้วยชื่อ sheet"""
    workbook = ET.fromstring(zf.read('xl/workbook.xml'))
    rels = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))

    target_by_rid = {rel.get('Id'): rel.get('Target') for rel in rels}

    mapping = {}
    for sheet in workbook.find('{%s}sheets' % NS_MAIN):
        target = target_by_rid.get(sheet.get('{%s}id' % NS_REL)) or ''
        target = target.lstrip('/')
        if not target.startswith('xl/'):
            target = 'xl/' + target
        mapping[sheet.get('name')] = target
    return mapping


def _extract_extlst(xml_text):
    match = _EXTLST_RE.search(xml_text)
    if not match:
        return None
    block = match.group(0)
    block = block[:block.rfind('</worksheet>')]
    return _XR_UID_RE.sub('', block)


def save_with_template_extensions(workbook, template_path):
    """save workbook ที่โหลดมาจาก template แล้วเอา dropdown (x14 data validation) กลับคืน
    คืนค่าเป็น bytes ของไฟล์ xlsx พร้อมส่งออก"""
    built = io.BytesIO()
    workbook.save(built)
    built.seek(0)

    with zipfile.ZipFile(template_path) as ztpl:
        template_sheets = _sheet_xml_by_name(ztpl)
        extras = {}
        for sheet_name, member in template_sheets.items():
            block = _extract_extlst(ztpl.read(member).decode('utf-8'))
            if block:
                extras[sheet_name] = block

    if not extras:
        built.seek(0)
        return built.read()

    result = io.BytesIO()
    with zipfile.ZipFile(built) as zin:
        built_sheets = _sheet_xml_by_name(zin)
        # path ของ sheet ในไฟล์ผลลัพธ์ -> บล็อก extLst ที่ต้องใส่กลับ
        block_by_member = {built_sheets[name]: block
                           for name, block in extras.items() if name in built_sheets}

        with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                block = block_by_member.get(item.filename)
                if block:
                    text = data.decode('utf-8')
                    if '<extLst>' not in text:
                        data = text.replace('</worksheet>', block + '</worksheet>').encode('utf-8')
                zout.writestr(item, data)

    return result.getvalue()
