from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from weightapp.models import BaseWeightType, BaseWeightStation, BaseVatType, BaseLineType, BaseLossType, BaseMill, BaseJobType, BaseCustomer, BaseStoneType, BaseTimeEstimate, BaseSite, BaseStoneColor, Weight, WeightHistory, BaseCarRegistration, BaseDriver, BaseScoop, BaseCarryType, BaseTransport, BaseCarTeam, BaseCar, BaseFertilizer, BaseCustomerSite, BaseCompany, BaseAffiliatedCompany,UserScale, BaseMachineType, BaseVisible, UserProfile, BaseSEC, SetWeightOY, ProductionGoal, Production, ProductionLossItem, StoneEstimate, StoneEstimateItem, SetCompStone, SetPatternCode, BaseStockSource, Stock, StockStone, StockStoneItem, SetLineMessaging, GasPrice, BaseMillSource, BaseSiteStore, BaseBusiness, PortStock, PortStockStone, PortStockStoneItem, BaseWeightRange, LoadingRate, LoadingRateLoc, LoadingRateItem, BaseAPI, DeliveryOrder, WeightDelivery, AppRelease, AppReleaseTargetStation, ClientUpdateLog, BaseCompanyMapBaseCustomer, BaseCompanyMapCustomerAlias, InternationalFreightRate, InternationalFreightRateFuelPrice, InternationalFreightRateTeam, CarryingweightRate
from weightapp.models import hash_password_sha1
from django.forms import CheckboxSelectMultiple, MultipleChoiceField, widgets
from django import forms
from django.db.models.fields.related import ManyToManyField
from django.db import models
from django.utils.html import format_html, format_html_join
from django.contrib.auth.models import User
from django.contrib.admin.views.autocomplete import AutocompleteJsonView


def user_full_name(user):
    # User.__str__ ถูกตั้งให้คืนแค่ first_name (models.py) หน้า admin ช่องเลือกผู้ใช้ให้แสดง ชื่อ + นามสกุล
    full_name = ('%s %s' % (user.first_name or '', user.last_name or '')).strip()
    return full_name or user.username


class UserFullNameAutocompleteJsonView(AutocompleteJsonView):
    # ผลลัพธ์ตอนพิมพ์ค้นหาในช่อง autocomplete ของ User ให้แสดง ชื่อ + นามสกุล
    def serialize_result(self, obj, to_field_name):
        result = super().serialize_result(obj, to_field_name)
        if isinstance(obj, User):
            result['text'] = user_full_name(obj)
        return result


def user_full_name_autocomplete_view(request):
    return UserFullNameAutocompleteJsonView.as_view(admin_site=admin.site)(request)

admin.site.autocomplete_view = user_full_name_autocomplete_view


class UserFullNameFieldMixin:
    # ค่าที่เลือกไว้แล้วในช่อง User (ตอนเปิดหน้าแก้ไข) ให้แสดง ชื่อ + นามสกุล
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield is not None and db_field.remote_field.model is User:
            formfield.label_from_instance = user_full_name
        return formfield

# Register your models here.
class BaseVatTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_vat_type_id', 'base_vat_type_name', 'base_vat_type_des'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class WeightResource(resources.ModelResource):
    #24/04/2025 ถ้า weight มาจาก Import ให้ใส่ user_update = 1 (นิจนันท์)
    def save_instance(self, instance, using_transactions=True, dry_run=False):
        instance._from_import = True
        instance.save()
        return instance
    
    class Meta:
        model =  Weight
        import_id_fields = ('weight_id',)

class BaseJobTypeResource(resources.ModelResource):     

    class Meta:
        model = BaseJobType
        import_id_fields = ('base_job_type_id',)
        fields = ('base_job_type_id', 'base_job_type_name',)
        export_order = ('base_job_type_id', 'base_job_type_name',)

class BaseJobTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseJobTypeResource
    list_display = ('base_job_type_id', 'base_job_type_name',)
    search_fields = ('base_job_type_id', 'base_job_type_name')

class BaseCustomerResource(resources.ModelResource):
    base_vat_type = fields.Field(
        column_name='base_vat_type',
        attribute='base_vat_type',
        widget=ForeignKeyWidget(BaseVatType, 'base_vat_type_id'))

    base_job_type = fields.Field(
        column_name='base_job_type',
        attribute='base_job_type',
        widget=ForeignKeyWidget(BaseJobType, 'base_job_type_id'))       

    class Meta:
        model = BaseCustomer
        import_id_fields = ('customer_id',)
        fields = ('customer_id', 'customer_name', 'base_vat_type', 'base_job_type', 'weight_type')
        export_order = ('customer_id', 'customer_name', 'base_vat_type', 'base_job_type', 'weight_type')

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(customer_id=instance.pk).update(customer_name=instance.customer_name)

