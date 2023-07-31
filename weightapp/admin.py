from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from weightapp.models import BaseWeightType, BaseWeightStation, BaseVatType, BaseLineType, BaseLossType, BaseMill, BaseJobType, BaseCustomer, BaseStoneType, BaseTimeEstimate

# Register your models here.
class BaseVatTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_vat_type_id', 'base_vat_type_name', 'base_vat_type_des'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseJobTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['base_job_type_id', 'base_job_type_name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseCustomerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['customer_id', 'customer_name'] #แสดงรายการสินค้าในรูปแบบตาราง
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
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseLineTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['id','name'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

class BaseTimeEstimateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['mill','time_name', 'time_from', 'time_to'] #แสดงรายการสินค้าในรูปแบบตาราง
    list_per_page = 20 #แสดงผล 20 รายการต่อ 1 หน้า

admin.site.register(BaseVatType, BaseVatTypeAdmin)
admin.site.register(BaseWeightType, BaseWeightTypeAdmin)
admin.site.register(BaseWeightStation, BaseWeightStationAdmin)
admin.site.register(BaseLossType, BaseLossTypeAdmin)
admin.site.register(BaseMill, BaseMillAdmin)
admin.site.register(BaseLineType, BaseLineTypeAdmin)
admin.site.register(BaseJobType, BaseJobTypeAdmin)
admin.site.register(BaseCustomer, BaseCustomerAdmin)
admin.site.register(BaseStoneType, BaseStoneTypeAdmin)
admin.site.register(BaseTimeEstimate, BaseTimeEstimateAdmin)

