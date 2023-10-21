from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q, F, CheckConstraint
from django.forms import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.models import Group, User
from django.db.models.signals import pre_save
from django.dispatch import receiver

class BaseWeightType(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120)
    class Meta:
        db_table = 'base_weight_type'

    def __str__(self):
        return self.name
    
class BaseCompany(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120, verbose_name="ชื่อบริษัท")
    code = models.CharField(blank=True, null=True, max_length=120, verbose_name="โค้ดบริษัท")
    class Meta:
        db_table = 'base_comp'
        verbose_name = 'บริษัท'
        verbose_name_plural = 'ข้อมูลบริษัท'

    def __str__(self):
        return self.code

class BaseMill(models.Model):
    mill_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสต้นทาง")
    mill_name = models.CharField(unique=True, blank=True, null=True, max_length=255, verbose_name="ชื่อต้นทาง")
    weight_type = models.ForeignKey(BaseWeightType,on_delete=models.CASCADE, null = True , verbose_name="ประเภทเครื่องชั่ง")
    v_stamp = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'base_mill'
        verbose_name = 'ต้นทาง'
        verbose_name_plural = 'ข้อมูลต้นทาง'

    def __str__(self):
        return self.mill_name

class BaseCarTeam(models.Model):
    car_team_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสทีม")
    car_team_name = models.CharField(unique=True, blank=True, null=True, max_length=255, verbose_name="ชื่อทีม")
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'base_car_team'
        verbose_name = 'ทีม'
        verbose_name_plural = 'ข้อมูลทีม'

    def __str__(self):
        return self.car_team_name
    
class BaseCar(models.Model):
    car_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสรถร่วม")
    car_name = models.CharField(blank=True, null=True, max_length=255, verbose_name="ชื่อรถร่วม")
    base_car_team = models.ForeignKey(BaseCarTeam,on_delete=models.CASCADE, null = True, verbose_name="ทีม")
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'base_car'
        verbose_name = 'รถร่วมและทีม'
        verbose_name_plural = 'ข้อมูลรถร่วมและทีม'

    def __str__(self):
        return self.car_id

class BaseVatType(models.Model):
    base_vat_type_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสชนิดvat")
    base_vat_type_name = models.CharField(blank=True, null=True, max_length=255, verbose_name="ชื่อชนิดvat")
    base_vat_type_des = models.CharField(blank=True, null=True, max_length=255, verbose_name="คำอธิบาย")
    
    class Meta:
        db_table = 'base_vat_type'
        verbose_name = 'ชนิดvat'
        verbose_name_plural = 'ข้อมูลชนิดvat'

    def __str__(self):
        return self.base_vat_type_name
    
class BaseJobType(models.Model):
    base_job_type_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสประเภทงานของลูกค้า")
    base_job_type_name = models.CharField(unique= True, blank=True, null=True, max_length=255, verbose_name="ชื่อประเภทงานของลูกค้า")
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'base_job_type'
        verbose_name = 'ประเภทงานของลูกค้า'
        verbose_name_plural = 'ข้อมูลประเภทงานของลูกค้า'
    
    def __str__(self):
        return self.base_job_type_id + " : " + self.base_job_type_name
    
class BaseStoneColor(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120)
    class Meta:
        db_table = 'base_stone_color'

    def __str__(self):
        return self.name
    
class BaseStoneType(models.Model):
    base_stone_type_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสหิน")
    base_stone_type_name = models.CharField(unique= True, blank=True, null=True, max_length=255, verbose_name="ชื่อหิน")
    type = models.CharField(blank=True, null=True, max_length=255, verbose_name="ประเภทหิน")
    cal_q = models.CharField(blank=True, null=True, max_length=120, verbose_name="ค่าคำนวณคิว")
    is_stone_estimate = models.BooleanField(default=False, verbose_name="ใช้ในการประมาณการณ์หิน")
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'base_stone_type'
        verbose_name = 'ชนิดหิน'
        verbose_name_plural = 'ข้อมูลชนิดหิน'

    def __str__(self):
        return self.base_stone_type_name
    
