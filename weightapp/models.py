from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q, F, CheckConstraint
from django.forms import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta, datetime

# Create your models here.
class BaseWeightType(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120)
    class Meta:
        db_table = 'base_weight_type'

    def __str__(self):
        return self.name

class BaseVatType(models.Model):
    base_vat_type_id = models.CharField(primary_key = True, max_length=120)
    base_vat_type_name = models.CharField(blank=True, null=True, max_length=255)
    base_vat_type_des = models.CharField(blank=True, null=True, max_length=255)
    
    class Meta:
        db_table = 'base_vat_type'

    def __str__(self):
        return self.base_vat_type_des
    
class BaseWeightStation(models.Model):
    id = models.CharField(primary_key = True, max_length=120)
    des = models.CharField(blank=True, null=True,max_length=120)
    weight_type = models.ForeignKey(BaseWeightType,on_delete=models.CASCADE, null = True)
    weight_id_min = models.IntegerField(blank = True, null = True, verbose_name="id น้อยสุดของตาชั่งนี้")
    weight_id_max = models.IntegerField(blank = True, null = True, verbose_name="id มากสุดของตาชั่งนี้")
    vat_type = models.ForeignKey(BaseVatType,on_delete=models.CASCADE, null = True, blank=True)

    class Meta:
        db_table = 'base_weight_station'
    
    def __str__(self):
        return self.id
    
class Weight(models.Model):
    weight_id = models.IntegerField(primary_key = True)#weight_id primary_key
    date = models.DateField()#วันที่
    date_in = models.DateField(blank=True, null=True)#วันที่ชั่งเข้า
    date_out = models.DateField(blank=True, null=True)#วันที่ชั่งออก
    time_in = models.TextField(blank=True, null=True)#เวลาชั่งเข้า
    time_out = models.TextField(blank=True, null=True)#เวลาชั่งออก
    ref_id = models.TextField(blank=True, null=True)#เลขที่ใบตัก
    doc_id = models.TextField(blank=True, null=True)#เลขที่เอกสาร
    car_registration_id = models.TextField(blank=True, null=True)#รหัสทะเบียนรถ
    car_registration_name = models.TextField(blank=True, null=True)#ทะเบียนรถ
    province = models.TextField(blank=True, null=True)#จังหวัด
    driver_id = models.TextField(blank=True, null=True)#รหัสคนขับ
    driver_name = models.TextField(blank=True, null=True)#คนขับ
    customer_id = models.TextField(blank=True, null=True)#รหัสลูกค้า
    customer_name = models.TextField(blank=True, null=True)#ลูกค้า
    site = models.TextField(blank=True, null=True)#หน้างาน
    mill_id = models.TextField(blank=True, null=True)#รหัสโรงโม่
    mill_name = models.TextField(blank=True, null=True)#โรงโม่
    stone_type = models.TextField(blank=True, null=True)#ชนิดหิน
    pay = models.TextField(blank=True, null=True)#จ่ายเงิน
    scale_id = models.TextField(blank=True, null=True)#รหัสผู้ชั่ง
    scale_name = models.TextField(blank=True, null=True)#ชื่อผู้ชั่ง
    scoop_id = models.TextField(blank=True, null=True)#รหัสผู้ตัก
    scoop_name = models.TextField(blank=True, null=True)#ชื่อผู้ตัก
    approve_id = models.TextField(blank=True, null=True)#รหัสผู้อนุมัติจ่าย
    approve_name = models.TextField(blank=True, null=True)#ชื่อผู้อนุมัติจ่าย
    vat_type = models.TextField(blank=True, null=True)#ชนิดvat
    stone_color = models.TextField(blank=True, null=True)#ประเภทหิน
    car_team = models.TextField(blank=True, null=True)#ทีม
    clean = models.TextField(blank=True, null=True)#ล้าง
    transport = models.TextField(blank=True, null=True)#ขนส่ง
    note = models.TextField(blank=True, null=True)#หมายเหตุ
    ship_cost = models.TextField(blank=True, null=True)#ค่าขนส่ง
    carry_type_name = models.TextField(blank=True, null=True)
    line_type = models.TextField(blank=True, null=True)
    bag_type = models.TextField(blank=True, null=True)#bag_type
    fertilizer = models.TextField(blank=True, null=True)#ชนิดปุ๋ย
    pack_weight = models.TextField(blank=True, null=True)#น้ำหนักบรรจุ
    price_per_ton = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)#price_per_ton
    vat = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    q = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#คิว
    amount = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#จำนวณเงิน
    amount_vat = models.DecimalField(blank=True, null=True, decimal_places=2 , max_digits=20)#จำนวนเงินสุทธิ
    weight_in = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)#weight_in
    weight_out = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)#weight_out
    weight_total = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)#weight_total
    oil_content = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    origin_weight = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)
    origin_q = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)
    freight_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#ค่าบรรทุก
    ton = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#จำนวนตัน
    sack = models.IntegerField(blank=True, null=True)#จำนวนกระสอบ
    price_up = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#ค่าขึ้น
    price_down = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#ค่าลง
    price_up_total = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#ค่าขึ้นรวม
    price_down_total = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#ค่าลงรวม
    freight_cost_total = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#ค่าบรรทุกรวม
    base_weight_station_name = models.ForeignKey(BaseWeightStation,on_delete=models.CASCADE, null = True)

    class Meta:
        db_table = 'weight'


