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
import datetime
import hashlib
import base64
from django.apps import apps

def hash_password_sha1(password):
    sha1_bytes = hashlib.sha1(password.encode('ascii')).digest()
    return base64.b64encode(sha1_bytes).decode('ascii')

def default_userscale_permission():
    return hash_password_sha1('weight')

def get_first_name(self):
    return self.first_name
User.add_to_class("__str__", get_first_name)

class BaseVisible(models.Model):
    name = models.CharField(max_length=255,unique=True, verbose_name="ชื่อแท็บการใช้งาน")
    step = models.IntegerField(blank = True, null = True, verbose_name="ลำดับแท็ปการใช้งาน")

    class Meta:
        db_table = 'base_visible'
        ordering=('id',)
        verbose_name = 'แท็บการใช้งาน'
        verbose_name_plural = 'ข้อมูลแท็บการใช้งาน'
    
    def __str__(self):
        return str(self.name)

class BaseBusiness(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120, verbose_name="ชื่อประเภทธุรกิจ")
    class Meta:
        db_table = 'base_biz'
        verbose_name = 'ประเภทธุรกิจ'
        verbose_name_plural = 'ข้อมูลประเภทธุรกิจ'

    def __str__(self):
        return self.name
    
class BaseCompany(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120, verbose_name="ชื่อบริษัท")
    code = models.CharField(blank=True, null=True, max_length=120, verbose_name="โค้ดบริษัท")
    biz = models.ForeignKey(BaseBusiness, on_delete=models.CASCADE, blank = True, null = True, verbose_name="ประเภทธุรกิจ")
    step = models.IntegerField(blank = True, null = True, verbose_name="ลำดับแท็ปบริษัท")

    class Meta:
        db_table = 'base_comp'
        verbose_name = 'บริษัท'
        verbose_name_plural = 'ข้อมูลบริษัท'

    def __str__(self):
        return self.code
    
#เก็บสถานะตรวจสอบแล้ว weight by date
class ApproveWeight(models.Model):
    company = models.ForeignKey(BaseCompany, on_delete=models.CASCADE, blank = True, null = True, verbose_name="บริษัท")
    date = models.DateField(default = timezone.now, verbose_name="รายการชั่งวันที่") #เก็บรายการชั่งวันที่
    update = models.DateTimeField(default=timezone.now)#เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    is_approve = models.BooleanField(default=False, verbose_name="สถานะการตวจสอบ") #เก็บสถานะการตวจสอบ

    class Meta:
        db_table = 'approve_weight'
        verbose_name = 'ยืนยันการตรวจสอบรายการชั่ง'
        verbose_name_plural = 'ข้อมูลยืนยันการตรวจสอบรายการชั่ง'

SYMBOL_CHOICES = (
    ('+','+'),
    ('-','-'),
)

class BaseStockSource(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120, verbose_name="ชื่อที่มาของ stock")
    symbol = models.CharField(choices = SYMBOL_CHOICES, blank=True, null=True, max_length=120, verbose_name="เครื่องหมาย (+ หรือ -)")
    step = models.IntegerField(blank = True, null = True, verbose_name="ลำดับ")

    class Meta:
        db_table = 'base_stock_source'
        verbose_name = 'ที่มาของ stock'
        verbose_name_plural = 'ข้อมูลที่มาของ stock'

    def __str__(self):
        return self.name
    
class BaseMillSource(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120, verbose_name="ชื่อที่มาของต้นทาง")

    class Meta:
        db_table = 'base_mill_source'
        verbose_name = 'ที่มาของต้นทาง'
        verbose_name_plural = 'ข้อมูลที่มาของต้นทาง'

    def __str__(self):
        return self.name

#USER PROFILE
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True, verbose_name="ผู้ใช้")
    visible = models.ManyToManyField(BaseVisible,verbose_name="การมองเห็นแท็ปการใช้งาน")
    company = models.ManyToManyField(BaseCompany,verbose_name="การมองเห็นแท็ปบริษัท")

    class Meta:
        verbose_name = 'ผู้ใช้และตำแหน่งงาน'
        verbose_name_plural = 'ข้อมูลผู้ใช้และตำแหน่งงาน'
        
    def __str__(self):
        return self.user.username
    
class BaseWeightType(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120)
    class Meta:
        db_table = 'base_weight_type'

    def __str__(self):
        return self.name

class BaseMill(models.Model):
    mill_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสต้นทาง")
    mill_name = models.CharField(unique=True, blank=True, null=True, max_length=255, verbose_name="ชื่อต้นทาง")
    weight_type = models.ForeignKey(BaseWeightType,on_delete=models.CASCADE, null = True , verbose_name="ประเภทเครื่องชั่ง")
    v_stamp = models.DateTimeField(auto_now=True)
    m_comp = models.ForeignKey(BaseCompany, on_delete=models.CASCADE, blank = True, null = True , verbose_name="โรงโม่ของบริษัท (ต้นทาง)")
    step = models.IntegerField(blank = True, null = True, verbose_name="ลำดับโรงโม่ของบริษัท (ต้นทาง)")
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    mill_source = models.ForeignKey(BaseMillSource, on_delete=models.CASCADE, blank = True, null = True , verbose_name="ที่มาของต้นทาง")

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
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    oil_customer_id = models.CharField(unique=True, blank=True, null=True, max_length=120, verbose_name="รหัสลูกค้าน้ำมัน") #รหัสลูกค้าน้ำมัน
    
    class Meta:
        db_table = 'base_car_team'
        verbose_name = 'ทีม'
        verbose_name_plural = 'ข้อมูลทีม'

    def __str__(self):
        return self.car_team_id + " : " + self.car_team_name
    
class BaseCar(models.Model):
    car_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสรถร่วม")
    car_name = models.CharField(blank=True, null=True, max_length=255, verbose_name="ชื่อรถร่วม")
    base_car_team = models.ForeignKey(BaseCarTeam,on_delete=models.CASCADE, null = True, verbose_name="ทีม")
    v_stamp = models.DateTimeField(auto_now=True)
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    
    class Meta:
        db_table = 'base_car'
        verbose_name = 'รถร่วมและทีม'
        verbose_name_plural = 'ข้อมูลรถร่วมและทีม'
        unique_together = 'car_name', 'base_car_team'

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
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    
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
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    inactive = models.BooleanField(default=False, verbose_name="ปิดการใช้งาน")
    
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
    is_disable = models.BooleanField(default=False, verbose_name="ปิดการใช้งาน")
    is_port_stock = models.BooleanField(default=False, verbose_name="ใช้ใน stock หินท่าเรือ")
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    
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
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    
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
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    
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
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง

    class Meta:
        db_table = 'base_driver'
        verbose_name = 'ผู้ขับ'
        verbose_name_plural = 'ข้อมูลผู้ขับ'

    def __str__(self):
        return self.driver_name
    
class BaseSiteStore(models.Model):
    name = models.CharField(blank=True, null=True, max_length=120, verbose_name="การจัดเก็บของปลายทาง")

    class Meta:
        db_table = 'base_site_store'
        verbose_name = 'การจัดเก็บของปลายทาง'
        verbose_name_plural = 'ข้อมูลการจัดเก็บของปลายทาง'

    def __str__(self):
        return self.name