class BaseFertilizer(models.Model):
    fertilizer_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสปุ๋ย")
    fertilizer_name = models.CharField(blank=True, null=True, max_length=255, verbose_name="ชื่อปุ๋ย")

    class Meta:
        db_table = 'base_fertilizer'
        verbose_name = 'ปุ๋ย'
        verbose_name_plural = 'ข้อมูลปุ๋ย'

    def __str__(self):
        return self.fertilizer_id
    
class BaseCustomer(models.Model):
    customer_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสลูกค้า")
    customer_name = models.CharField(unique=True, blank=True, null=True, max_length=255, verbose_name="ชื่อลูกค้า")
    address = models.CharField(blank=True, null=True, max_length=255, verbose_name="ที่อยู่")
    send_to = models.CharField(blank=True, null=True, max_length=255, verbose_name="ส่งที่")
    customer_type = models.CharField(blank=True, null=True, max_length=255, verbose_name="ประเภทลูกค้า")
    base_vat_type = models.ForeignKey(BaseVatType,on_delete=models.CASCADE, null = True, blank=True, verbose_name="ชนิดvat")
    base_job_type = models.ForeignKey(BaseJobType,on_delete=models.CASCADE, null = True, blank=True, verbose_name="ประเภทงานของลูกค้า")
    weight_type = models.ForeignKey(BaseWeightType,on_delete=models.CASCADE, null = True, verbose_name="ชนิดเครื่องชั่ง")
    is_stone_estimate = models.BooleanField(default=False, verbose_name="ใช้ในการประมาณการณ์หิน")
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'base_customer'
        verbose_name = 'ลูกค้า'
        verbose_name_plural = 'ข้อมูลลูกค้า'

    def __str__(self):
        return self.customer_name

class BaseScoop(models.Model):
    scoop_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสผู้ตัก")
    scoop_name = models.CharField(unique=True, blank=True, null=True, max_length=255, verbose_name="ชื่อผู้ตัก")
    v_stamp = models.DateTimeField(auto_now=True)
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")
    
    class Meta:
        db_table = 'base_scoop'
        verbose_name = 'ผู้ตัก'
        verbose_name_plural = 'ข้อมูลผู้ตัก'

    def __str__(self):
        return self.scoop_name
       
class BaseCarRegistration(models.Model):
    car_registration_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสทะเบียนรถ")
    car_registration_name = models.CharField(unique=True, blank=True, null=True, max_length=255, verbose_name="ชื่อทะเบียนรถ")
    car_type = models.CharField(blank=True, null=True, max_length=255, verbose_name="ประเภทรถ")
    v_stamp = models.DateTimeField(auto_now=True)
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")
    
    class Meta:
        db_table = 'base_car_registration'
        verbose_name = 'ทะเบียนรถ'
        verbose_name_plural = 'ข้อมูลทะเบียนรถ'

    def __str__(self):
        return self.car_registration_name

class BaseDriver(models.Model):
    driver_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสผู้ขับ")
    driver_name = models.CharField(unique= True, blank=True, null=True, max_length=255, verbose_name="ชื่อผู้ขับ")
    v_stamp = models.DateTimeField(auto_now=True)
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")

    class Meta:
        db_table = 'base_driver'
        verbose_name = 'ผู้ขับ'
        verbose_name_plural = 'ข้อมูลผู้ขับ'

    def __str__(self):
        return self.driver_name
    
class BaseSite(models.Model):
    base_site_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสปลายทาง")
    base_site_name = models.CharField(unique= True, blank=True, null=True, max_length=255, verbose_name="ชื่อปลายทาง")
    weight_type = models.ForeignKey(BaseWeightType,on_delete=models.CASCADE, null = True , verbose_name="ประเภทเครื่องชั่ง")
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'base_site'
        verbose_name = 'ปลายทาง'
        verbose_name_plural = 'ข้อมูลปลายทาง'

    def __str__(self):
        return self.base_site_name
    
