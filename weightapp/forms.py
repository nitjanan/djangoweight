import os
from django.contrib.auth import models
from django.contrib.auth.models import User
from django import forms
from django.db.models import fields
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.forms import fields, widgets, CheckboxSelectMultiple
from django.contrib.auth.forms import UserCreationForm
from weightapp.models import  Production, ProductionLossItem, BaseLossType, ProductionGoal, StoneEstimate, StoneEstimateItem, Weight, BaseSite, BaseMill, BaseStoneType, BaseStoneColor, BaseCustomer, BaseCarRegistration, BaseDriver, BaseScoop, BaseTransport, BaseMill, BaseScoop, BaseCarTeam, BaseCar, BaseDriver, BaseCarRegistration, BaseJobType, BaseCustomerSite
from django.utils.translation import gettext_lazy as _
from django.forms import (formset_factory, modelformset_factory, inlineformset_factory, BaseModelFormSet)
import string
from django.forms.widgets import TimeInput
from django.forms.models import BaseInlineFormSet

from django.forms.widgets import TextInput
from django.utils.dateparse import parse_duration
import re

#new check error id 
def has_only_en(name):
    char_set = string.ascii_letters + string.digits + "-"
    return all((True if x in char_set else False for x in name))

class DurationInput(TextInput):

    def _format_value(self, value):
        duration = parse_duration(value)

        seconds = duration.seconds

        minutes = seconds // 60
        seconds = seconds % 60

        minutes = minutes % 60

        return '{:02d}:{:02d}'.format(minutes, seconds)

class WeightStockForm(forms.ModelForm):
    class Meta:
       model = Weight
       fields = ('mill_name',)
       widgets = {
        }
       labels = {
            'mill_name': _('โรงโม่'),
       }
       
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
    '''
    def __init__(self,request,*args,**kwargs):
        super (WeightForm,self).__init__(*args,**kwargs)
        instance = kwargs.get('instance')

        if instance:
            # Access the attributes of the model instance if needed
            customer_id_value = instance.customer_id

        #เปลี่ยนการจัดกลุ่มเป็นแบบอื่นเพราะมีเคสที่ใช้เงื่อนไขนี้ไม่ได้
        self.fields['site'] = forms.ModelChoiceField(label='หน้างาน', queryset = BaseSite.objects.filter(base_customer_id = customer_id_value), required=False)    
    '''

    ''' hidden
    mill_name = forms.ModelChoiceField(label='โรงโม่', queryset = BaseMill.objects.all())
    stone_type_name = forms.ModelChoiceField(label='ชนิดหิน', queryset = BaseStoneType.objects.all())
    scoop_name = forms.ModelChoiceField(label='ชื่อผู้ตัก', queryset = BaseScoop.objects.all())    
    '''

    stone_color = forms.ModelChoiceField(label='สีของหิน', queryset = BaseStoneColor.objects.all())
    transport = forms.ModelChoiceField(label='ขนส่ง', queryset = BaseTransport.objects.all() , required=False)

    class Meta:
       model = Weight
       fields = ('date', 'doc_id', 'car_registration', 'car_registration_name', 'province','driver','driver_name', 'customer','customer_name','site','site_name','mill','mill_name','stone_type', 'stone_type_name', 'transport','carry_type_name', 'car_team', 'car_team_name', 'stone_color', 'scoop', 'scoop_name', 'note', 'weight_in', 'weight_out', 'weight_total', 'q', 'price_per_ton', 'vat', 'amount', 'amount_vat', 'oil_content', 'pay', 'clean_type', 'vat_type', 'is_s', 'is_cancel')
       widgets = {
        'date': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        'site_name' : forms.HiddenInput(),
        'site' : forms.HiddenInput(),
        'carry_type_name': forms.HiddenInput(),
        'pay': forms.HiddenInput(),
        'clean_type': forms.HiddenInput(),
        'vat_type': forms.HiddenInput(),
        'mill_name': forms.HiddenInput(),
        'stone_type_name': forms.HiddenInput(),
        'scoop_name': forms.HiddenInput(),
        'car_team': forms.HiddenInput(),
        'car_team_name': forms.HiddenInput(),
        'is_s': forms.CheckboxInput(attrs={'style':'width:20px;height:20px;'}),
        'is_cancel': forms.CheckboxInput(attrs={'style':'width:20px;height:20px;'})
        }
       labels = {
            'date': _('วันที่ผลิต'),
            'car_registration': _('รหัสทะเบียนรถ'),
            'car_registration_name': _('ทะเบียนรถ'),
            'province': _('ทะเบียน'),
            'driver': _('รหัสคนขับ'),
            'driver_name': _('ชื่อคนขับ'),
            'customer_name': _('ชื่อลูกค้า'),
            'mill': _('รหัสโรงโม่'),
            'mill_name': _('ชื่อโรงโม่'),
            'stone_type_name': _('ชื่อหิน'),
            'transport': _('ขนส่ง'),
       }