class BaseSite(models.Model):
    base_site_id = models.CharField(primary_key = True, max_length=120, verbose_name="รหัสปลายทาง")
    base_site_name = models.CharField(unique= True, blank=True, null=True, max_length=255, verbose_name="ชื่อปลายทาง")
    weight_type = models.ForeignKey(BaseWeightType,on_delete=models.CASCADE, null = True , verbose_name="ประเภทเครื่องชั่ง")
    v_stamp = models.DateTimeField(auto_now=True)
    s_comp = models.ForeignKey(BaseCompany, on_delete=models.CASCADE, blank = True, null = True , verbose_name="โรงโม่ของบริษัท (ปลายทาง)")
    step = models.IntegerField(blank = True, null = True, verbose_name="ลำดับโรงโม่ของบริษัท (ปลายทาง)")
    target = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10 , verbose_name="กำลังการผลิต (Target)")
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    store = models.ForeignKey(BaseSiteStore, on_delete=models.CASCADE, blank=True, null = True, verbose_name="การจัดเก็บ")
    
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
    user_created = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True, verbose_name="ผู้สร้าง")#เก็บผู้สร้าง
    created = models.DateTimeField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง

    class Meta:
        db_table = 'base_customer_site'
        ordering=('id',)
        verbose_name = 'ลูกค้าและปลายทาง'
        verbose_name_plural = 'ข้อมูลลูกค้าและปลายทาง'
        unique_together = 'customer', 'site'

    def __str__(self):
        return str(self.customer)
    
#ผูกผู้รับเหมากับบริษัท (ออกรายงานผลิตแยกผู้รับเหมาและชนิดหินเท่านั้น)    
class BaseSEC(models.Model):
    customer = models.ForeignKey(
        BaseCustomer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="ผู้รับเหมา"
    )
    company = models.ManyToManyField(
        BaseCompany,
        null=True,
        blank=True,
        verbose_name="บริษัท"
    )

    class Meta:
        db_table = 'base_SEC'
        ordering=('id',)
        verbose_name = 'ผู้รับเหมาและบริษัท'
        verbose_name_plural = 'ข้อมูลผู้รับเหมาและบริษัท'

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
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True, blank=True)

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
    stone_desc = models.CharField(blank=True, null=True,max_length=255)
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
    apw = models.ForeignKey(ApproveWeight, on_delete=models.CASCADE, blank=True, null = True) #ไม่ใช้แล้ว 08-05-2025 ใช้ is_apw แทน
    is_apw = models.BooleanField(default=False, verbose_name="สถานะตรวจสอบรายการชั่งแล้ว")#สถานะตรวจสอบรายการชั่งแล้ว

    #คำนวณราคาน้ำมัน
    oil_cost = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=10)
    oil_sell = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=10)
    #อ้างอิงใบส่งของ
    do_doc_no = models.CharField(blank=True, null=True,max_length=120)

    class Meta:
        db_table = 'weight'
        ordering = ["weight_id"]
        indexes = [
            # หน้า export เอกสารกรองด้วย carry_type_name + bws_id + ช่วงวันที่ ทุกครั้ง
            # ไม่มี index ชุดนี้ MySQL จะ full scan ทั้งตาราง (ล้านแถว) ทุก query
            models.Index(fields=['carry_type_name', 'date', 'bws_id'],
                         name='weight_carry_date_bws_idx'),
        ]

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
    stone_desc = models.CharField(blank=True, null=True,max_length=255)
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

    #อ้างอิงใบส่งของ
    do_doc_no = models.CharField(blank=True, null=True,max_length=120)

    class Meta:
        db_table = 'weight_history'
        ordering = ["-id"]
    
    def __str__(self):
        return str(self.weight_id)

@receiver(pre_save, sender=Weight)
def save_weight_history(sender, instance, **kwargs):
    #24/04/2025 ถ้า weight มาจาก Import ให้ใส่ user_update = 1 (นิจนันท์)
    tmp_user_update = None
    if hasattr(instance, '_from_import') and instance._from_import:
        tmp_user_update = 1

    if instance.pk:  # Only if the instance has already been saved (i.e., an update)
        try:
            old_weight = Weight.objects.get(pk=instance.pk)
            tmp_note = None

            #ถ้ารหัสกับชื่อ local และ center ให้เก็บ error 03/03/2025
            if old_weight.mill:
                mill = BaseMill.objects.get(mill_id = old_weight.mill.mill_id)
                center_mill = mill.mill_id + mill.mill_name #รหัสและชื่อบนหน้าเว็บ
                local_mill = old_weight.mill.mill_id + old_weight.mill_name #รหัสและชื่อจากตาชั่ง
                if local_mill != center_mill:
                    tmp_note = "error***" + str(old_weight.mill.mill_id) + str(old_weight.mill_name)

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
                    stone_desc = old_weight.stone_desc,
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
                    exp_note = tmp_note, #ถ้ารหัสกับชื่อ local และ center ให้เก็บ error 03/03/2025
                    exp_type = old_weight.exp_type,
                    user_update_id = tmp_user_update,
                    do_doc_no = old_weight.do_doc_no,
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
    
class BaseMachineType(models.Model):
    # M = เครื่องจักรหลัก, S = เครื่องจักรรอง ไว้แสดงข้อมูลเท่านั้น
    KIND_CHOICES = [
        ('M', 'main'),
        ('S', 'second'),
    ]
        
    name = models.CharField(unique=True, blank=True, null=True, max_length=255, verbose_name="ชื่อ")
    kind = models.CharField(blank=True, null=True, max_length=1, choices=KIND_CHOICES, verbose_name="ประเภทเครื่องจักร")

    class Meta:
        db_table = 'base_machine_type'
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
    site = models.ForeignKey(BaseSite,on_delete=models.CASCADE, null = True, blank=True)
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

''' อันเก่าคำนวนเวลาผิด
def decimalToTime(deci):
    result = None
    if deci is not None:
        hours, minutes = map(int, str(deci).split('.'))
        minutes = minutes * 6
        result = timedelta(hours=hours, minutes=minutes)
    return result
'''

def decimal_to_time(decimal_hours):
    if decimal_hours is not None:
        total_seconds = float(decimal_hours) * 3600
        
        time_delta = timedelta(seconds = total_seconds)
    return time_delta

def calculatorDiffTime(start_time, end_time):
    difference = None
    if start_time and end_time:
        difference = end_time - start_time
    return difference

#เก็บเป้าสะสมของตามเดือนนั้นๆ ตามโรงโม่และ line
class ProductionGoal(models.Model):
    date = models.DateField(default = timezone.now, verbose_name="วันที่ผลิต")
    accumulated_goal = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#เป้าสะสมของเดือนปีนั้นๆ
    line_type = models.ForeignKey(BaseLineType,on_delete=models.CASCADE, null = True, blank=True)
    site = models.ForeignKey(BaseSite,on_delete=models.CASCADE, null = True, blank=True, verbose_name="ปลายทาง")
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")

    class Meta:
        db_table = 'production_goal'

class Production(models.Model):
    site = models.ForeignKey(BaseSite,on_delete=models.CASCADE, null = True, blank=True, verbose_name="ปลายทาง")
    
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

    actual_start_time = models.DurationField(null = True, blank=True)#กำหนดจริง (เริ่ม)
    actual_end_time = models.DurationField(null = True, blank=True)#กำหนดจริง (สิ้นสุด)
    actual_time = models.DurationField(null = True, blank=True)#กำหนดจริง actual_start_time - actual_end_time

    total_loss_time = models.DurationField(null = True, blank=True)#รวมเวลาในการสูญเสีย
    actual_working_time = models.DurationField(null = True, blank=True)#ชั่วโมงการทำงานจริง

    uncontrol_time = models.DurationField(null = True, blank=True)#รวมเวลาในการสูญเสีย only uncontrol

    production_volume = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#ยอดผลิต
    accumulated_production_volume = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)#ยอดผลิตสะสม
    
    capacity_per_hour = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10)#กำลังการผลิตต่อชั่วโมง
    note = models.TextField(blank=True, null=True)#หมายเหตุ

    pd_goal =  models.ForeignKey(ProductionGoal,on_delete=models.CASCADE, null = True, blank=True)
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")
    
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

        self.actual_start_time = setDurationTime(self.actual_start_time)
        self.actual_end_time = setDurationTime(self.actual_end_time)

        self.plan_time = calculatorDiffTime(self.plan_start_time, self.plan_end_time)#ชั่วโมงทำงาน
        self.actual_time = calculatorDiffTime(self.actual_start_time, self.actual_end_time)#กำหนดจริง
        if self.run_start_time and self.run_end_time:
            self.run_time = calculatorDiffTime(self.run_start_time, self.run_end_time)#ชั่วโมงเดินเครื่อง
        elif self.mile_run_start_time and self.mile_run_end_time:
            self.run_time = decimal_to_time(calculatorDiffTime(self.mile_run_start_time, self.mile_run_end_time))
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'production'