class BaseCustomerSite(models.Model):
    customer = models.ForeignKey(
        BaseCustomer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        to_field='customer_id',  # Specify the correct field here
        verbose_name="ลูกค้า"
    )
    site = models.ForeignKey(
        BaseSite,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        to_field='base_site_id',  # Specify the correct field here
        verbose_name="ปลายทาง"
    )
    v_stamp = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'base_customer_site'
        ordering=('id',)
        verbose_name = 'ลูกค้าและปลายทาง'
        verbose_name_plural = 'ข้อมูลลูกค้าและปลายทาง'
        unique_together = 'customer', 'site'

    def __str__(self):
        return str(self.customer)
    
class BaseCarryType(models.Model):
    base_carry_type_id = models.CharField(primary_key = True, max_length=120)
    base_carry_type_name = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        db_table = 'base_carry_type'

    def __str__(self):
        return self.base_carry_type_name
    
class BaseTransport(models.Model):
    base_transport_id = models.CharField(primary_key = True, max_length=120)
    base_transport_name = models.CharField(blank=True, null=True, max_length=255)
    base_carry_type = models.ForeignKey(BaseCarryType,on_delete=models.CASCADE, null = True, blank=True)

    class Meta:
        db_table = 'base_transport'

    def __str__(self):
        return self.base_transport_name

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
    date = models.DateField(blank=True, null=True)#วันที่
    date_in = models.DateField(blank=True, null=True)#วันที่ชั่งเข้า
    date_out = models.DateField(blank=True, null=True)#วันที่ชั่งออก
    time_in = models.TimeField(blank=True, null=True)#เวลาชั่งเข้า
    time_out = models.TimeField(blank=True, null=True)#เวลาชั่งออก
    ref_id = models.CharField(blank=True, null=True,max_length=255)#เลขที่ใบตัก
    doc_id =  models.CharField(blank=True, null=True,max_length=255)#เลขที่เอกสาร
    car_registration = models.ForeignKey(BaseCarRegistration,on_delete=models.CASCADE, related_name='weight_car_registration', blank=True, null = True) # iiiiiiiiiiiii รหัสทะเบียนรถ
    car_registration_name = models.CharField(blank=True, null=True,max_length=255)#ทะเบียนรถ
    province = models.CharField(blank=True, null=True,max_length=255)#จังหวัด
    driver = models.ForeignKey(BaseDriver,on_delete=models.CASCADE, related_name='weight_driver', blank=True, null = True) #รหัสคนขับ iiiiiiiiiiiii
    driver_name = models.CharField(blank=True, null=True,max_length=255)#คนขับ
    customer = models.ForeignKey(BaseCustomer,on_delete=models.CASCADE, related_name='weight_customer', blank=True, null = True)#รหัสลูกค้า iiiiiiiiiiiii
    customer_name = models.CharField(blank=True, null=True,max_length=255)#ลูกค้า
    site = models.ForeignKey(BaseSite ,on_delete=models.CASCADE, related_name='weight_site', blank=True, null = True) # iiiiiiiiiiiii
    site_name = models.CharField(blank=True, null=True,max_length=255)#หน้างาน
    mill = models.ForeignKey(BaseMill ,on_delete=models.CASCADE, related_name='weight_mill', blank=True, null = True)#รหัสโรงโม่ iiiiiiiiiiiii
    mill_name = models.CharField(blank=True, null=True,max_length=255)#โรงโม่
    stone_type = models.ForeignKey(BaseStoneType ,on_delete=models.CASCADE, related_name='weight_stone_type', blank=True, null = True)#รหัสหิน  iiiiiiiiiiiii  
    stone_type_name = models.CharField(blank=True, null=True,max_length=255)#ชนิดหิน
    pay = models.CharField(blank=True, null=True,max_length=255)#จ่ายเงิน
    scale_id = models.CharField(blank=True, null=True,max_length=255)#รหัสผู้ชั่ง
    scale_name = models.CharField(blank=True, null=True,max_length=255)#ชื่อผู้ชั่ง
    scoop = models.ForeignKey(BaseScoop ,on_delete=models.CASCADE, related_name='weight_scoop', blank=True, null = True)#รหัสผู้ตัก iiiiiiiiiiiii
    scoop_name = models.CharField(blank=True, null=True,max_length=255)#ชื่อผู้ตัก
    approve_id = models.CharField(blank=True, null=True,max_length=255)#รหัสผู้อนุมัติจ่าย
    approve_name = models.CharField(blank=True, null=True,max_length=255)#ชื่อผู้อนุมัติจ่าย
    vat_type = models.CharField(blank=True, null=True,max_length=255)#ชนิดvat
    stone_color = models.CharField(blank=True, null=True,max_length=255)#ประเภทหิน
    car_team = models.ForeignKey(BaseCarTeam ,on_delete=models.CASCADE, related_name='weight_car_team', blank=True, null = True)#รหัสทีม iiiiiiiiiiiii
    car_team_name = models.CharField(blank=True, null=True,max_length=255)#ทีม
    clean_type = models.CharField(blank=True, null=True,max_length=255)#ล้าง
    transport = models.CharField(blank=True, null=True,max_length=255)#ขนส่ง
    note = models.CharField(blank=True, null=True,max_length=255)#หมายเหตุ
    ship_cost = models.CharField(blank=True, null=True,max_length=255)#ค่าขนส่ง
    carry_type_name = models.CharField(blank=True, null=True,max_length=255)#รับเอง-ส่งให้
    line_type = models.CharField(blank=True, null=True,max_length=255)
    bag_type = models.CharField(blank=True, null=True,max_length=255)#bag_type
    '''
    fertilizer = models.ForeignKey(
        BaseFertilizer, 
        on_delete=models.CASCADE, 
        related_name='weight_fertilizer', 
        to_field='fertilizer_id',
        blank=True, 
        null=True
    )    
    '''
    fertilizer_name = models.CharField(blank=True, null=True,max_length=255)#ชนิดปุ๋ย
    pack_weight = models.CharField(blank=True, null=True,max_length=255)#น้ำหนักบรรจุ
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
    bws = models.ForeignKey(BaseWeightStation,on_delete=models.CASCADE, null = True)
    base_weight_station_name = models.CharField(blank=True, null=True,max_length=255)#lc.
    v_stamp = models.DateTimeField(auto_now=True)

    # export to express
    is_s = models.BooleanField(default=False, verbose_name="สถานะ non vat")#สถานะ non vat
    exp_bill = models.CharField(blank=True, null=True,max_length=255)#บิลขาย
    exp_change = models.CharField(blank=True, null=True,max_length=255)#ปรับปรุง
    exp_remission = models.CharField(blank=True, null=True,max_length=255)#ลดหนี้
    exp_note = models.CharField(blank=True, null=True,max_length=255)#หมายเหตุ
    exp_type = models.CharField(blank=True, null=True,max_length=255)#ประเภทชั่ง
    is_cancel = models.BooleanField(default=False, verbose_name="สถานะยกเลิก")#สถานะยกเลิก

    class Meta:
        db_table = 'weight'
        ordering = ["weight_id"]