class WeightStockForm(forms.ModelForm):
    customer = forms.ModelChoiceField(label='ลูกค้า', queryset = BaseCustomer.objects.filter(weight_type = 2))
    
    class Meta:
       model = Weight
       fields = ('date', 'doc_id', 'car_registration', 'car_registration_name','driver','driver_name', 'customer','customer_name','mill','mill_name','stone_type','stone_type_name', 'scoop', 'scoop_name', 'weight_in', 'weight_out', 'weight_total', 'site', 'site_name', 'note', 'is_cancel')
       widgets = {
        'date': forms.DateInput(attrs={'class':'form-control','size': 3 , 'placeholder':'Select a date', 'type':'date'}),
        'customer_name': forms.HiddenInput(),
        'mill_name': forms.HiddenInput(),
        'stone_type_name': forms.HiddenInput(),
        'car_registration_name': forms.HiddenInput(),
        'driver_name': forms.HiddenInput(),
        'scoop_name': forms.HiddenInput(),
        'site_name': forms.HiddenInput(),
       }
       labels = {
            'date': _('วันที่ผลิต'),
            'car_registration': _('รหัสทะเบียนรถ'),
            'car_registration_name': _('ทะเบียนรถ'),
            'province': _('ทะเบียน'),
            'driver': _('รหัสคนขับ'),
            'driver_name': _('ชื่อคนขับ'),
            'customer_name': _('ชื่อลูกค้า'),
            'mill': _('รหัสโรงโม่'),
            'mill_name': _('ชื่อโรงโม่'),
            'stone_type_name': _('ชื่อหิน'),
       }

