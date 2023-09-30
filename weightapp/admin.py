from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from weightapp.models import BaseWeightType, BaseWeightStation, BaseVatType, BaseLineType, BaseLossType, BaseMill, BaseJobType, BaseCustomer, BaseStoneType, BaseTimeEstimate, BaseSite, BaseStoneColor, Weight, WeightHistory, BaseCarRegistration, BaseDriver, BaseScoop, BaseCarryType, BaseTransport, BaseCarTeam, BaseCar, BaseFertilizer, BaseCustomerSite

# Register your models here.
class BaseVatTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_vat_type_id', 'base_vat_type_name', 'base_vat_type_des'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseJobTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_job_type_id', 'base_job_type_name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

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
        import_id_fields = ('customer',)
        fields = ('customer_id', 'customer_name', 'base_vat_type', 'base_job_type')
        export_order = ('customer_id', 'customer_name', 'base_vat_type', 'base_job_type')

class BaseCustomerAdmin(ImportExportModelAdmin):
    resource_class = BaseCustomerResource
    list_display = ('customer_id', 'customer_name',)
    search_fields = ('customer_id', 'customer_name')

class BaseSiteResource(resources.ModelResource):
    base_customer_id = fields.Field(
        column_name='base_customer',
        attribute='base_customer',
        widget=ForeignKeyWidget(BaseCustomer, 'customer_id'))

    class Meta:
        model = BaseSite
        import_id_fields = ('base_site_id',)
        fields = ('base_site_id', 'base_site_name', 'base_customer_id',)
        export_order = ('base_site_id', 'base_site_name', 'base_customer_id',)

class BaseSiteAdmin(ImportExportModelAdmin):
    resource_class = BaseSiteResource
    list_display = ('base_site_id', 'base_site_name',)
    search_fields = ('base_site_id', 'base_site_name',)

class BaseStoneColorAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseStoneTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_stone_type_id', 'base_stone_type_name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseWeightTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseWeightStationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','des','weight_id_min','weight_id_max'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseLossTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseMillAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['mill_id','mill_name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

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

class BaseCarRegistrationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['car_registration_id', 'car_registration_name',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseDriverAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['driver_id', 'driver_name',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseScoopAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['scoop_id', 'scoop_name',] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

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

class BaseCustomerSiteAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['customer', 'site'] #แสดงรายการสินค้าในรูปแบบตาราง
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