class BaseCustomerAdmin(ImportExportModelAdmin):
    resource_class = BaseCustomerResource
    list_display = ('customer_id', 'customer_name',)
    search_fields = ('customer_id', 'customer_name')

class BaseSiteResource(resources.ModelResource):
    class Meta:
        model = BaseSite
        import_id_fields = ('base_site_id',)
        fields = ('base_site_id', 'base_site_name', 'weight_type', 'store')
        export_order = ('base_site_id', 'base_site_name', 'weight_type', 'store')

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(site_id=instance.pk).update(site_name=instance.base_site_name)

class BaseSiteAdmin(ImportExportModelAdmin):
    resource_class = BaseSiteResource
    list_display = ['base_site_id', 'base_site_name', 'weight_type', 'store']
    search_fields = ('base_site_id', 'base_site_name')

class BaseStoneColorAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseStoneTypeResource(resources.ModelResource):
    class Meta:
        model = BaseStoneType
        import_id_fields = ('base_stone_type_id',)
        fields = ('base_stone_type_id', 'base_stone_type_name', 'cal_q')
        export_order = ('base_stone_type_id', 'base_stone_type_name', 'cal_q')

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(stone_type_id=instance.pk).update(stone_type_name=instance.base_stone_type_name)

class BaseStoneTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseStoneTypeResource
    list_display = ('base_stone_type_id', 'base_stone_type_name', 'cal_q', 'inactive')
    search_fields = ('base_stone_type_id', 'base_stone_type_name', 'cal_q', 'inactive')

class BaseWeightTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseWeightStationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','des','weight_id_min','weight_id_max'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseLossTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseMachineTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name','kind'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseMillResource(resources.ModelResource):
    class Meta:
        model = BaseMill
        import_id_fields = ('mill_id',)
        fields = ('mill_id', 'mill_name', 'weight_type', 'mill_source')
        export_order = ('mill_id', 'mill_name', 'weight_type', 'mill_source')

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(mill_id=instance.pk).update(mill_name=instance.mill_name)

class BaseMillAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseMillResource
    list_display = ('mill_id', 'mill_name', 'weight_type', 'mill_source')
    search_fields = ('mill_id', 'mill_name')

class BaseLineTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseTimeEstimateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    autocomplete_fields = ['site']

    list_display = ['site','time_name', 'time_from', 'time_to'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class DateRangeListFilter(admin.FieldListFilter):
    """กรองช่วงวันที่ (ตั้งแต่ - ถึง) ในแถบตัวกรองด้านขวาของหน้า admin

    ไม่ใช้ date_hierarchy ของ Django เพราะต้องกวาดหาปี/เดือน/วันที่มีข้อมูลทั้งตารางทุกครั้งที่เปิดหน้า
    ตาราง weight มีราวล้านแถว หน้าจะช้าลงทุกครั้ง ตัวนี้ไม่ query อะไรเพิ่ม
    แค่ใส่ date__gte / date__lte ลงใน url ปุ่ม Export ของหน้า admin ก็กรองตามนี้ด้วย
    (export ทั้งตารางทีเดียว time out ให้กรองทีละช่วงก่อนกด Export)
    """
    template = 'admin/weightapp/date_range_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_gte = '%s__gte' % field_path
        self.lookup_lte = '%s__lte' % field_path
        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = 'วันที่'

    def expected_parameters(self):
        return [self.lookup_gte, self.lookup_lte]

    def choices(self, changelist):
        ours = (self.lookup_gte, self.lookup_lte)
        yield {
            'lookup_gte': self.lookup_gte,
            'lookup_lte': self.lookup_lte,
            'gte': self.used_parameters.get(self.lookup_gte, ''),
            'lte': self.used_parameters.get(self.lookup_lte, ''),
            # ตัวกรองอื่น / คำค้น / การเรียง ที่ใช้อยู่ ส่งต่อไปพร้อมฟอร์ม ไม่ให้หายตอนกดกรอง
            'hidden': [(key, value) for key, value in changelist.params.items() if key not in ours],
            'clear_url': changelist.get_query_string(remove=list(ours)),
            'selected': bool(self.used_parameters),
        }


class WeightAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
        
    resource_class = WeightResource
    list_display = ['weight_id', 'doc_id', 'date', 'customer_name', 'mill_name' , 'stone_type_name', 'site_name', 'car_team_name', 'bws'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ('weight_id', 'doc_id', 'date', 'customer__customer_id' ,'customer_name', 'stone_type__base_stone_type_id', 'stone_type_name', 'base_weight_station_name', 'mill__mill_id' ,'mill_name', 'site__base_site_id', 'site_name', 'car_team__car_team_id', 'car_team_name')
    # กรองช่วงวันที่ ดู DateRangeListFilter
    list_filter = (('date', DateRangeListFilter),)

class WeightHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
        
    list_display = ['id', 'date', 'weight_id', 'user_update', 'doc_id', 'customer_name', 'mill_name' , 'stone_type_name', 'site_name', 'v_stamp', 'exp_note'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ('weight_id', 'date', 'doc_id', 'customer__customer_id', 'customer_name', 'stone_type__base_stone_type_id',  'stone_type_name', 'mill__mill_id' ,'mill_name', 'site__base_site_id', 'site_name', 'bws__id', 'v_stamp', 'update', 'user_update__first_name', 'exp_note')

class BaseCarRegistrationResource(resources.ModelResource):
    company_code = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget(BaseCompany, 'code'))

    class Meta:
        model = BaseCarRegistration
        import_id_fields = ('car_registration_id',)
        fields = ('car_registration_id', 'car_registration_name', 'car_type', 'company_code')
        export_order = ('car_registration_id', 'car_registration_name', 'car_type', 'company_code')

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(car_registration_id=instance.pk).update(car_registration_name=instance.car_registration_name)

class BaseCarRegistrationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseCarRegistrationResource
    list_display = ('car_registration_id', 'car_registration_name',)
    search_fields = ('car_registration_id', 'car_registration_name',)

class BaseDriverResource(resources.ModelResource):
    company_code = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget(BaseCompany, 'code'))

    class Meta:
        model = BaseDriver
        import_id_fields = ('driver_id',)
        fields = ('driver_id', 'driver_name', 'company_code')
        export_order = ('driver_id', 'driver_name', 'company_code')

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(driver_id=instance.pk).update(driver_name=instance.driver_name)

class BaseDriverAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseDriverResource
    list_display = ('driver_id', 'driver_name',)
    search_fields = ('driver_id', 'driver_name',)

class BaseScoopResource(resources.ModelResource):
    company_code = fields.Field(
        column_name='company',
        attribute='company',
        widget=ForeignKeyWidget(BaseCompany, 'code'))

    class Meta:
        model = BaseScoop
        import_id_fields = ('scoop_id',)
        fields = ('scoop_id', 'scoop_name', 'company_code')
        export_order = ('scoop_id', 'scoop_name', 'company_code')

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(scoop_id=instance.pk).update(scoop_name=instance.scoop_name)

class BaseScoopAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseScoopResource
    list_display = ('scoop_id', 'scoop_name',)
    search_fields = ('scoop_id', 'scoop_name',)

class BaseCarryTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_carry_type_id', 'base_carry_type_name',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseTransportTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_transport_id', 'base_transport_name',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseTransportTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_transport_id', 'base_transport_name',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseCarTeamResource(resources.ModelResource):

    class Meta:
        model = BaseCarTeam
        import_id_fields = ('car_team_id',)
        fields = ('car_team_id', 'car_team_name','oil_customer_id',)
        export_order = ('car_team_id', 'car_team_name','oil_customer_id',)

    #ถ้ามาจากการ Import ให้ update Weight ด้วย
    def after_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            Weight.objects.filter(car_team_id=instance.pk).update(car_team_name=instance.car_team_name)

class BaseCarTeamAdmin(ImportExportModelAdmin):
    resource_class = BaseCarTeamResource
    list_display = ('car_team_id', 'car_team_name', 'oil_customer_id',)
    search_fields = ('car_team_id', 'car_team_name', 'oil_customer_id',)

class BaseCarResource(resources.ModelResource):
    base_car_team_id = fields.Field(
        column_name='base_car_team',
        attribute='base_car_team',
        widget=ForeignKeyWidget(BaseCarTeam, 'car_team_id'))

    class Meta:
        model = BaseCar
        import_id_fields = ('car_id', 'base_car_team_id',)
        fields = ('car_id', 'car_name', 'base_car_team_id',)
        export_order = ('car_id', 'car_name', 'base_car_team_id',)

class BaseCarAdmin(ImportExportModelAdmin):
    resource_class = BaseCarResource
    list_display = ('car_id', 'car_name',)
    search_fields = ('car_id', 'car_name',)

class BaseFertilizerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['fertilizer_id', 'fertilizer_name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseCustomerSiteResource(resources.ModelResource):
    class Meta:
        model = BaseCustomerSite
        import_id_fields = ('customer', 'site',)
        fields = ('id', 'customer', 'site',)
        export_order = ('id', 'customer', 'site',)

class BaseCustomerSiteAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseCustomerSiteResource
    list_display = ('id','customer', 'site',)
    search_fields = ('id', 'customer__customer_name', 'site__base_site_name',)

class BaseAffiliatedCompanyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name', 'name_sh', 'name_th', 'name_eng']
    search_fields = ('name', 'name_sh', 'name_th', 'name_eng')
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseCompanyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['name', 'code', 'biz', 'step', 'aff_so'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_filter = ('aff_so',)
    # จำเป็นต้องมี เพราะ BaseCompanyMapBaseCustomerAdmin ใช้ autocomplete_fields ชี้มาที่ BaseCompany
    # ถ้าไม่มี Django จะขึ้น admin.E040 ตั้งแต่ตอน system check แล้วรันคำสั่งอะไรไม่ได้เลยทั้งโปรเจกต์
    search_fields = ('name', 'code')
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

PASSWORD_PLACEHOLDER = '●' * 8  # ●●●●●●●● shown when a password is already set

class UserScaleForm(forms.ModelForm):
    # autocomplete=new-password: กัน browser เติมรหัสผ่านของคนที่ login admin ลงในช่องนี้เอง
    password = forms.CharField(label="รหัสผ่าน", required=False, widget=forms.PasswordInput(render_value=True, attrs={'autocomplete': 'new-password'}))
    permission = forms.ChoiceField(label="สิทธิ์การใช้งาน", choices=UserScale.PERMISSION_CHOICES, required=False, initial=UserScale.PERMISSION_WEIGHT)

    class Meta:
        model = UserScale
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.pk and instance.password:
            self.initial['password'] = PASSWORD_PLACEHOLDER
        if instance and instance.pk and instance.permission:
            for value, _label in UserScale.PERMISSION_CHOICES:
                if hash_password_sha1(value) == instance.permission:
                    self.initial['permission'] = value
                    break

    def clean_scale_id(self):
        # ตาชั่งเก็บผู้ชั่งโดยใช้ scale_id เป็น username (unique) ถ้า scale_id ซ้ำ รายการที่แก้ทีหลังจะทับ
        # ชื่อ/รหัสผ่านของอีกคนในตาชั่ง ทำให้อีกคน login ไม่ได้
        scale_id = (self.cleaned_data.get('scale_id') or '').strip()
        if not scale_id:
            raise forms.ValidationError('กรุณาระบุรหัสผู้ชั่ง')
        dup = UserScale.objects.filter(scale_id=scale_id)
        if self.instance and self.instance.pk:
            dup = dup.exclude(pk=self.instance.pk)
        if dup.exists():
            raise forms.ValidationError('รหัสผู้ชั่ง %s มีอยู่แล้ว' % scale_id)
        return scale_id

    def clean_password(self):
        password = self.cleaned_data.get('password') or ''
        if password and password != PASSWORD_PLACEHOLDER:
            try:
                password.encode('ascii')
            except UnicodeEncodeError:
                # ตาชั่ง hash ด้วย Encoding.ASCII ตัวอักษรไทยจะกลายเป็น '?' รหัสผ่านจะไม่ตรงกัน
                raise forms.ValidationError('รหัสผ่านต้องเป็นตัวอักษรภาษาอังกฤษ ตัวเลข หรือสัญลักษณ์เท่านั้น')
        return password

class UserScaleAdmin(UserFullNameFieldMixin, ImportExportModelAdmin, admin.ModelAdmin):
    form = UserScaleForm
    autocomplete_fields = ['user']

    list_display = ['user', 'scale_id', 'scale_name', 'password', 'permission'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['scale_id', 'scale_name'] #ค้นหาตามรหัสผู้ชั่ง หรือชื่อผู้ชั่ง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

    def save_model(self, request, obj, form, change):
        new_password = form.cleaned_data.get('password')
        if new_password and new_password != PASSWORD_PLACEHOLDER:
            obj.password = hash_password_sha1(new_password)
        elif change:
            obj.password = UserScale.objects.get(pk=obj.pk).password
        else:
            obj.password = None

        new_permission = form.cleaned_data.get('permission')
        if new_permission:
            obj.permission = hash_password_sha1(new_permission)
        elif change:
            obj.permission = UserScale.objects.get(pk=obj.pk).permission
        else:
            obj.permission = None
        super().save_model(request, obj, form, change)

class BaseVisibleAdmin(ImportExportModelAdmin):
    list_display = ('name','step')
	
class UserProfileAdmin(UserFullNameFieldMixin, ImportExportModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    autocomplete_fields = ['user']
    
    list_display = ['user', 'first_name', 'last_name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_select_related = ['user']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ['user__username', 'user__first_name', 'user__last_name'] #ค้นหาตาม username, ชื่อ, นามสกุล

    def first_name(self, obj):
        return obj.user.first_name if obj.user else ''
    first_name.short_description = 'First name'
    first_name.admin_order_field = 'user__first_name'

    def last_name(self, obj):
        return obj.user.last_name if obj.user else ''
    last_name.short_description = 'Last name'
    last_name.admin_order_field = 'user__last_name'

class BaseSECAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    autocomplete_fields = ['customer']
    list_display = ['id', 'customer'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class SetWeightOYAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['comp',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class ProductionGoalAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['date', 'site', 'line_type', 'accumulated_goal', 'company'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['date', 'site__base_site_name', 'line_type__name',]
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class ProductionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['created', 'site', 'line_type', 'company'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['created', 'site__base_site_name', 'line_type__name',]
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class ProductionLossItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['production', 'loss_type', 'mc_type', 'loss_time'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['production__created', 'production__site__base_site_name', 'mc_type__name', 'loss_type__name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class StoneEstimateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['created', 'site', 'company'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['created', 'site__base_site_name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class StoneEstimateItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['se', 'stone_type', 'percent'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['se__created', 'se__site__base_site_name', 'stone_type__base_stone_type_name']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class SetCompStoneAdmin(ImportExportModelAdmin):
    list_display = ['comp', 'stone'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ['comp', 'comp__name', 'comp__code']

class SetPatternCodeAdmin(ImportExportModelAdmin):
    list_display = ['m_name', 'pattern', 'start', 'end'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ['m_name', 'pattern', 'start', 'end']

class BaseStockSourceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['name', 'symbol', 'step'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['name', 'step']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class StockAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'created', 'company'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'created', 'company']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class StockStoneAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'stone', 'total', 'stk'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'stone', 'total', 'stk']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class StockStoneItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'source', 'quantity', 'ssn'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'source', 'quantity', 'ssn']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class SetLineMessagingAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'target_id', 'note'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ['id', 'target_id', 'note']

class GasPriceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'created', 'cost', 'sell', 'company'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    search_fields = ['id', 'created', 'cost', 'sell', 'company']

class BaseMillSourceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseSiteStoreAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('id', 'name',)

class BaseBusinessAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class PortStockAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'created', 'company'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'created', 'company']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class PortStockStoneAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    autocomplete_fields = ['stone']

    list_display = ['id', 'stone', 'total', 'ps', 'ps_created']
    search_fields = [
        'id__startswith',        # ค้นหา id (int) แทน icontains
        'ps__created',           # วันที่ผลิต (DateField)
        'ps__id',
    ]
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    # method สำหรับแสดงค่าในตาราง
    def ps_created(self, obj):
        return obj.ps.created if obj.ps else '-'
    ps_created.short_description = 'วันที่ผลิต'

class PortStockStoneItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    autocomplete_fields = ['cus']

    list_display = ['id', 'cus', 'total', 'pss', 'pss_ps_created'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'cus', 'total', 'pss']

    search_fields = [
        'id__startswith',
        'cus__customer_id',
        'cus__customer_name',
        'pss__id',
        'pss__ps__created',
    ]
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    def pss_ps_created(self, obj):
        return obj.pss.ps.created if obj.pss.ps else '-'
    pss_ps_created.short_description = 'วันที่ผลิต'

class BaseWeightRangeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    list_display = ['id', 'name','descrip', 'rate_min', 'rate_max'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class LoadingRateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'created', 'date_start_rate' , 'company'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'created', 'date_start_rate', 'company']
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class LoadingRateLocAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    autocomplete_fields = ['Lr']

    list_display = ['id', 'Lr', 'Lr_created']
    search_fields = [
        'id__startswith',        # ค้นหา id (int) แทน icontains
        'Lr__created',           # วันที่ผลิต (DateField)
        'Lr__id',
    ]
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    # method สำหรับแสดงค่าในตาราง
    def Lr_created(self, obj):
        return obj.Lr.created if obj.Lr else '-'
    Lr_created.short_description = 'วันที่สร้าง'

class LoadingRateItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['id', 'wt_range', 'tru_scoop', 'tru_shipp', 'chi_scoop', 'chi_shipp', 'Lr_created'] #แสดงรายการสินค้าในรูปแบบตาราง
    search_fields = ['id', 'wt_range', 'tru_scoop', 'tru_shipp', 'chi_scoop', 'chi_shipp']

    search_fields = [
        'id__startswith',
        'wt_range__code',
        'wt_range__name',
        'Lrl__id',
        'Lr__created',
    ]
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
    def Lr_created(self, obj):
        return obj.Lr.created if obj.Lr else '-'
    Lr_created.short_description = 'วันที่สร้าง'

class BaseAPIAdmin(ImportExportModelAdmin):
    list_display = ['id','url','apiname','username', 'password'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า


class DeliveryOrderAdmin(ImportExportModelAdmin):
    search_fields = ['doc_no', 'comp_code', 'delivery_date', 'customer_code', 'customer_name', 'site_id', 'site_name']
    list_display = ['doc_no','comp_code','delivery_date','customer_code', 'customer_name', 'site_id', 'site_name', 'credit_type'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class WeightDeliveryAdmin(ImportExportModelAdmin):
    search_fields = ['do_doc_no', 'comp_code', 'delivery_date']
    list_display = ['do_doc_no','comp_code','delivery_date'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

admin.site.register(BaseVisible, BaseVisibleAdmin)
admin.site.register(BaseCustomerSite, BaseCustomerSiteAdmin)
admin.site.register(BaseVatType, BaseVatTypeAdmin)
admin.site.register(BaseWeightType, BaseWeightTypeAdmin)
admin.site.register(BaseWeightStation, BaseWeightStationAdmin)
admin.site.register(BaseLossType, BaseLossTypeAdmin)
admin.site.register(BaseMachineType, BaseMachineTypeAdmin)
admin.site.register(BaseMill, BaseMillAdmin)
admin.site.register(BaseLineType, BaseLineTypeAdmin)
admin.site.register(BaseJobType, BaseJobTypeAdmin)
admin.site.register(BaseCustomer, BaseCustomerAdmin)
admin.site.register(BaseStoneType, BaseStoneTypeAdmin)
admin.site.register(BaseStoneColor, BaseStoneColorAdmin)
admin.site.register(BaseTimeEstimate, BaseTimeEstimateAdmin)
admin.site.register(BaseSite, BaseSiteAdmin)
admin.site.register(Weight, WeightAdmin)
admin.site.register(WeightHistory, WeightHistoryAdmin)
admin.site.register(BaseCarRegistration, BaseCarRegistrationAdmin)
admin.site.register(BaseDriver, BaseDriverAdmin)
admin.site.register(BaseScoop, BaseScoopAdmin)
admin.site.register(BaseCarryType, BaseCarryTypeAdmin)
admin.site.register(BaseTransport, BaseTransportTypeAdmin)
admin.site.register(BaseCarTeam, BaseCarTeamAdmin)
admin.site.register(BaseCar, BaseCarAdmin)
admin.site.register(BaseFertilizer, BaseFertilizerAdmin)
admin.site.register(BaseAffiliatedCompany, BaseAffiliatedCompanyAdmin)
admin.site.register(BaseCompany, BaseCompanyAdmin)
admin.site.register(UserScale, UserScaleAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BaseSEC, BaseSECAdmin)
admin.site.register(SetWeightOY, SetWeightOYAdmin)
admin.site.register(Production, ProductionAdmin)
admin.site.register(ProductionGoal, ProductionGoalAdmin)
admin.site.register(ProductionLossItem, ProductionLossItemAdmin)
admin.site.register(StoneEstimate, StoneEstimateAdmin)
admin.site.register(StoneEstimateItem, StoneEstimateItemAdmin)
admin.site.register(SetCompStone, SetCompStoneAdmin)
admin.site.register(SetPatternCode, SetPatternCodeAdmin)
admin.site.register(BaseStockSource, BaseStockSourceAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(StockStone, StockStoneAdmin)
admin.site.register(StockStoneItem, StockStoneItemAdmin)
admin.site.register(SetLineMessaging, SetLineMessagingAdmin)
admin.site.register(GasPrice, GasPriceAdmin)
admin.site.register(BaseMillSource, BaseMillSourceAdmin)
admin.site.register(BaseSiteStore, BaseSiteStoreAdmin)
admin.site.register(BaseBusiness, BaseBusinessAdmin)
admin.site.register(PortStock, PortStockAdmin)
admin.site.register(PortStockStone, PortStockStoneAdmin)
admin.site.register(PortStockStoneItem, PortStockStoneItemAdmin)
admin.site.register(BaseWeightRange, BaseWeightRangeAdmin)
admin.site.register(LoadingRate, LoadingRateAdmin)
admin.site.register(LoadingRateLoc, LoadingRateLocAdmin)
admin.site.register(LoadingRateItem, LoadingRateItemAdmin)
admin.site.register(BaseAPI, BaseAPIAdmin)
admin.site.register(DeliveryOrder, DeliveryOrderAdmin)
admin.site.register(WeightDelivery, WeightDeliveryAdmin)

class AppReleaseTargetStationFormSet(forms.BaseInlineFormSet):
    # กันเลือกตาชั่งผิดโปรแกรม เช่น Blue.Master ต้องเป็นตาชั่ง xxV เท่านั้น
    # (ดรอปดาวน์กรองด้วย JS ใน admin/weightapp/apprelease/change_form.html อยู่แล้ว ตรงนี้เช็คซ้ำฝั่ง server)
    def clean(self):
        super().clean()
        suffix = AppRelease.station_suffix_for(self.instance.product_code)
        if not suffix:
            return
        wrong = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or form.cleaned_data.get('DELETE'):
                continue
            station = form.cleaned_data.get('weight_station')
            if station and not station.id.upper().endswith(suffix):
                wrong.append(station.id)
        if wrong:
            raise forms.ValidationError(
                'รหัสโปรแกรม %s เลือกได้เฉพาะตาชั่งที่ลงท้ายด้วย %s (ไม่ถูกต้อง: %s)'
                % (self.instance.product_code, suffix, ', '.join(wrong)))


class AppReleaseTargetStationInline(admin.TabularInline):
    # เลือกตาชั่งที่จะปล่อยเวอร์ชันนี้ให้ ถ้าไม่เพิ่มเลย = ปล่อยให้ทุกตาชั่ง
    model = AppReleaseTargetStation
    formset = AppReleaseTargetStationFormSet
    extra = 0
    verbose_name = 'ตาชั่งที่ปล่อยให้ (ไม่เพิ่มเลย = ทุกตาชั่ง)'
    verbose_name_plural = 'ตาชั่งที่ปล่อยให้ (ไม่เพิ่มเลย = ทุกตาชั่ง)'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'weight_station' and formfield is not None:
            # ดรอปดาวน์แสดง รหัส - ชื่อตาชั่ง (des) แทนรหัสอย่างเดียว
            formfield.queryset = formfield.queryset.order_by('id')
            formfield.label_from_instance = lambda s: f"{s.id} - {s.des}" if s.des else s.id
        return formfield

@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'version', 'channel', 'is_mandatory', 'is_active', 'has_sql_script', 'released_at', 'target_station_list', 'release_notes_short')
    list_filter = ('product_code', 'channel', 'is_active', 'target_stations')
    ordering = ('-released_at',)
    exclude = ('created_by',)
    inlines = [AppReleaseTargetStationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('target_stations')

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # ส่ง mapping รหัสโปรแกรม -> ท้ายรหัสตาชั่ง ให้ JS ใน change_form.html กรองดรอปดาวน์ตาชั่ง
        extra_context = extra_context or {}
        extra_context['product_station_suffix'] = AppRelease.PRODUCT_STATION_SUFFIX
        return super().changeform_view(request, object_id, form_url, extra_context)

    def target_station_list(self, obj):
        # แสดง รหัส - des ทีละบรรทัด
        stations = sorted(obj.target_stations.all(), key=lambda s: s.id)
        if not stations:
            return 'ทุกตาชั่ง'
        return format_html_join('', '<div>{}</div>', ((f"{s.id} - {s.des}" if s.des else s.id,) for s in stations))
    target_station_list.short_description = 'ปล่อยให้ตาชั่ง'

    def release_notes_short(self, obj):
        # ตัดให้สั้นในหน้ารายการ เอาเมาส์ชี้ดูข้อความเต็มได้
        notes = (obj.release_notes or '').strip()
        if not notes:
            return '-'
        short = notes if len(notes) <= 80 else notes[:80] + '…'
        return format_html('<span title="{}">{}</span>', notes, short)
    release_notes_short.short_description = 'รายละเอียดอัพเดท'

    def save_model(self, request, obj, form, change):
        if not change or not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_sql_script(self, obj):
        return bool(obj.sql_script)
    has_sql_script.boolean = True
    has_sql_script.short_description = 'มี SQL'

@admin.register(ClientUpdateLog)
class ClientUpdateLogAdmin(admin.ModelAdmin):
    list_display = ('machine_name', 'product_code', 'weight_station', 'from_version', 'to_version', 'update_applied', 'sql_applied', 'checked_at')
    list_filter = ('product_code', 'weight_station', 'update_applied')
    ordering = ('-checked_at',)


class BaseCompanyMapCustomerAliasInline(admin.TabularInline):
    # ใส่รหัสลูกค้าสำรองในหน้าแถว map เลย เช่น สุราษฎร์พอร์ท 06-V-024 มีรหัสสำรอง 77-V-007
    model = BaseCompanyMapCustomerAlias
    extra = 0
    autocomplete_fields = ['base_customer']


class BaseCompanyMapBaseCustomerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    # ติ๊กปลายทางส่งออกได้จากหน้ารายการเลย ไม่ต้องเปิดทีละแถว เวลาไล่เก็บกวาดทั้งตาราง
    list_display = ('id', 'name', 'base_company', 'base_customer', 'alias_codes',
                    'is_export_destination', 'is_domestic_destination', 'oi_soc_code')
    list_editable = ('is_export_destination', 'is_domestic_destination')
    list_filter = ('is_export_destination', 'is_domestic_destination')
    search_fields = ('base_company__name', 'base_customer__customer_name', 'oi_soc_code',
                     'customer_aliases__base_customer__customer_id')
    autocomplete_fields = ['base_company', 'base_customer']
    inlines = [BaseCompanyMapCustomerAliasInline]
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('customer_aliases')

    @admin.display(description='รหัสลูกค้าสำรอง')
    def alias_codes(self, obj):
        return ', '.join(a.base_customer_id for a in obj.customer_aliases.all()) or '-'

class BaseCompanyMapCustomerAliasAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    # เมนูแยกไว้ดูรวดเดียวว่าทั้งระบบมีรหัสสำรองกี่ตัว ชี้ไปแถว map ไหนบ้าง
    # ส่วนการเพิ่มระหว่างแก้แถว map ใช้ inline ในหน้า "ข้อมูลบริษัทลูกค้า" ได้เหมือนเดิม
    list_display = ('id', 'base_customer', 'alias_code', 'map_row', 'map_main_code', 'map_is_export')
    search_fields = ('base_customer__customer_id', 'base_customer__customer_name', 'map_row__name')
    autocomplete_fields = ['map_row', 'base_customer']
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('map_row', 'base_customer')

    @admin.display(description='รหัสลูกค้าสำรอง', ordering='base_customer_id')
    def alias_code(self, obj):
        return obj.base_customer_id

    @admin.display(description='รหัสหลักของแถว map')
    def map_main_code(self, obj):
        return obj.map_row.base_customer_id or '-'

    # รหัสสำรองไม่มีธงของตัวเอง ใช้ธงของแถวแม่ โชว์ไว้กันเข้าใจผิดว่าต้องไปติ๊กที่นี่
    @admin.display(description='แถว map ติ๊กปลายทางส่งออก', boolean=True)
    def map_is_export(self, obj):
        return obj.map_row.is_export_destination


class InternationalFreightRateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'origin', 'destination', 'version', 'status', 'effective_date', 'created_at')
    list_filter = ('status',)
    search_fields = ('id', 'origin__base_company__name', 'origin__base_customer__customer_name', 'destination__base_company__name', 'destination__base_customer__customer_name')
    list_per_page = 20

admin.site.register(BaseCompanyMapBaseCustomer, BaseCompanyMapBaseCustomerAdmin)
admin.site.register(BaseCompanyMapCustomerAlias, BaseCompanyMapCustomerAliasAdmin)
admin.site.register(InternationalFreightRate, InternationalFreightRateAdmin)

class InternationalFreightRateFuelPriceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'base_comp', 'date', 'average_fuel_price')
    list_filter = ('base_comp',)
    search_fields = ('base_comp__name', 'base_comp__code')
    list_per_page = 20

class CarryingweightRateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'min_weight', 'max_weight')
    search_fields = ('name', 'description')
    list_per_page = 20

class InternationalFreightRateTeamAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'international_freight_rate', 'team', 'weight_carried', 'freight_rate', 'fuel_freight_adjustment', 'discount_per_ton', 'credit_days')
    search_fields = ('team__car_team_name',)
    list_per_page = 20

admin.site.register(InternationalFreightRateFuelPrice, InternationalFreightRateFuelPriceAdmin)
admin.site.register(InternationalFreightRateTeam, InternationalFreightRateTeamAdmin)
admin.site.register(CarryingweightRate, CarryingweightRateAdmin)


# สำเนาข้อมูลชั่งจากตาชั่ง ไว้กู้ local DB ที่เสีย ดูอย่างเดียว ตาชั่งเป็นคนเขียน
from weightapp.models import WeightMirror


@admin.register(WeightMirror)
class WeightMirrorAdmin(admin.ModelAdmin):
    list_display = ('comp_code', 'mine_code', 'table_name', 'row_id', 'action', 'record_date', 'queued_at',
                    'received_at')
    list_filter = ('comp_code', 'mine_code', 'table_name', 'action', 'record_date')
    search_fields = ('row_id',)
    date_hierarchy = 'record_date'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
