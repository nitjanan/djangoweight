from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from weightapp.models import BaseWeightType, BaseWeightStation, BaseVatType, BaseLineType, BaseLossType, BaseMill, BaseJobType, BaseCustomer, BaseStoneType, BaseTimeEstimate, BaseSite, BaseStoneColor, Weight, WeightHistory, BaseCarRegistration, BaseDriver, BaseScoop, BaseCarryType, BaseTransport, BaseCarTeam, BaseCar, BaseFertilizer, BaseCustomerSite, BaseCompany, UserScale

# Register your models here.
class BaseVatTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_vat_type_id', 'base_vat_type_name', 'base_vat_type_des'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

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

class BaseCustomerAdmin(ImportExportModelAdmin):
    resource_class = BaseCustomerResource
    list_display = ('customer_id', 'customer_name',)
    search_fields = ('customer_id', 'customer_name')

class BaseSiteResource(resources.ModelResource):
    class Meta:
        model = BaseSite
        import_id_fields = ('base_site_id',)
        fields = ('base_site_id', 'base_site_name', 'weight_type')
        export_order = ('base_site_id', 'base_site_name', 'weight_type')

class BaseSiteAdmin(ImportExportModelAdmin):
    resource_class = BaseSiteResource
    list_display = ('base_site_id', 'base_site_name',)
    search_fields = ('base_site_id', 'base_site_name',)

class BaseStoneColorAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseStoneTypeResource(resources.ModelResource):
    class Meta:
        model = BaseStoneType
        import_id_fields = ('base_stone_type_id',)
        fields = ('base_stone_type_id', 'base_stone_type_name', 'cal_q')
        export_order = ('base_stone_type_id', 'base_stone_type_name', 'cal_q')

class BaseStoneTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseStoneTypeResource
    list_display = ('base_stone_type_id', 'base_stone_type_name',)
    search_fields = ('base_stone_type_id', 'base_stone_type_name',)

class BaseWeightTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseWeightStationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','des','weight_id_min','weight_id_max'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseLossTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseMillResource(resources.ModelResource):
    class Meta:
        model = BaseMill
        import_id_fields = ('mill_id',)
        fields = ('mill_id', 'mill_name', 'weight_type')
        export_order = ('mill_id', 'mill_name', 'weight_type')

class BaseMillAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = BaseMillResource
    list_display = ('mill_id', 'mill_name',)
    search_fields = ('mill_id', 'mill_name',)

class BaseLineTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseTimeEstimateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['mill','time_name', 'time_from', 'time_to'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class WeightAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['weight_id', 'doc_id',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class WeightHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id' , 'weight_id', 'user_update',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

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
        fields = ('car_team_id', 'car_team_name',)
        export_order = ('car_team_id', 'car_team_name',)

class BaseCarTeamAdmin(ImportExportModelAdmin):
    resource_class = BaseCarTeamResource
    list_display = ('car_team_id', 'car_team_name',)
    search_fields = ('car_team_id', 'car_team_name',)

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
    search_fields = ('id', 'customer', 'site',)

class BaseCompanyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['name', 'code'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class UserScaleAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['user', 'scale_id', 'scale_name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า
	
admin.site.register(BaseCustomerSite, BaseCustomerSiteAdmin)
admin.site.register(BaseVatType, BaseVatTypeAdmin)
admin.site.register(BaseWeightType, BaseWeightTypeAdmin)
admin.site.register(BaseWeightStation, BaseWeightStationAdmin)
admin.site.register(BaseLossType, BaseLossTypeAdmin)
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
admin.site.register(BaseCompany, BaseCompanyAdmin)
admin.site.register(UserScale, UserScaleAdmin)