class WeightHistory(models.Model):
    date = models.DateField(blank=True, null=True)#วันที่
    date_in = models.DateField(blank=True, null=True)#วันที่ชั่งเข้า
    date_out = models.DateField(blank=True, null=True)#วันที่ชั่งออก
    time_in = models.TimeField(blank=True, null=True)#เวลาชั่งเข้า
    time_out = models.TimeField(blank=True, null=True)#เวลาชั่งออก
    ref_id = models.CharField(blank=True, null=True,max_length=255)#เลขที่ใบตัก
    doc_id =  models.CharField(blank=True, null=True,max_length=255)#เลขที่เอกสาร
    car_registration = models.ForeignKey(BaseCarRegistration,on_delete=models.CASCADE, related_name='weight_history_car_registration', blank=True, null = True) # iiiiiiiiiiiii รหัสทะเบียนรถ
    car_registration_name = models.CharField(blank=True, null=True,max_length=255)#ทะเบียนรถ
    province = models.CharField(blank=True, null=True,max_length=255)#จังหวัด
    driver = models.ForeignKey(BaseDriver,on_delete=models.CASCADE, related_name='weight_history_driver', blank=True, null = True) #รหัสคนขับ iiiiiiiiiiiii
    driver_name = models.CharField(blank=True, null=True,max_length=255)#คนขับ
    customer = models.ForeignKey(BaseCustomer,on_delete=models.CASCADE, related_name='weight_history_customer', blank=True, null = True)#รหัสลูกค้า iiiiiiiiiiiii
    customer_name = models.CharField(blank=True, null=True,max_length=255)#ลูกค้า
    site = models.ForeignKey(BaseSite ,on_delete=models.CASCADE, related_name='weight_history_site', blank=True, null = True)
    site_name = models.CharField(blank=True, null=True,max_length=255)#หน้างาน
    mill = models.ForeignKey(BaseMill ,on_delete=models.CASCADE, related_name='weight_history_mill', blank=True, null = True)#รหัสโรงโม่ iiiiiiiiiiiii
    mill_name = models.CharField(blank=True, null=True,max_length=255)#โรงโม่
    stone_type = models.ForeignKey(BaseStoneType ,on_delete=models.CASCADE, related_name='weight_history_stone_type', blank=True, null = True)#รหัสหิน  iiiiiiiiiiiii
    stone_type_name = models.CharField(blank=True, null=True,max_length=255)#ชนิดหิน
    pay = models.CharField(blank=True, null=True,max_length=255)#จ่ายเงิน
    scale_id = models.CharField(blank=True, null=True,max_length=255)#รหัสผู้ชั่ง
    scale_name = models.CharField(blank=True, null=True,max_length=255)#ชื่อผู้ชั่ง
    scoop = models.ForeignKey(BaseScoop ,on_delete=models.CASCADE, related_name='weight_history_scoop', blank=True, null = True)#รหัสผู้ตัก iiiiiiiiiiiii
    scoop_name = models.CharField(blank=True, null=True,max_length=255)#ชื่อผู้ตัก
    approve_id = models.CharField(blank=True, null=True,max_length=255)#รหัสผู้อนุมัติจ่าย
    approve_name = models.CharField(blank=True, null=True,max_length=255)#ชื่อผู้อนุมัติจ่าย
    vat_type = models.CharField(blank=True, null=True,max_length=255)#ชนิดvat
    stone_color = models.CharField(blank=True, null=True,max_length=255)#ประเภทหิน
    car_team = models.ForeignKey(BaseCarTeam ,on_delete=models.CASCADE, related_name='weight_history_car_team', blank=True, null = True)#รหัสทีม iiiiiiiiiiiii
    car_team_name = models.CharField(blank=True, null=True,max_length=255)#ทีม
    clean_type = models.CharField(blank=True, null=True,max_length=255)#ล้าง
    transport = models.CharField(blank=True, null=True,max_length=255)#ขนส่ง
    note = models.CharField(blank=True, null=True,max_length=255)#หมายเหตุ
    ship_cost = models.CharField(blank=True, null=True,max_length=255)#ค่าขนส่ง
    carry_type_name = models.CharField(blank=True, null=True,max_length=255)
    line_type = models.CharField(blank=True, null=True,max_length=255)
    bag_type = models.CharField(blank=True, null=True,max_length=255)#bag_type
    '''
    fertilizer = models.ForeignKey(
        BaseFertilizer, 
        on_delete=models.CASCADE, 
        related_name='weight_history_fertilizer', 
        to_field='fertilizer_id',
        blank=True, 
        null=True
    )    
    '''

    fertilizer_name = models.CharField(blank=True, null=True,max_length=255)#ชนิดปุ๋ย
    pack_weight = models.CharField(blank=True, null=True,max_length=255)#น้ำหนักบรรจุ
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
    bws = models.ForeignKey(BaseWeightStation,on_delete=models.CASCADE, null = True)
    weight_table = models.ForeignKey(Weight,on_delete=models.CASCADE, null = True)
    update = models.DateTimeField(default=timezone.now)#เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    user_update = models.ForeignKey(User,on_delete=models.CASCADE,related_name='user_update', blank=True, null=True)
    weight_id = models.IntegerField(blank=True, null=True)
    base_weight_station_name = models.CharField(blank=True, null=True,max_length=255)#lc.
    v_stamp = models.DateTimeField(auto_now=True)
    
    # export to express
    is_s = models.BooleanField(default=False, verbose_name="สถานะ non vat")#สถานะ non vat
    exp_bill = models.CharField(blank=True, null=True,max_length=255)#บิลขาย
    exp_change = models.CharField(blank=True, null=True,max_length=255)#ปรับปรุง
    exp_remission = models.CharField(blank=True, null=True,max_length=255)#ลดหนี้
    exp_note = models.CharField(blank=True, null=True,max_length=255)#หมายเหตุ
    exp_type = models.CharField(blank=True, null=True,max_length=255)#ประเภทชั่ง
    is_cancel = models.BooleanField(default=False, verbose_name="สถานะยกเลิก")#สถานะยกเลิก

    class Meta:
        db_table = 'weight_history'
        ordering = ["-id"]
    
    def __str__(self):
        return str(self.weight_id)

