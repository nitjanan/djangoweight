import os
from django.contrib.auth import models
from django.contrib.auth.models import User
from django import forms
from django.db.models import fields
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.forms import fields, widgets, CheckboxSelectMultiple
from django.contrib.auth.forms import UserCreationForm
from weightapp.models import  Production, ProductionLossItem, BaseLossType, ProductionGoal, StoneEstimate, StoneEstimateItem, Weight, BaseSite, BaseMill, BaseStoneType
from django.utils.translation import gettext_lazy as _
from django.forms import (formset_factory, modelformset_factory, inlineformset_factory, BaseModelFormSet)
import string
from django.forms.widgets import TimeInput
from django.forms.models import BaseInlineFormSet

from django.forms.widgets import TextInput
from django.utils.dateparse import parse_duration

class DurationInput(TextInput):

    def _format_value(self, value):
        duration = parse_duration(value)

        seconds = duration.seconds

        minutes = seconds // 60
        seconds = seconds % 60

        minutes = minutes % 60

        return '{:02d}:{:02d}'.format(minutes, seconds)
    
class ProductionForm(forms.ModelForm):
    class Meta:
       model = Production
       fields = ('created', 'mill', 'line_type', 'goal','plan_start_time','plan_end_time','run_start_time','run_end_time','mile_run_start_time','mile_run_end_time','note',)
       widgets = {
        'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        'plan_start_time': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time','required': 'true'}),
        'plan_end_time': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time','required': 'true'}),
        'run_start_time': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time','required': 'true'}),
        'run_end_time': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time','required': 'true'}),
        'note': forms.Textarea(attrs={'class':'form-control','rows':2, 'cols':15}),
        }
       labels = {
            'created': _('วันที่ผลิต'),
            'mill': _('โรงโม่'),
            'line_type': _('Line'),
            'goal': _('เป้าต่อวัน (ตัน)'),
            'plan_start_time': _('ชั่วโมงตามแผน (เริ่ม)'),
            'plan_end_time': _('ชั่วโมงตามแผน (สิ้นสุด)'),
            'run_start_time': _('ชั่วโมงเดินเครื่อง (เริ่ม)'),
            'run_end_time': _('ชั่วโมงเดินเครื่อง (สิ้นสุด)'),
            'mile_run_start_time': _('เลขไมล์ (เริ่ม)'),
            'mile_run_end_time': _('เลขไมล์ (สิ้นสุด)'),
            'note': _('หมายเหตุ'),
       }

class ProductionModelForm(forms.ModelForm):

    class Meta:
        model = Production
        fields = ('created', 'mill', 'line_type', 'goal','plan_start_time','plan_end_time','run_start_time','run_end_time','note',)
        labels = {
                'created': _('วันที่สร้าง'),
                'mill': _('โรงโม่'),
                'line_type': _('Line'),
                'goal': _('เป้าต่อวัน (ตัน)'),
                'plan_start_time': _('ชั่วโมงตามแผน (เริ่ม)'),
                'plan_end_time': _('ชั่วโมงตามแผน (สิ้นสุด)'),
                'run_start_time': _('ชั่วโมงเดินเครื่อง (เริ่ม)'),
                'run_end_time': _('ชั่วโมงเดินเครื่อง (สิ้นสุด)'),
                'note': _('หมายเหตุ'),
        }
        widgets = {
            'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
            'plan_start_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'plan_end_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'run_start_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'run_end_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'note': forms.Textarea(attrs={'class':'form-control','rows':2, 'cols':15}),
        }

ProductionFormset = formset_factory(ProductionForm)
ProductionModelFormset = modelformset_factory(
    Production,
    fields=('created', 'mill', 'line_type', 'goal','plan_start_time','plan_end_time','run_start_time','run_end_time','note',),
    extra=1,
        widgets = {
            'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
            'plan_start_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'plan_end_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'run_start_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'run_end_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
            'note': forms.Textarea(attrs={'class':'form-control','rows':2, 'cols':15}),
        }
)

class ProductionLossItemForm(forms.ModelForm):
    class Meta:
       model = ProductionLossItem
       fields = ('loss_type', 'loss_time',)
       widgets = {
        'loss_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
        }