class BaseMillForm(forms.ModelForm):
    class Meta:
       model = BaseMill
       fields = ('mill_id' , 'mill_name', 'weight_type')
       widgets = {
        }
       labels = {
            'mill_id': _('รหัสต้นทาง'),
            'mill_name': _('ชื่อต้นทาง'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('mill_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('mill_id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสต้นทางผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        elif not id or len(id) != 5 or not id.endswith("MA"):
            raise forms.ValidationError(u"รหัสควรมี  format 'xxxMA' (e.g., 012MA) กรุณาเปลี่ยนรหัสใหม่.")
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.mill_id = instance.mill_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance

class BaseJobTypeForm(forms.ModelForm):
    class Meta:
       model = BaseJobType
       fields = ('base_job_type_id' , 'base_job_type_name',)
       widgets = {
        }
       labels = {
            'base_job_type_id': _('รหัสประเภทงานของลูกค้า'),
            'base_job_type_name': _('ชื่อประเภทงานของลูกค้า'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('base_job_type_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('base_job_type_id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสประเภทงานผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.base_job_type_id = instance.base_job_type_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance


class BaseStoneTypeForm(forms.ModelForm):
    class Meta:
       model = BaseStoneType
       fields = ('base_stone_type_id' , 'base_stone_type_name', 'cal_q',)
       widgets = {
        }
       labels = {
            'base_stone_type_id': _('รหัสหิน'),
            'base_stone_type_name': _('ชื่อหิน'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('base_stone_type_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('base_stone_type_id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสหินผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        elif not id or len(id) != 4 or not id.endswith("ST"):
            raise forms.ValidationError(u"รหัสควรมี  format 'xxST' (e.g., 23ST) กรุณาเปลี่ยนรหัสใหม่.")
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.base_stone_type_id = instance.base_stone_type_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance

class BaseScoopForm(forms.ModelForm):
    class Meta:
       model = BaseScoop
       fields = ('scoop_id' , 'scoop_name', 'company')
       widgets = {
        }
       labels = {
            'scoop_id': _('รหัสผู้ตัก'),
            'scoop_name': _('ชื่อผู้ตัก'),
            'company': _('บริษัท'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('scoop_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('scoop_id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสผู้ตักผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        elif not id or len(id) != 4 or not id.endswith("TK"):
            raise forms.ValidationError(u"รหัสควรมี  format 'xxTK' (e.g., 23TK) กรุณาเปลี่ยนรหัสใหม่.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.scoop_id = instance.scoop_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance

class BaseCarTeamForm(forms.ModelForm):
    class Meta:
       model = BaseCarTeam
       fields = ('car_team_id' , 'car_team_name',)
       widgets = {
        }
       labels = {
            'car_team_id': _('รหัสทีม'),
            'car_team_name': _('ชื่อทีม'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('car_team_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.car_team_id = instance.car_team_id.replace(" ", "")

        if commit:
            instance.save()

        return instance

class BaseCarForm(forms.ModelForm):
    class Meta:
       model = BaseCar
       fields = ('base_car_team', 'car_id' , 'car_name', )
       widgets = {
        }
       labels = {
            'car_id': _('รหัสรถร่วม'),
            'car_name': _('ชื่อรถร่วม'),
            'base_car_team': _('ทีม'),
       }
    
    def clean_name_field(self):
        name_field = self.cleaned_data.get('car_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.car_id = instance.car_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance

class BaseSiteForm(forms.ModelForm):
    class Meta:
       model = BaseSite
       fields = ('base_site_id' , 'base_site_name', 'weight_type')
       widgets = {

        }
       labels = {
            'base_site_id': _('รหัสปลายทาง'),
            'base_site_name': _('ชื่อปลายทาง'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('base_site_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('base_site_id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสปลายทางผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        elif not id or len(id) != 5 or not id.endswith("PL"):
            raise forms.ValidationError(u"รหัสควรมี  format 'xxxPL' (e.g., 123PL) กรุณาเปลี่ยนรหัสใหม่.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.base_site_id = instance.base_site_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance

class BaseCustomerForm(forms.ModelForm):
    class Meta:
       model = BaseCustomer
       fields = ('weight_type', 'base_vat_type', 'base_job_type', 'customer_id', 'customer_name' , 'address', 'send_to',)
       widgets = {
           
        }
       labels = {
            'customer_id': _('รหัสลูกค้า'),
            'customer_name': _('ชื่อลูกค้า'),
            'address': _('ที่อยู่'),
            'send_to': _('ส่งที่'),
            'customer_type': _('ประเภทลูกค้า'),
            'base_vat_type': _('ชนิดvat'),
            'base_job_type': _('ประเภทงานของลูกค้า'),
            'weight_type': _('ชนิดเครื่องชั่ง'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('customer_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('customer_id')
        hoen = has_only_en(id)

        pattern1 = re.compile(r'^\d{2}RM$')
        pattern2 = re.compile(r'^\d{2}-V-\d{3}$')

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสลูกค้าผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        elif not id or not (pattern1.match(id) or pattern2.match(id)):
            raise forms.ValidationError(u"รหัสควรมี  format 'xx-V-xxx' หรือ 'xxRM' (e.g., 01-V-001, 01RM) กรุณาเปลี่ยนรหัสใหม่.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.customer_id = instance.customer_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance
    
class BaseCustomerSiteForm(forms.ModelForm):
    class Meta:
       model = BaseCustomerSite
       fields = ('customer' , 'site', )
       widgets = {
            'customer': forms.HiddenInput(),
            'site': forms.HiddenInput(),
        }
       labels = {
            'customer': _('ลูกค้า'),
            'site': _('ปลายทาง'),
       }


class BaseDriverForm(forms.ModelForm):
    class Meta:
       model = BaseDriver
       fields = ('driver_id', 'driver_name' ,'company')
       labels = {
            'driver_id': _('รหัสผู้ขับ'),
            'driver_name': _('ชื่อผู้ขับ'),
            'company': _('บริษัท'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('driver_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('driver_id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสผู้ขับผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        elif not id or len(id) != 4 or not id.endswith("KB"):
            raise forms.ValidationError(u"รหัสควรมี  format 'xxKB' (e.g., 23KB) กรุณาเปลี่ยนรหัสใหม่.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.driver_id = instance.driver_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance


# iterable 
CT_CHOICES =( 
    ("สิบล้อ", "สิบล้อ"), 
    ("จีน", "จีน"),
) 

class BaseCarRegistrationForm(forms.ModelForm):
    car_type = forms.ChoiceField(choices = CT_CHOICES)

    class Meta:
       model = BaseCarRegistration
       fields = ('car_registration_id', 'car_registration_name' ,'car_type','company')
       labels = {
            'car_registration_id': _('รหัสทะเบียนรถ'),
            'car_registration_name': _('ชื่อทะเบียนรถ'),
            'car_type': _('ประเภทรถ'),
            'company': _('บริษัท'),
       }

    def clean_name_field(self):
        name_field = self.cleaned_data.get('car_registration_name')
        if name_field:
            name_field = name_field.strip()  # Remove spaces from the beginning and end
        return name_field
    
    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('car_registration_id')
        hoen = has_only_en(id)

        if not hoen: #เช็คตัวอักษรภาษาไทยในรหัส
            raise forms.ValidationError(u"รหัสทะเบียนรถผิด ("+ str(id) +") มีตัวอักษรภาษาไทยหรือช่องว่าง ไม่สามารถบันทึกได้ กรุณาใส่รหัสใหม่")
        elif not id or len(id) != 5 or not id.endswith("CR"):
            raise forms.ValidationError(u"รหัสควรมี  format 'xxxCR' (e.g., 012CR) กรุณาเปลี่ยนรหัสใหม่.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.car_registration_id = instance.car_registration_id.upper().replace(" ", "")

        if commit:
            instance.save()

        return instance