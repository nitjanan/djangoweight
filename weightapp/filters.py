from django.db.models import fields
from django.db.models.fields import DateField
from django.forms.widgets import DateInput, TextInput
import django_filters
from django_filters import DateFilter
from .models import Weight, BaseWeightType, BaseWeightStation, BaseVatType, BaseMill, BaseLineType, Production
from django.utils.translation import gettext_lazy as _
from datetime import date

class WeightFilter(django_filters.FilterSet):
    start_created = django_filters.DateFilter(field_name = "date", lookup_expr='gte', widget=DateInput(attrs={'type':'date'}))
    end_created = django_filters.DateFilter(field_name = "date", lookup_expr='lte', widget=DateInput(attrs={'type':'date'}))
    doc_id = django_filters.CharFilter(field_name="doc_id", lookup_expr='icontains')
    customer_name = django_filters.CharFilter(field_name="customer_name", lookup_expr='icontains')
    stone_type = django_filters.CharFilter(field_name="stone_type", lookup_expr='icontains')
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
WeightFilter.base_filters['stone_type'].label = 'ชนิดหิน'
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
        

    def __init__(self, data, *args, **kwargs):
        if not data.get('start_created') and not data.get('end_created'):
            data = data.copy()
            data['start_created'] =  date.today().__str__()
            data['end_created'] =  date.today().__str__()
        super().__init__(data, *args, **kwargs)
    
ProductionFilter.base_filters['start_created'].label = 'วันที่'
ProductionFilter.base_filters['end_created'].label = 'ถึง'
ProductionFilter.base_filters['mill'].label = 'โรงโม่'
ProductionFilter.base_filters['line_type'].label = 'Line'