class ProductionLossItem(models.Model):
    production = models.ForeignKey(Production,on_delete=models.CASCADE, null = True, blank=True)
    loss_type = models.ForeignKey(BaseLossType,on_delete=models.CASCADE, null = True, blank=True)
    mc_type = models.ForeignKey(BaseMachineType,on_delete=models.CASCADE, null = True, blank=True)
    loss_time = models.DurationField(null = True, blank=True)
    
    def save(self, *args, **kwargs):
        #แปลงแค่ตอน create
        if self.pk is not None:
            old_instance = ProductionLossItem.objects.get(pk=self.pk)
            if self.loss_time != old_instance.loss_time:
                self.loss_time = setDurationTime(self.loss_time)
        else:
            self.loss_time = setDurationTime(self.loss_time)

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'production_loss_item'

class ProductionMachineItem(models.Model):
    production = models.ForeignKey(Production,on_delete=models.CASCADE, null = True, blank=True)
    mc_type = models.ForeignKey(BaseMachineType,on_delete=models.CASCADE, null = True, blank=True)
    mile_start = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)
    mile_end = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=20)
    diff_time = models.DurationField(null = True, blank=True)

    def save(self, *args, **kwargs):
        if self.mile_start and self.mile_end:
            self.diff_time = decimal_to_time(calculatorDiffTime(self.mile_start, self.mile_end))
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'production_machine_item'

#stock
class Stock(models.Model):
    created = models.DateField(default = timezone.now, verbose_name="วันที่ผลิต") #เก็บวันที่ stock
    update = models.DateField(auto_now=True, verbose_name="วันที่อัพเดท") #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")

    class Meta:
        db_table = 'stock'
    
    def __str__(self):
        return str(self.id)

#ชนิดหินและจำนวนหินทั้งหมดใน stock
class StockStone(models.Model):
    stone = models.ForeignKey(BaseStoneType, on_delete=models.CASCADE, null=True, blank=True, max_length=120, verbose_name="ชนิดหิน", to_field='base_stone_type_id')
    total = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10 , verbose_name="รวมทั้งหมด")
    stk = models.ForeignKey(Stock, on_delete=models.CASCADE,null=True, blank=True, verbose_name="stock")
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

    class Meta:
        db_table = 'stock_stone'
    
    def __str__(self):
        return str(self.id)

#ที่มาของ stock และจำนวนหินใน stock
class StockStoneItem(models.Model):
    source = models.ForeignKey(BaseStockSource, on_delete=models.CASCADE,null=True, blank=True, verbose_name="ที่มาของ stock")
    quantity = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10 , verbose_name="จำนวน stock", default=0.00)
    ssn = models.ForeignKey(StockStone, on_delete=models.CASCADE,null=True, blank=True, verbose_name="stock stone")

    class Meta:
        db_table = 'stock_stone_item'
        
    def __str__(self):
        return str(self.id)

class StoneEstimate(models.Model):
    created = models.DateField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    site = models.ForeignKey(BaseSite,on_delete=models.CASCADE, null = True, blank=True)
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")
    topup = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="top up ไม่ผ่านตาชั่ง", default=0.000)
    other = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="จากโรงโม่อื่น", default=0.000)
    scale = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="จากตาชั่ง", default=0.000)
    total =  models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="รวม", default=0.000)
    is_pass = models.BooleanField(default=False, verbose_name="สถานะการส่งไปโม่ต่อ") #เก็บสถานะการส่งไปโม่ต่อ
    
    class Meta:
        db_table = 'stone_estimate'

class StoneEstimateItem(models.Model):
    stone_type = models.ForeignKey(BaseStoneType,on_delete=models.CASCADE, null = True, blank=True)
    percent = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=8, default=0.0000 , verbose_name="เปอร์เซ็นต์")
    qty = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="จำนวนที่ได้ (ตัน)")
    site_id = models.CharField(blank=True, null=True, max_length=120, verbose_name="ส่งไปต่อ (รหัสปลายทาง) ที่แรก")
    qty_site = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="ส่งไปต่อ (ตัน) ที่แรก")
    nd_site_id = models.CharField(blank=True, null=True, max_length=120, verbose_name="ส่งไปต่อ (รหัสปลายทาง) ที่สอง")
    nd_qty_site = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="ส่งไปต่อ (ตัน) ที่สอง")
    total = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10 , verbose_name="sum estimate by stone")
    se = models.ForeignKey(StoneEstimate,on_delete=models.CASCADE, null = True, blank=True)
    
    class Meta:
        db_table = 'stone_estimate_item'

#USER PROFILE
class UserScale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True, verbose_name="ผู้ใช้")
    scale_id = models.CharField(blank=True, null=True,max_length=255, verbose_name="รหัสผู้ชั่ง")#รหัสผู้ชั่ง
    scale_name = models.CharField(blank=True, null=True,max_length=255, verbose_name="ชื่อผู้ชั่ง")#ชื่อผู้ชั่ง
    password = models.CharField(blank=True, null=True,max_length=255, verbose_name="รหัสผ่าน")#รหัสผ่าน (เก็บแบบ hash)
    v_stamp = models.DateTimeField(auto_now=True)

    PERMISSION_ADMIN = 'admin'
    PERMISSION_EDIT_WEIGHT = 'edit_weight'
    PERMISSION_SALE = 'sale'
    PERMISSION_ADD_SETTING = 'add_setting'
    PERMISSION_WEIGHT = 'weight'
    PERMISSION_CHOICES = [
        (PERMISSION_ADMIN, 'admin'),
        (PERMISSION_EDIT_WEIGHT, 'edit_weight'),
        (PERMISSION_SALE, 'sale'),
        (PERMISSION_WEIGHT, 'weight'),
        (PERMISSION_ADD_SETTING, 'add_setting'),
    ]
    permission = models.CharField(blank=True, null=True, max_length=255, default=default_userscale_permission, verbose_name="สิทธิ์การใช้งาน")#สิทธิ์การใช้งาน (เก็บแบบ hash, ค่าเริ่มต้น weight)

    class Meta:
        verbose_name = 'ผู้ชั่ง'
        verbose_name_plural = 'ข้อมูลผู้ชั่ง'
    
    def __str__(self):
        return self.scale_name

#set weight old year
class SetWeightOY(models.Model):
    comp = models.ForeignKey(BaseCompany, on_delete=models.CASCADE, blank = True, null = True, verbose_name="บริษัท")
    weight = models.TextField(blank=True, null=True, verbose_name="ตั้งค่าน้ำหนัก")
    prod_run = models.TextField(blank=True, null=True, verbose_name="ตั้งค่าผลิต ชม.โม่")
    prod_work = models.TextField(blank=True, null=True, verbose_name="ตั้งค่าผลิต ตัน/ชม.")
    prod_cap = models.TextField(blank=True, null=True, verbose_name="ตั้งค่าผลิต วันทำงาน")
    prod_hpd = models.TextField(blank=True, null=True, verbose_name="ตั้งค่าผลิต ชม./วัน")

    class Meta:
        verbose_name = 'ตั้งค่าน้ำหนักหินปีก่อน'
        verbose_name_plural = 'ข้อมูลตั้งค่าน้ำหนักหินปีก่อน'

