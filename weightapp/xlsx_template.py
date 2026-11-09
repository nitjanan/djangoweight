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
TRIP_REPORT_TEMPLATE = os.path.join(TEMPLATE_DIR, 'trip_report_template_v19.xlsx')
# v19 = v18 ที่เปลี่ยนเป็นคิดค่าขนส่งรายเที่ยวจากราคาน้ำมันวันที่วิ่ง (แทนราคาเฉลี่ยรายเดือน) ทำใน Excel จริง
#   บันทึกรายเที่ยว : แทรก N ราคาน้ำมันวันที่วิ่ง (ระบบเติม ว่างได้) / O อัตรา / P ค่าขนส่ง = M x O
#     แผงตรวจเลื่อนเป็น Q-R (+ R12 เที่ยวที่ยังไม่มีราคาน้ำมัน) คอลัมน์ช่วยเลื่อนเป็น T-AD
#     AE แถวอัตราของเที่ยว / AF payKey = accKey + อัตรา (หน้าสรุปจ่ายแยกบรรทัดตามอัตรา)
#   อัตราค่าขนส่ง : ลบ J ราคาเฉลี่ย / L ส่วนปรับ / M อัตราสุทธิ เหลือ G H I + J ปรับ / K คีย์ / L หมายเหตุ
#   สรุปจ่ายรถร่วม : 1 บรรทัด = payKey อัตราอ่านจาก O ของเที่ยวแรก รายได้ = Σ P
#   สรุปเหมือง : อัตราแถวทีม = Σ ค่าขนส่ง ÷ Σ ตันจ่าย (เที่ยวในกลุ่มอาจคนละอัตรา)
# v18 =v17 ที่ปรับหัวตารางหน้าสรุปให้เหมือนไฟล์บัญชีเดิม (ส่งออก ด.5-69) ทำใน Excel จริงทั้งหมด
#   สรุปจ่ายรถร่วม : ซ่อน G (อัตราตามสัญญา) H (ส่วนปรับน้ำมัน) ไม่ลบ เพราะแถบตรวจ BF อ้างตำแหน่งอยู่
#     I (อัตราสุทธิ) ใช้หัว "อัตรา ค่าขนส่ง (บาท/ตัน)" คู่กับ J "(บาท/กม.)"
#   สรุปเหมือง : แทรก I-J ใต้หัวใหญ่ "อัตราค่าขนส่ง" (บาท/ตัน) / (บาท/กม.) หัวตารางเป็น 2 แถว (7-8)
#     ข้อมูลเลื่อนเป็นแถว 9-708 แถบตัวกรอง/ตรวจเลื่อนจาก I ไป K (K3 K5 K7 / K11 / K13 / K15)
#     แถวทีม = อัตราของทีมนั้น / แถวชนิดหิน = รายได้รวม ÷ ตันรวม  (คอลัมน์ช่วย AK-AM)
# v17 =v16 ที่เปลี่ยนสูตรค่าขนส่ง (issue #125) ทำใน Excel จริงทั้งหมด
#   ลบคอลัมน์ช่วงราคาน้ำมันฐานของเส้นทาง (I / V / W / X) และ J ค่าขนส่ง ณ ราคาน้ำมันฐาน ของชีตอัตรา
#   แทรก I = ขอบบนของน้ำมันฐานวันทำสัญญา (H = ขอบล่าง) เพราะสัญญาตกลงน้ำมันฐานเป็นช่วงได้
#   ส่วนปรับ L : ราคาเฉลี่ย J อยู่ในช่วง H ถึง I = 0 / ต่ำกว่า H = (J − H) × K / สูงกว่า I = (J − I) × K
#   อัตราสุทธิ M = ตามสัญญา G + L
#   แถวที่ไม่มีค่าสัญญา (G ว่าง) M = 0 ไม่ใช่ "" เพราะหน้าสรุปเอา M ไปคูณ ได้ "" แล้วยอดรวมเป็น #VALUE!
#   หน้าสรุปจ่ายรถร่วม ช่อง AT (หัว G "อัตราตามสัญญา") ชี้ไป G ของชีตอัตรา แทน J เดิม
#   ส่วนปรับ (BC) ชี้ L / อัตราสุทธิ (BD) ชี้ M / คีย์ชี้ N
# v16 = v15 ที่ขยายพื้นที่ข้อมูลจากแถว 6-6005 (6,000 เที่ยว) เป็น 6-10005 (10,000 เที่ยว)
#   ทำใน Excel จริง : แทรก 4,000 แถวที่แถว 6005 (แถวสุดท้ายของช่วง) แล้วก๊อปแถว 6004 ลงไป
#   Excel ขยายการอ้างอิง $6:$6005 ทุกชีตเป็น $6:$10005 ให้เอง รวม dropdown x14 / autofilter / print area
# v15 = v14 ที่แทรก 2 คอลัมน์กลาง sheet อัตราค่าขนส่ง ด้วยการสั่ง Insert ใน Excel จริง
#   G ค่าขนส่งตามสัญญา (แสดงผล)   H น้ำมันฐานวันทำสัญญา (ใหม่ แสดงผล)
#   I ช่วงราคาฐานแบบข้อความ (เดิม H)   J ค่าขนส่ง ณ ราคาน้ำมันฐาน = ค่าขนส่งในใบราคา (ใหม่ ตัวตั้งที่ใช้คิด)
#   อัตราสุทธิ N = ROUND(J + ส่วนปรับ M, 2)  (เดิมคิดจาก G)
#   ที่เหลือเลื่อนขวา 2 ช่อง : ขอบบน V / ส่วนต่าง W / ขอบล่าง X / หมายเหตุ P
#   sheet สรุปจ่ายรถร่วม ช่อง AT (หัว G "อัตรา ณ น้ำมันฐาน") ชี้ไป J แทน G
#   เพื่อให้ อัตรา ณ น้ำมันฐาน + ส่วนปรับ = อัตราสุทธิ และช่องตรวจ BF4 (นับแถวที่ G = 0) นับถูก
# Excel เลื่อนการอ้างอิงข้ามชีต 2,700 สูตรกับ dropdown x14 16 ตัวให้เองตอนแทรก
# ถ้าจะแทรกคอลัมน์อีก ต้องทำใน Excel แบบนี้ ห้ามทำด้วย openpyxl (ไม่เลื่อนสูตรให้)
# v14 = v13 ที่เลิกคิดส่วนปรับน้ำมันเป็นขั้น กลับไปคิดทุกบาททุกสตางค์
# ลบคอลัมน์ T (ขั้นการปรับน้ำมัน) ของ v13 ทิ้ง ที่เหลือเลื่อนมาชิดซ้าย 1 ช่อง
#   H ช่วงราคาฐานแบบข้อความ "31.00 - 31.99" (ระบบเติม) แสดงผลเท่านั้น
#   T ราคาน้ำมันฐานขอบบน (ระบบเติม)
#   U ส่วนต่างที่ใช้คิด (สูตร) อยู่ระหว่าง V ถึง T = 0 หลุดขอบไหนวัดจากขอบนั้น
#   V ราคาน้ำมันฐานขอบล่าง (ระบบเติม)
#   K = ROUND(U * J, 2) ส่วนต่างเท่าไหร่ปรับเท่านั้น
# v14 เพิ่มคอลัมน์ต่อท้ายที่ T เพื่อไม่ต้องเลื่อนสูตรข้ามชีต (v15 เปลี่ยนมาแทรกกลางด้วย Excel)
# v13 = v12 ที่เปลี่ยนส่วนปรับน้ำมันมาคิดจากช่วงราคาฐาน (ขอบล่าง-ขอบบน) และตัดเป็นขั้น
# ขั้นการปรับถูกยกเลิกใน v14 แต่ช่วงราคาฐานยังอยู่
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