class BaseLossType(models.Model):
    name = models.CharField(unique=True, blank=True, null=True, max_length=255)
    class Meta:
        db_table = 'base_loss_type'
        ordering = ["id"]

    def __str__(self):
        return self.name
    
class BaseLineType(models.Model):
    name = models.CharField(unique=True, blank=True, null=True, max_length=255)
    class Meta:
        db_table = 'base_line_type'

    def __str__(self):
        return self.name
    
class BaseMill(models.Model):
    id = models.CharField(primary_key = True, max_length=120)
    name = models.CharField(unique=True, blank=True, null=True, max_length=255)

    class Meta:
        db_table = 'base_mill'

    def __str__(self):
        return self.name
    
def setDurationTime(duration):
    result = None
    if duration is not None:
        if str(duration).startswith('0:'):
            _ , hours, minutes  = map(int, str(duration).split(':'))
        else:
            hours, minutes, _  = map(int, str(duration).split(':'))
        result = timedelta(hours=hours, minutes=minutes)

    return result

def decimalToTime(deci):
    result = None
    if deci is not None:
        hours, minutes = map(int, str(deci).split('.'))
        result = timedelta(hours=hours, minutes=minutes)
    return result

def calculatorDiffTime(start_time, end_time):
    difference = None
    if start_time and end_time:
        difference = end_time - start_time
    return difference

class Production(models.Model):
    mill = models.ForeignKey(BaseMill,on_delete=models.CASCADE, null = True, blank=True)
    line_type = models.ForeignKey(BaseLineType,on_delete=models.CASCADE, null = True, blank=True)

    created = models.DateField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันเวลาที่สร้างครั้งแรกอัตโนมัติ
    update = models.DateField(auto_now=True, verbose_name="วันที่อัพเดท") #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด

    goal = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#เป้าต่อวัน
    accumulated_goal = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#เป้าสะสม
    
    plan_start_time = models.DurationField(null = True, blank=True)#ชั่วโมงตามแผน (เริ่ม)
    plan_end_time = models.DurationField(null = True, blank=True)#ชั่วโมงตามแผน (สิ้นสุด)
    plan_time = models.DurationField(null = True, blank=True)#ชั่วโมงทำงาน plan_end_time - plan_start_time

    run_start_time = models.DurationField(null = True, blank=True)#ชั่วโมงเดินเครื่อง (เริ่ม)
    run_end_time = models.DurationField(null = True, blank=True)#ชั่วโมงเดินเครื่อง (สิ้นสุด)
    mile_run_start_time = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#ชั่วโมงเดินเครื่องเลขไมล์(เริ่ม)
    mile_run_end_time = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#ชั่วโมงเดินเครื่องเลขไมล์(สิ้นสุด)
    run_time = models.DurationField(null = True, blank=True)#ชั่วโมงเดินเครื่อง run_end_time - run_start_time

    total_loss_time = models.DurationField(null = True, blank=True)#รวมเวลาในการสูญเสีย
    actual_working_time = models.DurationField(null = True, blank=True)#ชั่วโมงการทำงานจริง

    production_volume = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#ยอดผลิต
    accumulated_production_volume = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#ยอดผลิตสะสม
    
    capacity_per_hour = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#กำลังการผลิตต่อชั่วโมง
    note = models.TextField(blank=True, null=True)#หมายเหตุ

    '''
    def clean(self):
        if self.plan_start_time > self.plan_end_time:
            raise forms.ValidationError(_('Start plan time should be before end'))
        if self.run_start_time > self.run_end_time:
            raise forms.ValidationError(_('Start run time should be before end'))
        return super().clean()    
    '''
    

    def save(self, *args, **kwargs):
        # Convert the timedelta to string and extract the hours and minutes
        self.plan_start_time = setDurationTime(self.plan_start_time)
        self.plan_end_time = setDurationTime(self.plan_end_time)
        self.run_start_time = setDurationTime(self.run_start_time)
        self.run_end_time = setDurationTime(self.run_end_time)
        self.plan_time = calculatorDiffTime(self.plan_start_time, self.plan_end_time)#ชั่วโมงทำงาน
        if self.run_start_time and self.run_end_time:
            self.run_time = calculatorDiffTime(self.run_start_time, self.run_end_time)#ชั่วโมงเดินเครื่อง
        elif self.mile_run_start_time and self.mile_run_end_time:
            self.run_time = decimalToTime(calculatorDiffTime(self.mile_run_start_time, self.mile_run_end_time))
            print("testttttttt" + str(self.run_time))
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'production'


class ProductionLossItem(models.Model):
    production = models.ForeignKey(Production,on_delete=models.CASCADE, null = True, blank=True)
    loss_type = models.ForeignKey(BaseLossType,on_delete=models.CASCADE, null = True, blank=True)
    loss_time = models.DurationField(null = True, blank=True)
    
    def save(self, *args, **kwargs):
        # Convert the timedelta to string and extract the hours and minutes
        self.loss_time = setDurationTime(self.loss_time)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'production_loss_item'