#ตั้งค่าบริษัทและชนิดหินหน้า dashbord
class SetCompStone(models.Model):
    comp = models.OneToOneField(BaseCompany, on_delete=models.CASCADE,null=True, blank=True, verbose_name="บริษัท")
    stone = models.TextField(blank=True, null=True, verbose_name="list หินหน้า dashbord ***เรียงตาม id")

    class Meta:
        db_table = 'set_company_stone'
        verbose_name = 'ตั้งค่าบริษัทและชนิดหินหน้า dashbord'
        verbose_name_plural = 'ข้อมูลตั้งค่าบริษัทและชนิดหินหน้า dashbord'
        
    def __str__(self):
        return str(self.comp)

class SetPatternCode(models.Model):
    m_name = models.CharField(blank=True, null=True, max_length=120, verbose_name="Models Name")
    start = models.CharField(blank=True, null=True, max_length=120, verbose_name="เริ่มจาก")
    end = models.CharField(blank=True, null=True, max_length=120, verbose_name="ถึง")
    pattern = models.CharField(blank=True, null=True, max_length=120, verbose_name="แพทเทิร์นรหัส")
    wt_id = models.CharField(blank=True, null=True, max_length=120, verbose_name="Weight Type Id")

    class Meta:
        db_table = 'set_pattern_code'
        verbose_name = 'ตั้งค่าแพทเทิร์นรหัส Base'
        verbose_name_plural = 'ข้อมูลตั้งค่าแพทเทิร์นรหัส Base'

    def __str__(self):
        return self.m_name
    
    def get_model(self):
        if self.m_name:
            try:
                # Get the model class from the app registry
                model = apps.get_model(app_label='weightapp', model_name=self.m_name)
                return model
            except LookupError:
                # Handle the case where the model does not exist
                return None
        return None

class SetLineMessaging(models.Model):
    target_id = models.CharField(blank=True, null=True, max_length=120, verbose_name="user/group ID")
    note = models.CharField(blank=True, null=True, max_length=120)

    class Meta:
        db_table = 'set_line_messaging'
        verbose_name = 'ตั้งค่า Line Messaging'
        verbose_name_plural = 'ข้อมูลตั้งค่า Line Messaging'

    def __str__(self):
        return str(self.id)
    
class GasPrice(models.Model):
    created = models.DateField(default = timezone.now, verbose_name="วันที่สร้าง") #เก็บวันที่สร้าง
    cost = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=10 , verbose_name="ราคาต้นทุน")
    sell = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=10 , verbose_name="ราคาขาย")
    total_cost = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=10 , verbose_name="รวมต้นทุน * ปริมาณน้ำมัน")
    total_sell = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=10 , verbose_name="รวมราคาขาย * ปริมาณน้ำมัน")
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")

    class Meta:
        db_table = 'gas_price'
        verbose_name = 'ราคาน้ำมัน'
        verbose_name_plural = 'ข้อมูลราคาน้ำมัน'

    def __str__(self):
        return str(self.id)
    
#Port Stock
class PortStock(models.Model):
    created = models.DateField(default = timezone.now, verbose_name="วันที่ผลิต") #เก็บวันที่ stock
    update = models.DateField(auto_now=True, verbose_name="วันที่อัพเดท") #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True , verbose_name="บริษัท")

    class Meta:
        db_table = 'port_stock'

    def __str__(self):
        return str(self.id)

#ชนิดหินและจำนวนหินทั้งหมดใน Port Stock
class PortStockStone(models.Model):
    stone = models.ForeignKey(BaseStoneType, on_delete=models.CASCADE, null=True, blank=True, max_length=120, verbose_name="ชนิดหิน", to_field='base_stone_type_id')
    total = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=10 , verbose_name="รวมทั้งหมด")
    ps = models.ForeignKey(PortStock, on_delete=models.CASCADE,null=True, blank=True, verbose_name="port stock")
    note = models.TextField(blank=True, null=True, verbose_name="หมายเหตุ")

    class Meta:
        db_table = 'port_stock_stone'

    def __str__(self):
        return str(self.id)
        
class PortStockStoneItem(models.Model):
    cus = models.ForeignKey(
        BaseCustomer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        max_length=120,
        to_field='customer_id',
        db_column='cus_id',
        verbose_name="ลูกค้า"
    )
    quoted = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0.00) #ยกมา
    receive = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0.00) #รับเข้า
    pay = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0.00) #จ่ายลงเรือ
    loss = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0.00) #สูญเสียจากการขนถ่าย
    other = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0.00) #เพิ่ม หินอันเดอร์ไซต์ เฉพาะ (หิน 40-80)
    sell_cus = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0.00) #ขายในนามบริษัทอื่น SLC
    total = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0.00) #รวม
    pss = models.ForeignKey('PortStockStone', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'port_stock_stone_item'

class BaseWeightRange(models.Model):
    name = models.CharField(max_length=120,unique=True, verbose_name="ชื่อ")
    descrip = models.CharField(max_length=255,unique=True, verbose_name="คำอธิบาย")
    rate_min =  models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5, verbose_name="เรทน้ำหนักน้อยที่สุด")
    rate_max =  models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5, verbose_name="เรทน้ำหนักมากที่สุด")
    company = models.ManyToManyField(BaseCompany,verbose_name="บริษัท")

    class Meta:
        db_table = 'base_weight_range'
        ordering=('id',)
        verbose_name = 'เรทน้ำหนักตาชั่ง'
        verbose_name_plural = 'ข้อมูลเรทน้ำหนักตาชั่ง'
    
    def __str__(self):
        return str(self.name)

############# เรทค่าตัก/ขน #############
######################################
class LoadingRate(models.Model):
    created = models.DateField(auto_now_add=True, verbose_name="วันที่สร้าง")
    update = models.DateField(auto_now=True, verbose_name="วันที่อัพเดท") #เก็บวันเวลาที่แก้ไขอัตโนมัติล่าสุด
    date_start_rate = models.DateField(default = timezone.now, verbose_name="วันเริ่มใช้เรทราคา")
    company = models.ForeignKey(BaseCompany,on_delete=models.CASCADE, null = True, verbose_name="บริษัท")

    class Meta:
        db_table = 'loading_rate'
    
    def __str__(self):
        return str(self.id)
    
class LoadingRateLoc(models.Model):
    mill = models.ForeignKey(
        BaseMill,
        max_length=120,
        to_field='mill_id',
        db_column='mill_id',
        on_delete=models.CASCADE,
        verbose_name="รหัสต้นทาง",
        blank=True, null=True,
    )
    site = models.ForeignKey(
        BaseSite,
        max_length=120,
        to_field='base_site_id',
        db_column='site_id',
        on_delete=models.CASCADE,
        verbose_name="รหัสปลายทาง",
        blank=True, null=True,
    )
    weight_type = models.ForeignKey(BaseWeightType,on_delete=models.CASCADE, null = True , verbose_name="ประเภทเครื่องชั่ง")
    Lr = models.ForeignKey(LoadingRate,on_delete=models.CASCADE, blank=True, null = True)

    class Meta:
        db_table = 'loading_rate_loc'
    
    def __str__(self):
        return str(self.id)
    