#form set create
'''
ProductionLossItemFormset = formset_factory(ProductionLossItemForm)
ProductionLossItemModelFormset = modelformset_factory(
    ProductionLossItem,
    fields=('loss_type', 'loss_time',),
    extra=1,
    can_delete=True,
    widgets={
        'loss_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
    }
)
'''

#ใช้จากหน้า view แล้ว (ProductionLossItemFormSet)
ProductionLossItemFormset = forms.modelformset_factory(
    ProductionLossItem,
    fields=('loss_type', 'loss_time'),
    extra= len(BaseLossType.objects.all()),  # Number of empty forms to display
    widgets={
        'loss_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
    }
)

ProductionLossItemInlineFormset = inlineformset_factory(
    Production,
    ProductionLossItem,
    form=ProductionLossItemForm,
    fields=('loss_type', 'loss_time'),
    widgets = {
        'loss_time': forms.TimeInput(attrs={'class':'form-control', 'type': 'time'}),
    },
    extra=1,
)


class ProductionGoalForm(forms.ModelForm):
    pk = forms.IntegerField(widget = forms.HiddenInput(), required = False)
    class Meta:
       model = ProductionGoal
       fields = ('accumulated_goal','pk')
       labels = {
            'accumulated_goal': _('เป้าที่คาดการณ์ของเดือนนี้'),
       }

#เปอร์เซ็นคาดการณ์คำนวณหินเบอร์
class StoneEstimateForm(forms.ModelForm):
    class Meta:
       model = StoneEstimate
       fields = ('created', 'mill',)
       widgets = {
        'created': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        }
       labels = {
            'created': _('วันที่ประมาณการณ์'),
            'mill': _('โรงโม่'),
       }

class StoneEstimateItemForm(forms.ModelForm):
    class Meta:
       model = StoneEstimateItem
       fields=('stone_type', 'percent')
       widgets = {
        }

#เปอร์เซ็นคาดการณ์คำนวณหินเบอร์
StoneEstimateItemInlineFormset = inlineformset_factory(
    StoneEstimate,
    StoneEstimateItem,
    form=StoneEstimateItemForm,
    fields=('stone_type', 'percent'),
    widgets = {  
    },
    extra=1,
)

class WeightForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super (WeightForm,self).__init__(*args,**kwargs)
        instance = kwargs.get('instance')

        if instance:
            # Access the attributes of the model instance if needed
            customer_id_value = instance.customer_id

        #เปลี่ยนการจัดกลุ่มเป็นแบบอื่นเพราะมีเคสที่ใช้เงื่อนไขนี้ไม่ได้
        #self.fields['site'] = forms.ModelChoiceField(label='หน้างาน', queryset = BaseSite.objects.filter(base_site_name = self.fields['site'], base_customer_id = self.fields['customer_id']))

    site = forms.ModelChoiceField(label='หน้างาน', queryset = BaseSite.objects.none())
    mill_name = forms.ModelChoiceField(label='โรงโม่', queryset = BaseMill.objects.all())
    stone_type = forms.ModelChoiceField(label='ชนิดหิน', queryset = BaseStoneType.objects.all())
    class Meta:
       model = Weight
       fields = ('date', 'doc_id', 'car_registration_id', 'car_registration_name', 'province','driver_id','driver_name', 'customer_id','customer_name','site','mill_id','mill_name','stone_type','carry_type_name', 'car_team', 'stone_color', 'scoop_id', 'scoop_name', 'note', 'weight_in', 'weight_out', 'weight_total', 'price_per_ton', 'vat', 'amount', 'amount_vat', 'oil_content')
       widgets = {
        'date': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        }
       labels = {
            'date': _('วันที่ผลิต'),
            'car_registration_id': _('รหัสทะเบียนรถ'),
            'car_registration_name': _('ทะเบียนรถ'),
            'province': _('ทะเบียน'),
            'driver_id': _('รหัสคนขับ'),
            'driver_name': _('ชื่อคนขับ'),

            'customer_name': _('ชื่อลูกค้า'),
            'mill_id': _('รหัสโรงโม่'),
            'mill_name': _('ชื่อโรงโม่'),
            'stone_type': _('ชื่อหิน'),
       }