@receiver(pre_save, sender=Weight)
def save_weight_history(sender, instance, **kwargs):
    if instance.pk:  # Only if the instance has already been saved (i.e., an update)
        try:
            old_weight = Weight.objects.get(pk=instance.pk)
            WeightHistory.objects.create(
                    date = old_weight.date,
                    date_in = old_weight.date_in,
                    date_out = old_weight.date_out,
                    time_in = old_weight.time_in,
                    time_out = old_weight.time_out,
                    ref_id = old_weight.ref_id,
                    doc_id =  old_weight.doc_id,
                    car_registration = old_weight.car_registration,
                    car_registration_name = old_weight.car_registration_name,
                    province = old_weight.province,
                    driver = old_weight.driver,
                    driver_name = old_weight.driver_name,
                    customer = old_weight.customer,
                    customer_name = old_weight.customer_name,
                    site = old_weight.site,
                    site_name = old_weight.site_name,
                    mill = old_weight.mill,
                    mill_name = old_weight.mill_name,
                    stone_type = old_weight.stone_type,
                    stone_type_name = old_weight.stone_type_name,
                    pay = old_weight.pay,
                    scale_id = old_weight.scale_id,
                    scale_name = old_weight.scale_name,
                    scoop = old_weight.scoop,
                    scoop_name = old_weight.scoop_name,
                    approve_id = old_weight.approve_id,
                    approve_name = old_weight.approve_name,
                    vat_type = old_weight.vat_type,
                    stone_color = old_weight.stone_color,
                    car_team = old_weight.car_team,
                    car_team_name = old_weight.car_team_name,
                    clean_type = old_weight.clean_type,
                    transport = old_weight.transport,
                    note = old_weight.note,
                    ship_cost = old_weight.ship_cost,
                    carry_type_name = old_weight.carry_type_name,
                    line_type = old_weight.line_type,
                    bag_type = old_weight.bag_type,
                    #fertilizer = old_weight.fertilizer,
                    fertilizer_name = old_weight.fertilizer_name,
                    pack_weight = old_weight.pack_weight,
                    price_per_ton = old_weight.price_per_ton,
                    vat = old_weight.vat,
                    q = old_weight.q,
                    amount = old_weight.amount,
                    amount_vat = old_weight.amount_vat,
                    weight_in = old_weight.weight_in,
                    weight_out = old_weight.weight_out,
                    weight_total = old_weight.weight_total,
                    oil_content = old_weight.oil_content,
                    origin_weight = old_weight.origin_weight,
                    origin_q = old_weight.origin_q,
                    freight_cost = old_weight.freight_cost,
                    ton = old_weight.ton,
                    sack = old_weight.sack,
                    price_up = old_weight.price_up,
                    price_down = old_weight.price_down,
                    price_up_total = old_weight.price_up_total,
                    price_down_total = old_weight.price_down_total,
                    freight_cost_total = old_weight.freight_cost_total,
                    bws = old_weight.bws,
                    weight_id = old_weight.pk,
                    weight_table = old_weight,
                    is_s = old_weight.is_s,
                    is_cancel = old_weight.is_cancel,
                    exp_bill = old_weight.exp_bill,
                    exp_change = old_weight.exp_change,
                    exp_remission = old_weight.exp_remission,
                    exp_note = old_weight.exp_note,
                    exp_type = old_weight.exp_type
            )
        except Weight.DoesNotExist:
            pass

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

    
class BaseTimeEstimate(models.Model):
    mill = models.ForeignKey(BaseMill,on_delete=models.CASCADE, null = True, blank=True)
    time_from = models.TimeField(null = True, blank=True)
    time_to = models.TimeField(null = True, blank=True)
    time_name = models.CharField(blank=True, null=True, max_length=120)

    class Meta:
        db_table = 'base_time_estimate'

    def __str__(self):
        return self.time_name
    
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
        minutes = minutes * 6
        result = timedelta(hours=hours, minutes=minutes)
    return result