class LoadingRateItem(models.Model):
    wt_range = models.ForeignKey(BaseWeightRange, on_delete=models.CASCADE, blank=True, null = True, verbose_name="เรทน้ำหนักตาชั่ง")

    tru_shipp = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5 , verbose_name="อัตราค่าขน/บรรทุก (สิบล้อ)")
    chi_shipp = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5 , verbose_name="อัตราค่าขน/บรรทุก (จีน)")

    bh_tru_scoop = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5 , verbose_name="อัตราค่าตักจากแบ็คโฮ (สิบล้อ)")
    bh_chi_scoop = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5 , verbose_name="อัตราค่าตักจากแบ็คโฮ (จีน)")

    tru_scoop = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5 , verbose_name="อัตราค่าตักจากรถตัก (สิบล้อ)")
    chi_scoop = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=5 , verbose_name="อัตราค่าตักจากรถตัก (จีน)")

    Lrl = models.ForeignKey(LoadingRateLoc ,on_delete=models.CASCADE, blank=True, null = True)
    Lr = models.ForeignKey(LoadingRate ,on_delete=models.CASCADE, blank=True, null = True)

    class Meta:
        db_table = 'loading_rate_item'
        indexes = [
            models.Index(fields=['Lrl', 'wt_range']),
            models.Index(fields=['Lr']),
        ]
    
    def __str__(self):
        return str(self.id)
    
############# เรทค่าตัก/ขน #############
######################################
class WeightDelivery(models.Model):
    weight_id = models.IntegerField(unique=True, blank = True, null = True, db_index=True)
    delivery_date = models.DateField(
        null=True,
        blank=True,
        db_index=True
    )
    bws = models.CharField(
        max_length=20, blank=False, null=True, db_index=True
    )
    comp_code = models.CharField(
        max_length=20, blank=False, null=True, db_index=True
    )
    do_id = models.IntegerField()
    do_doc_no =  models.CharField(
        max_length=30, blank=False, null=True, db_index=True
    )
    #เลขที่ชั่ง จาก ตาชั่ง local
    weight_doc_id =  models.CharField(
        max_length=30, blank=False, null=True, db_index=True
    )

    carry_type_name = models.CharField(blank=True, null=True,max_length=20)
    weight_ton = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)
    weight_q = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)
    unit_name = models.CharField(
        max_length=20, blank=False, null=True
    )
    is_cancel = models.BooleanField(default=False, verbose_name="สถานะยกเลิกรายการ")
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'weight_delivery'
        ordering = ['id']
        indexes = [
            models.Index(fields=['weight_id', 'bws']),
            models.Index(fields=['weight_id', 'do_doc_no']),
            models.Index(
                fields=['do_doc_no', 'bws', 'delivery_date']
            ),
            models.Index(fields=['weight_id']),
        ]

    def __str__(self):
        return str(self.id)
	
class DeliveryOrder(models.Model):
    delivery_date = models.DateField(
        null=True,
        blank=True,
        db_index=True
    )
    doc_no = models.CharField(
        max_length=30, blank=False, null=True, db_index=True
    )

    car_company = models.IntegerField(blank=True, null=True)
    car_customer = models.IntegerField(blank=True, null=True)

    car_company_tot = models.IntegerField(blank=True, null=True)
    car_customer_tot = models.IntegerField(blank=True, null=True)

    car_company_rem = models.IntegerField(blank=True, null=True)
    car_customer_rem = models.IntegerField(blank=True, null=True)

    customer_code = models.CharField(max_length=20, blank=False, null=True)
    customer_name = models.CharField(max_length=255, blank=False, null=True)
    customer_address = models.CharField(max_length=255, blank=False, null=True)
    site_id = models.CharField(max_length=20, blank=False, null=True)
    site_name = models.CharField(max_length=255, blank=False, null=True)

    product_code = models.CharField(max_length=20, blank=False, null=True)
    product_name = models.CharField(max_length=255, blank=False, null=True)

    sale_name = models.CharField(max_length=255, blank=False, null=True)
    note = models.CharField(max_length=255, blank=False, null=True)
    status= models.CharField(max_length=255, blank=False, null=True)
    
    qty = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)
    qty_tot = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=10)

    unit_name = models.CharField(max_length=20, blank=False, null=True)
    comp_code = models.CharField(max_length=20, blank=False, null=True, db_index=True)
    v_stamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'delivery_order'
        ordering = ['id']
        indexes = [
            models.Index(
                fields=['doc_no', 'comp_code', 'delivery_date']
            ),
            models.Index(fields=['comp_code', 'doc_no']),
            models.Index(fields=['doc_no',]),
        ]

    def __str__(self):
        return str(self.id)
    
class BaseAPI(models.Model):
    url = models.CharField(max_length=255, blank=True, null = True, verbose_name="url api data")
    apiname = models.CharField(max_length=255, blank=True, null = True, verbose_name="api name")
    username = models.CharField(max_length=255, blank=True, null = True, verbose_name="username get api")
    password = models.CharField(max_length=255, blank=True, null = True, verbose_name="password get api")
    token = models.CharField(max_length=255, blank=True, null = True, verbose_name="token")

    class Meta:
        db_table = 'base_api'
        ordering=('id',)
        verbose_name = 'ตั้งค่า API'
        verbose_name_plural = 'ข้อมูลตั้งค่า API'

    def __str__(self):
        return str(self.id)

class AppRelease(models.Model):
    CHANNEL_CHOICES = [
        ('stable', 'Stable'),
        ('beta', 'Beta'),
    ]

    product_code = models.CharField(max_length=50, default='Blue.SLC.W1.IN.Server', verbose_name="รหัสโปรแกรม")
    version = models.CharField(max_length=20, verbose_name="เวอร์ชัน")
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='stable', verbose_name="ช่องทาง")
    release_notes = models.TextField(blank=True, null=True, verbose_name="รายละเอียดอัพเดท")
    installer_file = models.FileField(upload_to='releases/%Y/%m/', verbose_name="ไฟล์ติดตั้ง")
    file_hash_sha256 = models.CharField(max_length=64, verbose_name="SHA256")
    # สคริปต์ SQL (PostgreSQL) ที่ต้องรันกับ DB local ของ client ก่อนติดตั้งเวอร์ชันใหม่ (ถ้ามี)
    sql_script = models.FileField(upload_to='releases/sql/%Y/%m/', blank=True, null=True, verbose_name="สคริปต์ SQL (ถ้ามี)")
    sql_script_hash_sha256 = models.CharField(max_length=64, blank=True, null=True, verbose_name="SHA256 ของสคริปต์ SQL")
    is_mandatory = models.BooleanField(default=False, verbose_name="บังคับอัพเดท")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    released_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่ปล่อยเวอร์ชัน")
    created_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="สร้างโดย")

    class Meta:
        db_table = 'app_release'
        unique_together = ('product_code', 'version')
        ordering = ['-released_at']
        verbose_name = 'เวอร์ชันโปรแกรม'
        verbose_name_plural = 'ข้อมูลเวอร์ชันโปรแกรม'

    def clean(self):
        import re
        from django.core.exceptions import ValidationError
        if not re.fullmatch(r'[0-9a-fA-F]{64}', self.file_hash_sha256 or ''):
            raise ValidationError({'file_hash_sha256': 'ต้องเป็นค่า SHA256 แบบ hex 64 ตัวอักษร'})
        if self.sql_script and not re.fullmatch(r'[0-9a-fA-F]{64}', self.sql_script_hash_sha256 or ''):
            raise ValidationError({'sql_script_hash_sha256': 'ถ้าอัพโหลดสคริปต์ SQL ต้องระบุ SHA256 แบบ hex 64 ตัวอักษรด้วย'})

    def __str__(self):
        return f"{self.product_code} v{self.version} ({self.channel})"

