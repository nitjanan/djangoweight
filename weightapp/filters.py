from django.db.models import fields
from django.db.models.fields import DateField
from django.forms.widgets import DateInput, TextInput
import django_filters
from django_filters import DateFilter
from .models import Weight, BaseWeightType, BaseWeightStation, BaseVatType, BaseMill, BaseLineType, Production, StoneEstimate, BaseStoneType, BaseScoop, BaseCarTeam, BaseCar, BaseSite, BaseCustomer, BaseDriver, BaseCarRegistration, BaseJobType
from django.utils.translation import gettext_lazy as _
from datetime import date

class WeightFilter(django_filters.FilterSet):
    start_created = django_filters.DateFilter(field_name = "date", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "date", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    doc_id = django_filters.CharFilter(field_name="doc_id", lookup_expr='icontains')
    customer_name = django_filters.CharFilter(field_name="customer_name", lookup_expr='icontains')
    stone_type_name = django_filters.CharFilter(field_name="stone_type_name", lookup_expr='icontains')
    weight_type =  django_filters.ModelChoiceFilter(field_name="base_weight_station_name__weight_type", queryset= BaseWeightType.objects.all())
    vat_type =  django_filters.ModelChoiceFilter(field_name="base_weight_station_name__vat_type", queryset= BaseVatType.objects.all())

    class Meta:
        model = Weight
        fields = ('doc_id', 'date', )
        
        #ดึงทุก field
        # fields = '__all__'

WeightFilter.base_filters['doc_id'].label = 'เลขที่ชั่ง'
WeightFilter.base_filters['start_created'].label = 'วันที่'
WeightFilter.base_filters['end_created'].label = 'ถึง'
WeightFilter.base_filters['customer_name'].label = 'ชื่อลูกค้า'
WeightFilter.base_filters['stone_type_name'].label = 'ชนิดหิน'
WeightFilter.base_filters['weight_type'].label = 'ประเภทชั่ง'
WeightFilter.base_filters['vat_type'].label = 'vat'


class ProductionFilter(django_filters.FilterSet):
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    mill =  django_filters.ModelChoiceFilter(field_name="mill", queryset= BaseMill.objects.all())
    line_type =  django_filters.ModelChoiceFilter(field_name="line_type", queryset= BaseLineType.objects.all())

    class Meta:
        model = Production
        fields = ('created', 'mill', 'line_type',)
        
    '''
    def __init__(self, data, *args, **kwargs):
        if not data.get('start_created') and not data.get('end_created'):
            data = data.copy()
            data['start_created'] =  date.today().__str__()
            data['end_created'] =  date.today().__str__()
        super().__init__(data, *args, **kwargs)    
    '''
    
ProductionFilter.base_filters['start_created'].label = 'วันที่'
ProductionFilter.base_filters['end_created'].label = 'ถึง'
ProductionFilter.base_filters['mill'].label = 'โรงโม่'
ProductionFilter.base_filters['line_type'].label = 'Line'

class StoneEstimateFilter(django_filters.FilterSet):
    start_created = django_filters.DateFilter(field_name = "created", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "created", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    mill =  django_filters.ModelChoiceFilter(field_name="mill", queryset= BaseMill.objects.all())

    class Meta:
        model = StoneEstimate
        fields = ('created', 'mill',)

StoneEstimateFilter.base_filters['start_created'].label = 'วันที่'
StoneEstimateFilter.base_filters['end_created'].label = 'ถึง'
StoneEstimateFilter.base_filters['mill'].label = 'โรงโม่'


class BaseMillFilter(django_filters.FilterSet):
    mill_id = django_filters.CharFilter(field_name="id", lookup_expr='icontains')
    mill_name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = BaseMill
        fields = ('mill_id', 'mill_name',)

BaseMillFilter.base_filters['mill_id'].label = 'รหัสโรงโม่'
BaseMillFilter.base_filters['mill_name'].label = 'ชื่อโรงโม่'


class BaseJobTypeFilter(django_filters.FilterSet):
    base_job_type_id = django_filters.CharFilter(field_name="base_job_type_id", lookup_expr='icontains')
    base_job_type_name = django_filters.CharFilter(field_name="base_job_type_name", lookup_expr='icontains')

    class Meta:
        model = BaseJobType
        fields = ('base_job_type_id', 'base_job_type_name',)

BaseJobTypeFilter.base_filters['base_job_type_id'].label = 'รหัสประเภทงานของลูกค้า'
BaseJobTypeFilter.base_filters['base_job_type_name'].label = 'ชื่อประเภทงานของลูกค้า'


class BaseStoneTypeFilter(django_filters.FilterSet):
    base_stone_type_id = django_filters.CharFilter(field_name="base_stone_type_id", lookup_expr='icontains')
    base_stone_type_name = django_filters.CharFilter(field_name="base_stone_type_name", lookup_expr='icontains')

    class Meta:
        model = BaseStoneType
        fields = ('base_stone_type_id', 'base_stone_type_name',)

BaseStoneTypeFilter.base_filters['base_stone_type_id'].label = 'รหัสหิน'
BaseStoneTypeFilter.base_filters['base_stone_type_name'].label = 'ชื่อหิน'


class BaseScoopFilter(django_filters.FilterSet):
    scoop_id = django_filters.CharFilter(field_name="scoop_id", lookup_expr='icontains')
    scoop_name = django_filters.CharFilter(field_name="scoop_name", lookup_expr='icontains')

    class Meta:
        model = BaseScoop
        fields = ('scoop_id', 'scoop_name',)

BaseScoopFilter.base_filters['scoop_id'].label = 'รหัสผู้ตัก'
BaseScoopFilter.base_filters['scoop_name'].label = 'ชื่อผู้ตัก'


class BaseCarTeamFilter(django_filters.FilterSet):
    car_team_id = django_filters.CharFilter(field_name="car_team_id", lookup_expr='icontains')
    car_team_name = django_filters.CharFilter(field_name="car_team_name", lookup_expr='icontains')

    class Meta:
        model = BaseCarTeam
        fields = ('car_team_id', 'car_team_name',)

BaseCarTeamFilter.base_filters['car_team_id'].label = 'รหัสทีม'
BaseCarTeamFilter.base_filters['car_team_name'].label = 'ชื่อทีม'


class BaseCarFilter(django_filters.FilterSet):
    car_id = django_filters.CharFilter(field_name="car_id", lookup_expr='icontains')
    car_name = django_filters.CharFilter(field_name="car_name", lookup_expr='icontains')

    class Meta:
        model = BaseCar
        fields = ('car_id', 'car_name', 'base_car_team')

BaseCarFilter.base_filters['car_id'].label = 'รหัสรถร่วม'
BaseCarFilter.base_filters['car_name'].label = 'ชื่อรถร่วม'
BaseCarFilter.base_filters['base_car_team'].label = 'ทีม'


class BaseSiteFilter(django_filters.FilterSet):
    base_site_id = django_filters.CharFilter(field_name="base_site_id", lookup_expr='icontains')
    base_site_name = django_filters.CharFilter(field_name="base_site_name", lookup_expr='icontains')
    base_customer = django_filters.CharFilter(field_name="base_customer__customer_name", lookup_expr='icontains')

    class Meta:
        model = BaseSite
        fields = ('base_site_id', 'base_site_name', 'base_customer')

BaseSiteFilter.base_filters['base_site_id'].label = 'รหัสหน้างาน'
BaseSiteFilter.base_filters['base_site_name'].label = 'ชื่อหน้างาน'
BaseSiteFilter.base_filters['base_customer'].label = 'ลูกค้า'


class BaseCustomerFilter(django_filters.FilterSet):
    customer_id = django_filters.CharFilter(field_name="customer_id", lookup_expr='icontains')
    customer_name = django_filters.CharFilter(field_name="customer_name", lookup_expr='icontains')

    class Meta:
        model = BaseCustomer
        fields = ('weight_type',  'customer_id', 'customer_name', 'base_vat_type', 'base_job_type',)

BaseCustomerFilter.base_filters['customer_id'].label = 'รหัสลูกค้า'
BaseCustomerFilter.base_filters['customer_name'].label = 'ชื่อลูกค้า'


class BaseDriverFilter(django_filters.FilterSet):
    driver_id = django_filters.CharFilter(field_name="driver_id", lookup_expr='icontains')
    driver_name = django_filters.CharFilter(field_name="driver_name", lookup_expr='icontains')

    class Meta:
        model = BaseDriver
        fields = ('driver_id',  'driver_name', )

BaseDriverFilter.base_filters['driver_id'].label = 'รหัสผู้ขับ'
BaseDriverFilter.base_filters['driver_name'].label = 'ชื่อผู้ขับ'

class BaseCarRegistrationFilter(django_filters.FilterSet):
    car_registration_id = django_filters.CharFilter(field_name="car_registration_id", lookup_expr='icontains')
    car_registration_name = django_filters.CharFilter(field_name="car_registration_name", lookup_expr='icontains')
    car_type = django_filters.CharFilter(field_name="car_type", lookup_expr='icontains')

    class Meta:
        model = BaseDriver
        fields = ('car_registration_id',  'car_registration_name', 'car_type')

BaseCarRegistrationFilter.base_filters['car_registration_id'].label = 'รหัสทะเบียนรถ'
BaseCarRegistrationFilter.base_filters['car_registration_name'].label = 'ชื่อทะเบียนรถ'
BaseCarRegistrationFilter.base_filters['car_type'].label = 'ประเภทรถ'