def calculatorDiffTime(start_time, end_time):
    difference = None
    if start_time and end_time:
        difference = end_time - start_time
    return difference

#เก็บเป้าสะสมของตามเดือนนั้นๆ ตามโรงโม่และ line
class ProductionGoal(models.Model):
    date = models.DateField(default = timezone.now, verbose_name="วันที่ผลิต")
    accumulated_goal = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#เป้าสะสมของเดือนปีนั้นๆ
    mill = models.ForeignKey(BaseMill,on_delete=models.CASCADE, null = True, blank=True)
    line_type = models.ForeignKey(BaseLineType,on_delete=models.CASCADE, null = True, blank=True)

    class Meta:
        db_table = 'production_goal'

class Production(models.Model):
    mill = models.ForeignKey(BaseMill,on_delete=models.CASCADE, null = True, blank=True)
    line_type = models.ForeignKey(BaseLineType,on_delete=models.CASCADE, null = True, blank=True)

    created = models.DateField(default = timezone.now, verbose_name="วันที่ผลิต") #เก็บวันที่ผลิต
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

    pd_goal =  models.ForeignKey(ProductionGoal,on_delete=models.CASCADE, null = True, blank=True)
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


class StoneEstimate(models.Model):
    created = models.DateField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    mill = models.ForeignKey(BaseMill,on_delete=models.CASCADE, null = True, blank=True)
    
    class Meta:
        db_table = 'stone_estimate'

class StoneEstimateItem(models.Model):
    stone_type = models.ForeignKey(BaseStoneType,on_delete=models.CASCADE, null = True, blank=True)
    percent = models.IntegerField(blank=True, null=True)
    se = models.ForeignKey(StoneEstimate,on_delete=models.CASCADE, null = True, blank=True)
    
    class Meta:
        db_table = 'stone_estimate_item'

#USER PROFILE
class UserScale(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True, verbose_name="ผู้ใช้")
    scale_id = models.CharField(blank=True, null=True,max_length=255, verbose_name="รหัสผู้ชั่ง")#รหัสผู้ชั่ง
    scale_name = models.CharField(blank=True, null=True,max_length=255, verbose_name="ชื่อผู้ชั่ง")#ชื่อผู้ชั่ง

    class Meta:
        verbose_name = 'ผู้ชั่ง'
        verbose_name_plural = 'ข้อมูลผู้ชั่ง'
    
    def __str__(self):
        return self.scale_name