class ClientUpdateLog(models.Model):
    product_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="โปรดักส์")
    weight_station = models.ForeignKey(BaseWeightStation, null=True, blank=True, on_delete=models.SET_NULL, db_constraint=False, verbose_name="ตาชั่ง")
    machine_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="ชื่อเครื่อง")
    from_version = models.CharField(max_length=20, blank=True, null=True, verbose_name="เวอร์ชันเดิม")
    to_version = models.CharField(max_length=20, verbose_name="เวอร์ชันใหม่")
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name="เวลาที่เช็ค")
    update_applied = models.BooleanField(default=False, verbose_name="อัพเดทสำเร็จ")
    sql_applied = models.BooleanField(default=False, verbose_name="รันสคริปต์ SQL สำเร็จ")

    class Meta:
        db_table = 'client_update_log'
        ordering = ['-checked_at']
        verbose_name = 'ประวัติการอัพเดทเครื่อง'
        verbose_name_plural = 'ประวัติการอัพเดทเครื่อง'

    def __str__(self):
        return f"{self.machine_name} -> {self.to_version}"

class BaseCompanyMapBaseCustomer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120, verbose_name="ชื่อ")
    base_company = models.ForeignKey(BaseCompany , null = True, on_delete=models.CASCADE, verbose_name="บริษัท")
    base_customer = models.ForeignKey(BaseCustomer, null = True, on_delete=models.CASCADE, verbose_name="ลูกค้า")
    
    class Meta:
        db_table = 'base_company_map_base_customer'
        ordering = ['id']
        unique_together = ('base_company', 'base_customer')
        verbose_name = 'บริษัทลูกค้า'
        verbose_name_plural = 'ข้อมูลบริษัทลูกค้า'
    
    def __str__(self):
        company = self.base_company.name if self.base_company else "-"
        customer = self.base_customer.customer_name if self.base_customer else "-"
        return f"{company} - {customer}"

class InternationalFreightRateStatus(models.TextChoices):
    """สถานะการอนุมัติของ 1 ใบ (1 เวอร์ชัน)

    เก็บเฉพาะข้อเท็จจริงว่า "ใบนี้ผ่านการอนุมัติหรือยัง" ซึ่งไม่เปลี่ยนอีกเมื่อเกิดขึ้นแล้ว
    ส่วนคำถามว่า "ใบไหนใช้อยู่ตอนนี้" ไม่เก็บเป็นค่า แต่คำนวณจาก effective_date
    เพราะคำตอบขึ้นกับว่าถามถึงเดือนไหน เดือน พ.ค. กับ ส.ค. อาจได้คนละใบ
    """
    DRAFT = 'draft', 'ร่าง'
    PENDING = 'pending', 'รออนุมัติ'
    APPROVED = 'approved', 'อนุมัติแล้ว'
    REJECTED = 'rejected', 'ไม่อนุมัติ'


# เวอร์ชันแรกของทุกเส้นทางมีผล "ตั้งแต่ต้น" ไม่ใช่ตั้งแต่วันที่สร้างแถว
# เพราะข้อมูลการชั่งมีย้อนหลังหลายปี แต่แถวอัตราเพิ่งถูกกรอกเข้าระบบปีนี้
# ถ้าใช้วันที่สร้าง export เดือนเก่าจะหาอัตราไม่เจอแล้วเที่ยวหายทั้งเส้นทาง
# หมายเหตุ : ไฟล์นี้ import datetime แบบโมดูล (บรรทัดล่างทับ from datetime import ...) จึงต้องเรียกเต็ม
INTERNATIONAL_FREIGHT_RATE_FIRST_DATE = datetime.date(2000, 1, 1)


