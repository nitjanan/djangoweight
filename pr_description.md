## 🎯 สรุปการทำงาน (Summary)
PR นี้ครอบคลุมการเพิ่มระบบ **International Freight Rate (การจัดการอัตราค่าขนส่งระหว่างประเทศ)** และฟีเจอร์การดึงรายงานสรุปรถส่งออกในรูปแบบไฟล์ **Excel** โดยเชื่อมโยงข้อมูลบิลเติมน้ำมันจริงจากระบบ Express รวมถึงเพิ่มความปลอดภัยและแก้ไขบั๊กจากการ Migration และ Admin ต่างๆ

## ✨ ฟีเจอร์ใหม่ (New Features)
- **International Freight Rate System:** 
  - เพิ่มระบบจัดการอัตราค่าขนส่งระหว่างประเทศ (Model, Views, Templates) พร้อมรองรับ CRUD
  - เพิ่มระบบ Versioning เพื่อเก็บประวัติการเปลี่ยนแปลงเรทราคา และ Approval Workflow ในการอนุมัติเรท
  - เพิ่มหน้าเช็ค Fuel Price History และ Daily Fuel Price แยกตามบริษัท
- **Excel Report & Express Integration:**
  - สร้างระบบ Export Document เป็น Excel โดยอัปเดตไปใช้ `trip_report_template_v12.xlsx`
  - นำข้อมูลบิลเติมน้ำมันจริงจากระบบ **Express** มาคำนวณราคาน้ำมันเฉลี่ยแบบถ่วงน้ำหนัก
  - กรอกข้อมูลลง Sheet Oil อัตโนมัติจากบิลเติมน้ำมันจริง
- **Database Model:** 
  - เพิ่ม Model `BaseCompanyMapBaseCustomer` พร้อมฟิลด์ `oi_soc_code` และนำไป Register ลงใน Admin แล้ว

## 🛠 การแก้ไขและปรับปรุง (Fixes & Improvements)
- **Excel Logic Changes:**
  - เปลี่ยนวิธีคิดค่าน้ำมันเป็นแบบ **รายเที่ยว** แทนการเฉลี่ยทั้งกลุ่ม และเพิ่มรายละเอียดขอบเขตแถวสูตร
  - แก้ไขให้ใน Sheet อัตราค่าขนส่ง มีการตัดแถวที่ไม่มีเที่ยวรองรับออก
  - จัดเรียงแถวอัตราค่าขนส่ง ให้แสดงแถวที่มีเที่ยววิ่งจริงขึ้นมาก่อนเสมอ
- **Security & Config:**
  - ย้ายข้อมูล Credential ของ `pg_db` ออกจาก `settings.py` ไปซ่อนไว้ใน `.env`
- **Bug Fixes:**
  - แก้ไขปัญหา Migration `0274/0276` ที่รันบนฐานข้อมูลเปล่าไม่ผ่าน (เนื่องจากเรื่อง Collation ของฐานข้อมูล)
  - แก้ไข Migration Graph พังหลักจาก Rebase ข้อมูลลง Main (`NodeNotFoundError`)
  - แก้ไขบั๊ก `admin.E040` ที่ทำให้ระบบพังหลักจาก Rebase (โดยการเติม `search_fields` ให้กับ `BaseCompanyAdmin`)
- **Cleanup:** 
  - เอาไฟล์ `trip_report_template_v11.xlsx` ออกจาก Git Tracking เพราะเป็นไฟล์เก่าเกิน Limit (3,000 เที่ยว) และกินพื้นที่ (Binary 1.1 MB)