class InternationalFreightRate(models.Model):
    """1 แถว = 1 ใบ = 1 เวอร์ชันของเส้นทางหนึ่ง

    แก้ราคาแล้วไม่ทับของเดิม แต่ออกใบใหม่ทั้งใบ (copy ทีมมาด้วย) ใบเก่าอยู่ครบไม่ถูกแตะ
    เอกสารเดือนเก่าจึงได้ตัวเลขเดิมเสมอ ต่อให้ราคาปัจจุบันเปลี่ยนไปแล้ว

    root = ใบแรกสุดของเส้นทางนั้น ใช้เป็นตัวแทน "เส้นทาง" (ใบแรกชี้ตัวเอง)
    ทุกเวอร์ชันของเส้นทางเดียวกันมี root เดียวกัน
    """
    id = models.AutoField(primary_key=True) #
    # ผูกกับคู่บริษัท-ลูกค้าที่ map ไว้แล้ว แทนการเก็บชื่อเป็นข้อความ
    # PROTECT : ห้ามลบแถว map ที่ยังมีอัตราค่าขนส่งอ้างอยู่ ไม่งั้นจะเหลือรายการที่ไม่รู้ต้นทาง/ปลายทาง
    # ชื่อดึงจาก origin.name เอา ไม่เก็บซ้ำในตารางนี้ กันข้อมูลขัดกันเองเวลามีคนแก้ชื่อในตาราง map
    origin = models.ForeignKey(BaseCompanyMapBaseCustomer, on_delete=models.PROTECT, related_name='freight_rate_origins', null=True, blank=True, verbose_name="ต้นทาง")
    destination = models.ForeignKey(BaseCompanyMapBaseCustomer, on_delete=models.PROTECT, related_name='freight_rate_destinations', null=True, blank=True, verbose_name="ปลายทาง")
    base_fuel_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="ราคาน้ำมันฐาน")#
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="ระยะทาง")#
    payload_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="น้ำหนักบรรทุก")#
    fuel_freight_adjustment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="ปรับค่าขนส่งตามน้ำมันที่ใช้ ลิตรละ 1 บาท")#
    fuel_used_per_trip = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="ใช้น้ำมัน (ลิตร/เที่ยว)")#
    # ราคาน้ำมันเฉลี่ยย้ายไปตาราง InternationalFreightRateFuelPrice เพราะเปลี่ยนทุกเดือน
    # ส่วน base_fuel_price กับ fuel_freight_adjustment ยังอยู่ที่นี่ เป็นเงื่อนไขในสัญญาที่ไม่เปลี่ยนรายเดือน
    note = models.CharField(max_length=255, null=True, blank=True, verbose_name="หมายเหตุ")#

    # --- การทำเวอร์ชัน ---
    # PROTECT : ห้ามลบใบแรกทิ้งขณะที่ยังมีเวอร์ชันอื่นอ้างอยู่ ไม่งั้นทั้งเส้นทางจะขาดตัวแทน
    # การลบเส้นทางต้องลบทั้งตระกูล (ทุกใบที่ root เดียวกัน) ดูใน API delete
    root = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True,
                             related_name='versions', verbose_name="เส้นทาง (ใบแรกสุด)")
    version = models.IntegerField(default=1, verbose_name="เวอร์ชัน")
    # วันที่เริ่มใช้จริง เป็นวันไหนของเดือนก็ได้ ไม่บังคับวันที่ 1
    # v1 = INTERNATIONAL_FREIGHT_RATE_FIRST_DATE (ตั้งแต่ต้น) · v2 ขึ้นไป = วันที่อนุมัติ
    effective_date = models.DateField(null=True, blank=True, verbose_name="วันที่เริ่มใช้")

    # --- การอนุมัติ ---
    # เฟสนี้ยังไม่เปิดระบบอนุมัติ ทุกใบจึงเป็น approved ทันที
    # พอเปิดเฟส 2 ค่อยเปลี่ยนใบใหม่ให้เริ่มที่ pending แล้วรอผู้บริหารกด
    status = models.CharField(max_length=20, choices=InternationalFreightRateStatus.choices,
                              default=InternationalFreightRateStatus.APPROVED,
                              verbose_name="สถานะ")
    user_created = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='international_freight_rates_created',
                                     verbose_name="ผู้ออกใบ")
    # เวลาที่ส่งขออนุมัติ "ครั้งล่าสุด" ถ้าโดน reject แล้วส่งใหม่ ค่านี้จะทับของเดิม
    # ประวัติครบทุกรอบอยู่ใน InternationalFreightRateApproval ไม่ได้หายไปไหน
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="ส่งขออนุมัติเมื่อ")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='international_freight_rates_approved',
                                    verbose_name="ผู้อนุมัติ")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="อนุมัติเมื่อ")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่สร้าง")
    # ใบที่อนุมัติแล้วจะไม่ถูกแก้อีก ค่านี้จึงมีความหมายเฉพาะช่วงที่ยังเป็นร่าง/รออนุมัติ
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไขล่าสุด")

    class Meta:
        db_table = 'international_freight_rate'
        ordering = ['id']
        unique_together = ('root', 'version')
        indexes = [
            models.Index(fields=['root', 'status', '-effective_date', '-id'],
                         name='ifr_root_status_month_idx'),
        ]
        verbose_name = 'อัตราค่าขนส่งไปนอกประเทศ'
        verbose_name_plural = 'อัตราค่าขนส่งไปนอกประเทศ'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # ใบแรกของเส้นทางชี้ตัวเอง ต้องรอให้มี id ก่อนถึงจะตั้งได้
        if self.root_id is None:
            self.root_id = self.id
            super().save(update_fields=['root'])

    @classmethod
    def effectiveOn(cls, as_of=None, queryset=None):
        """ใบที่ใช้จริงของทุกเส้นทาง ณ วันที่ที่ระบุ — 1 เส้นทางได้ 1 ใบเท่านั้น

        นี่คือกฎกลางจุดเดียวของทั้งระบบ ห้ามเขียน query หาอัตราเองที่อื่น
        ไม่งั้นจะมีที่ที่หลุดไปใช้ใบที่ยังไม่อนุมัติ หรือใบที่ยังไม่ถึงวันมีผล

        as_of ต้องเป็น "วันที่" ไม่ใช่เดือน เพราะ effective_date เป็นวันไหนก็ได้ของเดือน
        ถ้าส่งวันที่ 1 ของเดือนเข้ามา ใบที่เริ่มใช้กลางเดือนจะยังไม่ถูกเลือก
        as_of = None แปลว่าเอาใบล่าสุดที่อนุมัติแล้ว ไม่สนวันมีผล

        queryset ส่งเข้ามาได้เพื่อใส่ select_related / prefetch_related เพิ่มเอง
        """
        qs = cls.objects.all() if queryset is None else queryset
        qs = qs.filter(status=InternationalFreightRateStatus.APPROVED)
        if as_of is not None:
            qs = qs.filter(effective_date__lte=as_of)

        # ตัดสินด้วย "ลำดับใบ" (id) ไม่ใช่ "วันที่มีผล"
        # ใบที่ออกทีหลังคือคำสั่งล่าสุดของคน จึงต้องชนะเสมอเมื่อถึงวันมีผลแล้ว
        #
        # ถ้าเรียงตาม effective_date จะมีกับดัก : ตั้งวันย้อนหลังในใบล่าสุดแล้วมันไม่มีผล
        # เพราะใบเก่าที่วันใหม่กว่าจะชนะ คนแก้ราคาแล้วงงว่าทำไมระบบไม่เปลี่ยน
        # เช่น v8 วันมีผล 23 ส.ค. / v9 ตั้งย้อนเป็น 1 ส.ค. -> ต้องได้ v9 ไม่ใช่ v8
        by_root = {}
        for rate in qs.order_by('root_id', 'id'):
            by_root[rate.root_id] = rate
        return list(by_root.values())

    def isFirstVersion(self):
        """ใบแรกของเส้นทาง แก้ทับได้เลยไม่ต้องขึ้นเวอร์ชัน ถ้ายังไม่มีใบอื่นตามมา"""
        return self.root_id == self.id

    def __str__(self):
        origin = self.origin.name if self.origin else "-"
        destination = self.destination.name if self.destination else "-"
        return f"{origin} - {destination} (v{self.version})"


class InternationalFreightRateFuelPrice(models.Model):
    """ราคาน้ำมันเฉลี่ยรายเดือนของแต่ละเส้นทาง (เก็บแบบ log ต่อท้าย)

    แยกออกมาจาก InternationalFreightRate เพราะราคาเปลี่ยนทุกเดือน
    ส่วนตัวสัญญา (ระยะทาง / อัตรา / ราคาน้ำมันฐาน) ไม่เปลี่ยน

    แก้ราคาเดือนเดิมกี่ครั้งก็เพิ่มแถวใหม่ทุกครั้ง ไม่ทับของเก่า
    "ราคาที่ใช้จริง" ของเดือนหนึ่ง = แถวที่ id มากที่สุดของเดือนนั้น (บันทึกล่าสุด)
    """
    id = models.AutoField(primary_key=True)
    # ผูกกับ "เส้นทาง" (แถว root) ไม่ใช่เวอร์ชันใดเวอร์ชันหนึ่ง
    # เพราะราคาน้ำมันเปลี่ยนทุกเดือน ส่วนใบอัตราเปลี่ยนปีละครั้ง คนละจังหวะกัน
    # ถ้าผูกกับเวอร์ชัน พอออกใบใหม่ประวัติราคาน้ำมันจะติดอยู่กับใบเก่าแล้วใบใหม่เริ่มจากศูนย์
    root = models.ForeignKey(
        InternationalFreightRate, on_delete=models.CASCADE,
        related_name='fuel_prices', verbose_name="เส้นทาง (ใบแรกสุด)")

    # เก็บเป็นวันที่ 1 ของเดือนเสมอ (ดู save) หน้าเว็บให้เลือกแค่เดือน ไม่มีช่องวัน
    # ใช้ DateField แทน year/month แยกช่อง จะได้กรองช่วงเดือนและเรียงลำดับได้ตรง ๆ
    month = models.DateField(verbose_name="ประจำเดือน")
    average_fuel_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="ราคาน้ำมันเฉลี่ย (บาท/ลิตร)")

    note = models.CharField(max_length=255, null=True, blank=True, verbose_name="หมายเหตุ")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไขล่าสุด")

    class Meta:
        db_table = 'international_freight_rate_fuel_price'
        # ใหม่ไปเก่า : เดือนล่าสุดก่อน ถ้าเดือนเดียวกันเอาที่บันทึกทีหลังขึ้นก่อน
        ordering = ['-month', '-id']
        # ไม่มี unique_together เพราะ 1 เดือนมีได้หลายแถว (แก้ราคากี่ครั้งก็เก็บครบ)
        indexes = [
            models.Index(fields=['root', '-month', '-id'],
                         name='ifr_fuel_rate_month_idx'),
        ]
        verbose_name = 'ราคาน้ำมันเฉลี่ยรายเดือน'
        verbose_name_plural = 'ราคาน้ำมันเฉลี่ยรายเดือน'

    def save(self, *args, **kwargs):
        # ตัดวันทิ้งเสมอ ให้ทุกแถวของเดือนเดียวกันมีค่า month ตรงกันเป๊ะ
        # ไม่งั้นการจับกลุ่มตามเดือนจะแตกเป็นหลายกลุ่มโดยไม่ตั้งใจ
        if self.month:
            self.month = self.month.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return "%s : %s" % (self.month.strftime('%Y-%m') if self.month else '-',
                            self.average_fuel_price)


# class CarryingweightTeam(models.TextChoices):
#     # เก็บลง db เป็นข้อความไทยตรงๆ และแสดงผลเป็นข้อความเดียวกัน
#     weight_carried_1 = "แบก นน.", "แบก นน."
#     weight_carried_2 = "ไม่แบก นน.", "ไม่แบก นน."
#     weight_carried_3 = "ตาม นน.", "ตาม นน."
#     weight_carried_4 = "นน. 35.01-40 ตัน", "นน. 35.01-40 ตัน"
#     weight_carried_5 = "นน. 40.01-50 ตันขึ้นไป", "นน. 40.01-50 ตันขึ้นไป"
#     weight_carried_6 = "น้อยกว่าหรือเท่ากับ 35 ตัน", "น้อยกว่าหรือเท่ากับ 35 ตัน"
#     weight_carried_7 = "น้ำหนัก 35.01-50 ตัน", "น้ำหนัก 35.01-50 ตัน"
#     weight_carried_8 = "นน 50 ตันขึ้นไป", "นน 50 ตันขึ้นไป"
#     weight_carried_9 = "นน 40-50 ตัน", "นน 40-50 ตัน"
#     weight_carried_10 = "เหมาเรทเดียว", "เหมาเรทเดียว"

class CarryingweightRate(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(_("ชื่อเรท"), max_length=100)
    # weight_carried = models.CharField(_("ประเภทการแบก นน."), max_length=100, choices=CarryingweightTeam.choices)
    description = models.CharField(_("รายละเอียด"), max_length=255)
    min_weight = models.DecimalField(_("น้ำหนักขั้นต่ำ"), max_digits=10, decimal_places=2)
    max_weight = models.DecimalField(_("น้ำหนักสูงสุด"), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไขล่าสุด")
    
    class  Meta:
        db_table = 'carryingweight_rate'
        verbose_name = 'ประเภทการแบกน้ำหนัก'
        verbose_name_plural = 'ประเภทการแบกน้ำหนัก'
        
    def __str__(self):
        return f"{self.name} ({self.min_weight} - {self.max_weight})"
    





class InternationalFreightRateTeam(models.Model):
    id = models.AutoField(primary_key=True)
    international_freight_rate = models.ForeignKey(InternationalFreightRate, on_delete=models.CASCADE, related_name='teams', verbose_name="อัตราค่าขนส่งไปนอกประเทศ")
    # base_car_team เป็นตารางเก่าจาก phpMyAdmin dump คอลัมน์ car_team_id ใช้ collation utf8mb4_general_ci
    # ต่างจาก default ของ DB (utf8mb4_unicode_ci) ที่ Django ใช้สร้างคอลัมน์ใหม่
    # MySQL 8 จะ error 3780 ถ้าสร้าง FK ข้าม collation จึงต้องบังคับ collation ของคอลัมน์ฝั่งนี้ให้ตรงกัน
    # ดู migration 0274 ที่แปลง collation แล้วค่อยสร้าง constraint จริง
    # team = NULL หมายถึง "ทุกทีม" (เคสเหมาเรทเดียวที่ทุกทีมคิดราคาเท่ากัน) เก็บแถวเดียวพอ
    # ถ้าทีมไหนคิดไม่เท่ากัน ค่อยเพิ่มแถวที่ระบุทีมนั้นมาทับ
    # การหาราคา : หาแถวที่ตรงทีมก่อน ไม่เจอค่อย fallback ไปแถว team = NULL
    team = models.ForeignKey(BaseCarTeam, on_delete=models.CASCADE, null=True, blank=True, verbose_name="ทีมขนส่ง (ว่าง = ทุกทีม)")
    # weight_carried = models.CharField(max_length=50, choices=CarryingweightTeam.choices, verbose_name="ประเภทการแบกน้ำหนัก")
    weight_carried = models.ForeignKey(CarryingweightRate, on_delete=models.CASCADE, null=True, blank=True, verbose_name="ประเภทการแบกน้ำหนัก")
    freight_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="ค่าขนส่ง")
    discount_per_ton = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="ลดบาท/ตัน")
    freight_rate_per_ton_km = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name="ค่าขนส่ง บาท/ตัน/กม.")
    note = models.TextField(null=True, blank=True, verbose_name="หมายเหตุ")

    class Meta:
        db_table = 'international_freight_rate_team'
        ordering = ['id']
        verbose_name = 'อัตราค่าขนส่งไปนอกประเทศ (ทีม)'
        verbose_name_plural = 'อัตราค่าขนส่งไปนอกประเทศ (ทีม)'

    def __str__(self):
        team_name = self.team.car_team_name if self.team else "ทุกทีม"
        return f"{team_name} - {self.weight_carried}"



class InternationalFreightRateApprovalAction(models.TextChoices):
    SUBMIT = 'submit', 'ขออนุมัติ'
    APPROVE = 'approve', 'อนุมัติ'
    REJECT = 'reject', 'ไม่อนุมัติ'


class InternationalFreightRateApproval(models.Model):
    """บทสนทนาการอนุมัติของ 1 ใบ เก็บต่อท้ายทุกครั้ง ไม่ทับของเดิม

    ต้องแยกเป็นตาราง ไม่ใช่คอลัมน์บนใบ เพราะเป็นการคุยไป-กลับหลายรอบ
    (ขอ -> ไม่อนุมัติพร้อมเหตุผล -> แก้แล้วขอใหม่ -> อนุมัติ) คอลัมน์เดียวเก็บได้แค่ครั้งล่าสุด

    ผูกกับ "ใบ" ไม่ใช่เส้นทาง เพราะใบที่ยังไม่อนุมัติแก้ทับในแถวเดิมได้
    บทสนทนาทั้งรอบจึงอยู่ครบในใบเดียว ไม่กระจัดกระจายข้ามเวอร์ชัน
    """
    id = models.AutoField(primary_key=True)
    international_freight_rate = models.ForeignKey(
        InternationalFreightRate, on_delete=models.CASCADE,
        related_name='approvals', verbose_name="ใบอัตราค่าขนส่ง")
    action = models.CharField(max_length=20, choices=InternationalFreightRateApprovalAction.choices,
                              verbose_name="การกระทำ")
    # ไม่บังคับที่ระดับ DB แต่บังคับที่ API : ตอนขออนุมัติกับตอนไม่อนุมัติต้องเขียนเหตุผล
    comment = models.TextField(null=True, blank=True, verbose_name="ความเห็น")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                             related_name='international_freight_rate_approvals',
                             verbose_name="ผู้บันทึก")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="เมื่อ")

    class Meta:
        db_table = 'international_freight_rate_approval'
        # เก่าไปใหม่ อ่านไล่จากบนลงล่างเหมือนแชท
        ordering = ['id']
        indexes = [
            models.Index(fields=['international_freight_rate', 'id'], name='ifr_approval_rate_idx'),
        ]
        verbose_name = 'การอนุมัติอัตราค่าขนส่งไปนอกประเทศ'
        verbose_name_plural = 'การอนุมัติอัตราค่าขนส่งไปนอกประเทศ'

    def __str__(self):
        return "%s : %s" % (self.get_action_display(), self.comment or '-')


# InternationalFreightRateLog ถูกลบทิ้งใน migration 0285
# ตารางนั้นไม่เคยมีโค้ดไหนเขียนหรืออ่าน (0 แถว) และฟิลด์ก็ล้าสมัยไปแล้วหลังเปลี่ยน
# origin/destination เป็น FK และย้าย average_fuel_price ออกไปตารางราคาน้ำมันรายเดือน
# ตอนนี้ InternationalFreightRate เก็บทุกเวอร์ชันไว้ในตัวเองแล้ว จึงไม่ต้องมีตารางประวัติแยก

    def __str__(self):
        return f"Version {self.version} - {self.origin} to {self.destination}"
    