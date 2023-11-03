from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.cache import cache_page
from weightapp.models import Weight, Production, BaseLossType, ProductionLossItem, BaseMill, BaseLineType, ProductionGoal, StoneEstimate, StoneEstimateItem, BaseStoneType, BaseTimeEstimate, BaseCustomer, BaseSite, WeightHistory, BaseTransport, BaseCar, BaseScoop, BaseCarTeam, BaseCar, BaseDriver, BaseCarRegistration, BaseJobType, BaseCustomerSite, UserScale
from django.db.models import Sum, Q, Max
from decimal import Decimal
from django.views.decorators.cache import cache_control
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from .filters import WeightFilter, ProductionFilter, StoneEstimateFilter, BaseMillFilter, BaseStoneTypeFilter, BaseScoopFilter, BaseCarTeamFilter, BaseCarFilter, BaseSiteFilter, BaseCustomerFilter, BaseDriverFilter, BaseCarRegistrationFilter, BaseJobTypeFilter, BaseCustomerSiteFilter
from .forms import ProductionForm, ProductionLossItemForm, ProductionModelForm, ProductionLossItemFormset, ProductionLossItemInlineFormset, ProductionGoalForm, StoneEstimateForm, StoneEstimateItemInlineFormset, WeightForm, WeightStockForm, BaseMillForm, BaseStoneTypeForm ,BaseScoopForm, BaseCarTeamForm, BaseCarForm, BaseSiteForm, BaseCustomerForm, BaseDriverForm, BaseCarRegistrationForm, BaseJobTypeForm, BaseCustomerSiteForm
import xlwt
from django.db.models import Count, Avg
import stripe, logging, datetime
import openpyxl
from openpyxl.styles import PatternFill, Alignment, Font, Color, NamedStyle, Side, Border
from openpyxl.utils import get_column_letter
from datetime import date, timedelta, datetime, time
from django.views import generic
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django import forms
from django.db.models import Sum
import random
from django.db.models.functions import Coalesce
from django.db.models import F, ExpressionWrapper
from django.db import models
import pandas as pd
import calendar
from collections import defaultdict
from re import escape as reescape
from django.db.models import Value as V
from django.db.models.functions import Cast, Concat
from django.contrib.auth.decorators import login_required

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import generics, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from weightapp.serializers import BaseScoopSerializer, BaseMillSerializer, WeightSerializer, BaseCustomerSerializer, BaseStoneTypeSerializer, BaseCarTeamSerializer, BaseDriverSerializer, BaseCarRegistrationSerializer, BaseCarRegistrationSerializer, BaseCarSerializer, BaseSiteSerializer, BaseCarSerializer, BaseStoneTypeTestSerializer, BaseJobTypeSerializer, SignUpSerializer, BaseCustomerSiteSerializer
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from django.db import IntegrityError
from .tokens import create_jwt_pair_for_user
import csv
from io import StringIO

def generate_pastel_color():
    # Generate random pastel colors by restricting the RGB channels within a specific range
    red = random.randint(150, 255)
    green = random.randint(150, 255)
    blue = random.randint(150, 255)
    return f"{red:02x}{green:02x}{blue:02x}"

def set_border(ws, side=None, blank=True):
    wb = ws._parent
    side = side if side else Side(border_style='thin', color='000000')
    for cell in ws._cells.values():
        cell.border = Border(top=side, bottom=side, left=side, right=side)
    if blank:
        white = Side(border_style='thin', color='FFFFFF')
        wb._borders.append(Border(top=white, bottom=white, left=white, right=white))
        wb._cell_styles[0].borderId = len(wb._borders) - 1

def getSumByStone(mode, stoneType, type):
    start_date = datetime.strptime(startDateInMonth(str(datetime.today().strftime('%Y-%m-%d'))), "%Y-%m-%d")
    end_date = datetime.strptime(endDateInMonth(str(datetime.today().strftime('%Y-%m-%d'))), "%Y-%m-%d")

    #type 1 = sell, 2 = stock, 3 = produce
    if type == 1:
        w = Weight.objects.filter(bws__weight_type = mode, stone_type = stoneType, date__range=(start_date, end_date)).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')
    elif type == 2:
        w = Weight.objects.filter(Q(site='005PL') | Q(site='006PL') | Q(site='007PL')| Q(site='008PL'), bws__weight_type = mode, stone_type = stoneType, date__range=(start_date, end_date)).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0') 
    elif type == 3:
        w = Weight.objects.filter(Q(site='009PL') | Q(site='010PL') | Q(site='011PL'), bws__weight_type = mode, stone_type = stoneType, date__range=(start_date, end_date)).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')
    return  float(w)

def getSumOther(mode, list_sum_stone, type):
    start_date = datetime.strptime(startDateInMonth(str(datetime.today().strftime('%Y-%m-%d'))), "%Y-%m-%d")
    end_date = datetime.strptime(endDateInMonth(str(datetime.today().strftime('%Y-%m-%d'))), "%Y-%m-%d")

    query_filters = Q()
    for item_number_prefix in list_sum_stone:
        query_filters |= Q(stone_type = item_number_prefix)

    #type 1 = sell, 2 = stock, 3 = produce
    if type == 1:
        w = Weight.objects.filter(bws__weight_type = mode, date__range=(start_date, end_date)).exclude(query_filters).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')
    elif type == 2:
        w = Weight.objects.filter(Q(site='005PL') | Q(site='006PL') | Q(site='007PL')| Q(site='008PL'), bws__weight_type = mode, date__range=(start_date, end_date)).exclude(query_filters).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0') 
    elif type == 3:
        w = Weight.objects.filter(Q(site='009PL') | Q(site='010PL') | Q(site='011PL'), bws__weight_type = mode, date__range=(start_date, end_date)).exclude(query_filters).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')
    return  float(w)

def getNumListStoneWeightChart(mode, stone_list_id, type):
    #sell
    list_sum_stone = []
    for stone_id in stone_list_id:
        list_sum_stone.append(getSumByStone(mode, stone_id, type))

    list_sum_stone.append(getSumOther(mode, stone_list_id, type))
    #list_sum_stone.append(0.0)
    return list_sum_stone

# Create your views here.

@login_required(login_url='login')
def index(request):
    # today date
    current_date = datetime.now()
    previous_day = current_date - timedelta(days=1)

    weight = Weight.objects.filter(date = previous_day, bws__weight_type = 1).values('date','customer_name').annotate(sum_weight_total=Sum('weight_total')).order_by('-sum_weight_total')
    sum_all_weight = Weight.objects.filter(date = previous_day, bws__weight_type = 1).aggregate(s=Sum('weight_total'))["s"]

    data_sum_produc_all = Weight.objects.filter(Q(site='009PL') | Q(site='010PL') | Q(site='011PL'), date = previous_day, bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]
    data_sum_produc_mill1 = Weight.objects.filter(site='009PL' ,date = previous_day, bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]
    data_sum_produc_mill2 = Weight.objects.filter(site='010PL' ,date = previous_day, bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]
    data_sum_produc_mill3 = Weight.objects.filter(site='011PL' ,date = previous_day, bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]
    
    #'หิน 3/4', 'หิน 40/80', 'หินฝุ่น', 'หินคลุก A', 'หินคลุก B', 'อื่นๆ',
    sell_list_name = ['01ST','16ST','07ST','09ST','10ST']
    sell_list = getNumListStoneWeightChart(1, sell_list_name, 1)

    stock_list_name = ['01ST','16ST','07ST','09ST','10ST']
    stock_list = getNumListStoneWeightChart(2, stock_list_name, 2)

    produce_list_name = ['01ST','16ST','07ST','09ST','10ST']
    produce_list = getNumListStoneWeightChart(2, produce_list_name, 3)
    produce_list = [0.0, 0.0, 0.0, 0.0, 0.0]

    #list วันที่ทั้งหมด ระหว่าง startDate และ endDate
    start_date = datetime.strptime(startDateInMonth(str(datetime.today().strftime('%Y-%m-%d'))), "%Y-%m-%d")
    end_date = datetime.strptime(endDateInMonth(str(datetime.today().strftime('%Y-%m-%d'))), "%Y-%m-%d")
    now_date = datetime.strptime(str(datetime.today().strftime('%Y-%m-%d')), "%Y-%m-%d")

    ####################################
    ########### chart mill #############
    ####################################
    #สร้าง list ระหว่าง start_date และ end_date
    list_date_between = pd.date_range(start_date, end_date).tolist()
    list_date = [date.strftime("%Y-%m-%d") for date in list_date_between]

    sum_goal_mill_1 = ProductionGoal.objects.filter(date__year = f'{now_date.year}' , date__month = f'{now_date.month}' , mill__mill_name = 'โรงโม่ 1').aggregate(s=Sum('accumulated_goal'))["s"]
    sum_goal_mill_2 = ProductionGoal.objects.filter(date__year = f'{now_date.year}' , date__month = f'{now_date.month}' , mill__mill_name = 'โรงโม่ 2').aggregate(s=Sum('accumulated_goal'))["s"]
    sum_goal_mill_3 = ProductionGoal.objects.filter(date__year = f'{now_date.year}' , date__month = f'{now_date.month}' , mill__mill_name = 'โรงโม่ 3').aggregate(s=Sum('accumulated_goal'))["s"]

    list_goal_mill_1 = []
    list_goal_mill_2 = []
    list_goal_mill_3 = []

    weight_mill1 = Weight.objects.filter(
        date__range=(start_date, end_date),
        mill_name='โรงโม่ 1',
        stone_type_name__icontains='เข้าโม่'
    ).values('date').annotate(
        cumulative_total=Sum('weight_total', distinct=True),
    ).order_by('date')

    weight_mill2 = Weight.objects.filter(
        date__range=(start_date, end_date),
        mill_name='โรงโม่ 2',
        stone_type_name__icontains='เข้าโม่'
    ).values('date').annotate(
        cumulative_total=Sum('weight_total', distinct=True),
    ).order_by('date')

    weight_mill3 = Weight.objects.filter(
        date__range=(start_date, end_date),
        mill_name='โรงโม่ 3',
        stone_type_name__icontains='เข้าโม่'
    ).values('date').annotate(
        cumulative_total=Sum('weight_total', distinct=True),
    ).order_by('date')

    
    cumulative_total1 = 0
    cumulative_total2 = 0
    cumulative_total3 = 0
    for date in list_date:
        for w in weight_mill1:
            if str(date) == str(w['date']):
                cumulative_total1 += w['cumulative_total']
        list_goal_mill_1.append(calculatePersent(cumulative_total1, sum_goal_mill_1))

        for w in weight_mill2:
            if str(date) == str(w['date']):
                cumulative_total2 += w['cumulative_total']
        list_goal_mill_2.append(calculatePersent(cumulative_total2, sum_goal_mill_2))

        for w in weight_mill3:
            if str(date) == str(w['date']):
                cumulative_total3 += w['cumulative_total']
        list_goal_mill_3.append(calculatePersent(cumulative_total3, sum_goal_mill_3))

    ####################################
    ######## chart loss weight #########
    ####################################
    actual_working_time_all = Production.objects.filter(created__year = f'{now_date.year}' , created__month = f'{now_date.month}').annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']
    actual_working_time_mill1 = Production.objects.filter(created__year = f'{now_date.year}' , created__month = f'{now_date.month}', mill__mill_name = 'โรงโม่ 1').annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']
    actual_working_time_mill2 = Production.objects.filter(created__year = f'{now_date.year}' , created__month = f'{now_date.month}', mill__mill_name = 'โรงโม่ 2').annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']
    actual_working_time_mill3 = Production.objects.filter(created__year = f'{now_date.year}' , created__month = f'{now_date.month}', mill__mill_name = 'โรงโม่ 3').annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']

    total_loss_time_all = Production.objects.filter(created__range = (start_date, end_date)).aggregate(s=Sum('total_loss_time'))["s"]
    total_loss_time_mill1 = Production.objects.filter(created__range = (start_date, end_date), mill__mill_name = 'โรงโม่ 1').aggregate(s=Sum('total_loss_time'))["s"]
    total_loss_time_mill2 = Production.objects.filter(created__range = (start_date, end_date), mill__mill_name = 'โรงโม่ 2').aggregate(s=Sum('total_loss_time'))["s"]
    total_loss_time_mill3 = Production.objects.filter(created__range = (start_date, end_date), mill__mill_name = 'โรงโม่ 3').aggregate(s=Sum('total_loss_time'))["s"]
    
    persent_loss_weight_all = calculatePersent(total_loss_time_all if total_loss_time_all else None, actual_working_time_all)
    persent_loss_weight_mill1 = calculatePersent(total_loss_time_mill1 if total_loss_time_mill1 else None, actual_working_time_mill1)
    persent_loss_weight_mill2 = calculatePersent(total_loss_time_mill2 if total_loss_time_mill2 else None, actual_working_time_mill2)
    persent_loss_weight_mill3 = calculatePersent(total_loss_time_mill3 if total_loss_time_mill3 else None, actual_working_time_mill3)

    list_persent_loss_weight = [persent_loss_weight_mill3, persent_loss_weight_mill2, persent_loss_weight_mill1, persent_loss_weight_all]

    context = { 'weight': weight,
                'previous_day':previous_day,
                'actual_working_time_all':actual_working_time_all,
                'sum_all_weight': sum_all_weight,
                'sell_list':sell_list,
                'stock_list':stock_list,
                'produce_list':produce_list,
                'data_sum_produc_all':data_sum_produc_all,
                'data_sum_produc_mill1':data_sum_produc_mill1,
                'data_sum_produc_mill2':data_sum_produc_mill2,
                'data_sum_produc_mill3':data_sum_produc_mill3,
                'list_date': list_date,
                'list_goal_mill_1':list_goal_mill_1,
                'list_goal_mill_2':list_goal_mill_2,
                'list_goal_mill_3':list_goal_mill_3,
                'list_persent_loss_weight':list_persent_loss_weight,
                'dashboard_page':'active',}
    return render(request, "index.html",context)

def calculatePersent(num, num_all):
    persent = 0.0
    if num_all and num:
        persent = (num/num_all)*100
    return f'{round(persent)}'

def is_scale(user):
    return user.groups.filter(name='scale').exists()

def is_edit_weight(user):
    return user.groups.filter(name='edit_weight').exists()

def is_edit_setting(user):
    return user.groups.filter(name='edit_setting').exists()

def loginPage(request):
    if request.method == 'POST':
        form = AuthenticationForm(data = request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username,password=password)
            #ถ้าล็อกอินสำเร็จไปหน้า home else ให้ไปสมัครใหม่
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, "account/login.html", {'form':form,})

def logoutUser(request):
    logout(request)
    return redirect('login')

def weightTable(request):

    if is_scale(request.user):
        us = UserScale.objects.filter(user = request.user).values_list('scale_id')
        data = Weight.objects.filter(scale_id__in = us).order_by('date','weight_id')
    elif request.user.is_superuser:
        data = Weight.objects.all().order_by('date','weight_id')

    #กรองข้อมูล
    myFilter = WeightFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    weight = p.get_page(page)

    context = {'weight':weight,'filter':myFilter, 'weightTable_page':'active', }
    return render(request, "weight/weightTable.html",context)

@login_required
def editWeight(request, mode, weight_id):
    weight_data = get_object_or_404(Weight, pk=weight_id)

    if mode == 1:
        template_name = "weight/editWeightSell.html"
        tmp_form_post = WeightForm(request.POST, request.FILES, instance=weight_data)
        tmp_form = WeightForm(instance=weight_data)
    elif mode == 2:
        template_name = "weight/editWeightStock.html"
        tmp_form_post = WeightStockForm(request.POST, request.FILES, instance=weight_data)
        tmp_form = WeightStockForm(instance=weight_data)


    if request.method == 'POST':
        form = tmp_form_post
        if form.is_valid():
            # log history เก็บข้อมูลก่อนแก้
            weight_form = form.save()

            weight_history = WeightHistory.objects.filter(weight_id = weight_form.pk).order_by('-update')[0]
            weight_history.user_update = request.user
            weight_history.save()
            return redirect('weightTable')
    else:
        form = tmp_form

    context = {'weightTable_page': 'active', 'form': form, 'weight': weight_data, 'is_edit_weight': is_edit_weight(request.user)}
    return render(request, template_name, context)

def searchDataCustomer(request):
    if 'customer_id' in request.GET and 'weight_id' in request.GET:
        customer_id = request.GET.get('customer_id')

        site = BaseCustomerSite.objects.filter(customer = customer_id).values('site__base_site_id','site__base_site_name')
    data = {
        'site_list': list(site),
    }
    return JsonResponse(data)

def searchDataBaesCustomer(request):
    if 'customer_id' in request.GET :
        customer_id = request.GET.get('customer_id')
        try:
            customer = BaseCustomer.objects.get(customer_id = customer_id)
            val = customer.customer_id
        except BaseCustomer.DoesNotExist:
            val = None
    data = {
        'val': val,
    }
    return JsonResponse(data)

def setDataCustomer(request):
    if 'customer_id' in request.GET:
        customer_id = request.GET.get('customer_id')
        qs = BaseCustomer.objects.get(customer_id = customer_id)
        val = qs.customer_id + ":" + qs.customer_name
    data = {
        'val': val,
    }
    return JsonResponse(data)

def setDataSite(request):
    if 'site_id' in request.GET:
        site_id = request.GET.get('site_id')
        qs = BaseSite.objects.get(base_site_id = site_id)
        val = qs.base_site_id + ":" + qs.base_site_name
    data = {
        'val': val,
    }
    return JsonResponse(data)

def setDataCarryType(request):
    if 'transport_id' in request.GET:
        transport_id = request.GET.get('transport_id')
        qs = BaseTransport.objects.get(base_transport_id = transport_id)
        val = qs.base_carry_type.base_carry_type_name  
    data = {
        'val': val,
    }
    return JsonResponse(data)

def searchNumCalQ(request):
    if 'stone_type_id' in request.GET:
        stone_type_id = request.GET.get('stone_type_id')
        qs = BaseStoneType.objects.get(base_stone_type_id = stone_type_id)
        val = qs.cal_q
    data = {
        'val': val,
    }
    return JsonResponse(data)

def searchTeamFromCar(request):
    if 'car_registration_name' in request.GET :
        car_registration_name = request.GET.get('car_registration_name')

        team = BaseCar.objects.filter(car_name = car_registration_name).values('base_car_team__car_team_id','base_car_team__car_team_name')
    data = {
        'team_list': list(team),
    }
    return JsonResponse(data)

def autocompalteCustomer(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        qs = BaseCustomer.objects.filter(Q(customer_id__icontains = term) | Q(customer_name__icontains = term))[:15]
        titles = list()
        for obj in qs:
            titles.append(obj.customer_id +":"+ obj.customer_name)
    return JsonResponse(titles, safe=False)

def autocompalteSite(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        qs = BaseSite.objects.filter(Q(base_site_id__icontains = term) | Q(base_site_name__icontains = term))[:15]
        titles = list()
        for obj in qs:
            titles.append(obj.base_site_id +":"+ obj.base_site_name)
    return JsonResponse(titles, safe=False)

def excelProductionByStone(request, my_q, list_date):
    # Query ข้อมูลขาย
    data = Weight.objects.filter( Q(mill='010MA') | Q(mill='011MA') | Q(mill='012MA'),my_q, bws__weight_type = 1).order_by('date','mill','stone_type').values_list('date','mill_name', 'stone_type_name').annotate(sum_weight_total = Sum('weight_total'))
    # Query ข้อมูลผลิตรวม
    data_sum_produc = Weight.objects.filter( Q(site='009PL') | Q(site='010PL') | Q(site='011PL'),my_q, bws__weight_type = 2).order_by('date','site').values_list('date','site_name').annotate(sum_weight_total = Sum('weight_total'))

    # Create a new workbook and get the active worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    if data or data_sum_produc:
        date_style = NamedStyle(name='custom_datetime', number_format='DD/MM/YYYY')
        
        # Create a set of all unique mill and stone values
        mills = set()
        stones = set()
        for item in data:
            mills.add(item[1])
            stones.add(item[2]) 

        mill_col_list = []

        
        # Create a list of colors for each line_type
        mill_colors = [generate_pastel_color() for i  in range(len(mills) + 1)]

        column_index = 2 + len(mills)
        for mill in mills:
            worksheet.cell(row=1, column=column_index, value=f'ยอดขาย{mill}')
            worksheet.merge_cells(start_row=1, start_column = column_index, end_row=1, end_column=(column_index + len(stones)) -1 )
            
            cell = worksheet.cell(row=1, column=column_index)
            cell.alignment = Alignment(horizontal='center')

            info = {}
            info['mill'] = mill
            info['strat_col'] = column_index
            info['end_col'] = column_index + len(stones)
            mill_col_list.append(info)

            #อัพเดทจำนวน col ตามชนิดหิน
            column_index += len(stones)

        #set color in header in row 1-2
        for row in worksheet.iter_rows(min_row=1, max_row=2):
            # Set the background color for each cell in the column
            for cell in row:
                #cell.border = Border(top=side, bottom=side, left=side, right=side)
                cell.alignment = Alignment(horizontal='center')
                line_index = (cell.column - 5) // (len(stones))
                fill_color = mill_colors[line_index % len(mill_colors)]
                fill = PatternFill(start_color=fill_color, fill_type="solid")
                cell.fill = fill

        # Write headers row 2 to the worksheet
        column_index = 2 + len(mills)
        for mill in mills:
            for stone in stones:
                worksheet.cell(row=2, column=column_index, value=stone).alignment = Alignment(horizontal='center')
                column_index += 1

        # Create a dictionary to store data by date, mill, and stone
        date_data = {}

        # Loop through the data and populate the dictionary  
        for item in data:
            date = item[0]
            mill = item[1]
            stone = item[2]
            value = item[3]

            if date not in date_data:
                date_data[date] = {}

            if mill not in date_data[date]:
                date_data[date][mill] = {}

            date_data[date][mill][stone] = value

        row_index = 3
        for idl, ldate in enumerate(list_date):
            #เขียนวันที่ใน worksheet column 1
            worksheet.cell(row=idl+3, column=1, value=ldate).style = date_style
            worksheet.cell(row=idl+3, column=1).alignment = Alignment(horizontal='center')

            for date, mill_data in date_data.items():
                #เขียน weight total ของแต่ละหินใน worksheet
                if worksheet.cell(row=idl+3, column = 1).value == date:
                    column_index = 2 + len(mills)
                    for mill in mills:
                        stone_data = mill_data.get(mill, {})
                        for stone in stones:
                            value = stone_data.get(stone, '')
                            worksheet.cell(row=idl+3, column=column_index, value=value).number_format = '#,##0.00'
                            column_index += 1
                    #row_index += 1
            row_index += 1    

        #นำข้อมูลการผลิตมาเรียง
        sorted_queryset = sorted(data_sum_produc, key=lambda x: x[0])

        # Create a dictionary to store the summed values by date and mill_name
        summed_values = {}
        for date, mill_name, value in sorted_queryset:
            key = (date, mill_name)
            summed_values[key] = summed_values.get(key, 0) + float(value)

        mill_produc_list = []

        # Create headers
        headers = ['Date'] + list(set(row[1] for row in sorted_queryset))
        for col_num, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = f'ยอดผลิต{header}'
            cell.alignment = Alignment(horizontal='center')
            worksheet.merge_cells(start_row=1, start_column = col_num, end_row=2, end_column=col_num)

            info = {}
            if header != 'Date':
                info['mill'] = header
                info['col'] = col_num
                mill_produc_list.append(info)


        # Fill in the data ยืด วันที่ จาก วันที่ขายทั้งหมด set(row[0] for row in data หากยึด วันที่ตามวันที่ผลิต set(row[0] for row in sorted_queryset
        for row_num, date in enumerate(sorted(set(row for row in list_date)), 2):
            #worksheet.cell(row=row_num, column=4, value=date)
            row_num += 1 
            for col_num, mill_name in enumerate(headers[1:], 2):
                key = (date, mill_name)
                value = summed_values.get(key, '')
                worksheet.cell(row=row_num, column=col_num, value=value).number_format = '#,##0.00'
        

        # Write headers row 1 to the worksheet
        worksheet.cell(row=1, column=1, value='Date')

        worksheet.cell(row=row_index, column=1, value='รวมทั้งสิ้น')
        sum_by_col = Decimal('0.00')
        for col in range(2, column_index):
            for row in range(3, row_index):
                sum_by_col = sum_by_col + Decimal( worksheet.cell(row=row, column=col).value or '0.00' )
            worksheet.cell(row=row_index, column=col, value=sum_by_col).number_format = '#,##0.00'
            worksheet.cell(row=row_index, column=col).font = Font(bold=True)
            sum_by_col = Decimal('0.00')

        #คิดเป็นเปอร์เซ็น
        worksheet.cell(row=row_index+1, column=1, value="เปอร์เซ็นต์เฉลี่ย")
        for col, produc in zip(mill_col_list, mill_produc_list):
            if col['mill'] == produc['mill']:
                for i in range(col['strat_col'], col['end_col']):
                    sum_produc_val = Decimal(worksheet.cell(row=row_index, column = produc['col']).value or '1.00' )
                    val = Decimal(worksheet.cell(row=row_index, column = i).value or '1.00' )
                    percent = int(val/sum_produc_val * 100)

                    worksheet.cell(row=row_index+1, column=i, value = " " if val == Decimal('1.00') else f'{percent}%').alignment = Alignment(horizontal='right')
                    worksheet.cell(row=row_index+1, column=i).font = Font(color="FF0000")

        # Set the column widths
        for column_cells in worksheet.columns:
            max_length = 0
            column = column_cells[2].column_letter
            for cell in column_cells:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column].width = adjusted_width
            worksheet.column_dimensions[column].height = 20

        side = Side(border_style='thin', color='000000')
        set_border(worksheet, side)
    else:
        worksheet.cell(row = 1, column = 1, value = f'ไม่มีข้อมูลยอดผลิตตามประเภทหินของเดือนนี้')

    # Set the response headers for the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=export.xlsx'

    # Save the workbook to the response
    workbook.save(response)
    return response

def exportExcelProductionByStone(request):

    doc_id = request.GET.get('doc_id') or None
    start_created = request.GET.get('start_created') or None
    end_created = request.GET.get('end_created') or None
    customer_name = request.GET.get('customer_name') or None
    stone_type = request.GET.get('stone_type') or None

    my_q = Q()
    if doc_id is not None:
        my_q &= Q(doc_id__icontains = doc_id)
    if start_created is not None:
        my_q &= Q(date__gte = start_created)
    if end_created is not None:
        my_q &=Q(date__lte = end_created)
    if customer_name is not None :
        my_q &=Q(customer_name__icontains = customer_name)
    if stone_type is not None :
        my_q &=Q(stone_type_name__icontains = stone_type)

    my_q &= ~Q(customer_name ='ยกเลิก')
   
    startDate = datetime.strptime(start_created or startDateInMonth(datetime.today().strftime('%Y-%m-%d')), "%Y-%m-%d").date()
    endDate = datetime.strptime(end_created or datetime.today().strftime('%Y-%m-%d'), "%Y-%m-%d").date()

    #สร้าง list ระหว่าง start_date และ end_date
    list_date = [startDate+timedelta(days=x) for x in range((endDate-startDate).days + 1)]

    response = excelProductionByStone(request, my_q, list_date)
    return response

def exportExcelProductionByStoneInDashboard(request):
    #ดึงรายงานของเดือนนั้นๆ
    end_created = datetime.today().strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)

    my_q = Q()
    if start_created is not None:
        my_q &= Q(date__gte = start_created)
    if end_created is not None:
        my_q &=Q(date__lte = end_created)
    my_q &= ~Q(customer_name ='ยกเลิก')

    #เปลี่ยนออกเป็น ดึงรายงานของเดือนนั้นๆเท่านั้น
    startDate = datetime.strptime(start_created, "%Y-%m-%d").date()
    endDate = datetime.strptime(end_created, "%Y-%m-%d").date()

    #สร้าง list ระหว่าง start_date และ end_date
    list_date = [startDate+timedelta(days=x) for x in range((endDate-startDate).days + 1)]

    response = excelProductionByStone(request, my_q, list_date)
    return response

def viewProduction(request):
    data = Production.objects.all().order_by('-created', 'mill')

    #กรองข้อมูล
    myFilter = ProductionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    product = p.get_page(page)

    context = {'production_page':'active', 'product': product,'filter':myFilter, }
    return render(request, "production/viewProduction.html",context)

def calculatorDiffTime(request, start_time, end_time):
    difference = None
    if start_time is None:
        start_time = timedelta(hours=0, minutes=0) 
    if end_time is None:
        end_time = timedelta(hours=0, minutes=0)
    difference = end_time - start_time
    return difference

def calculatorDiff(request, val1, val2):
    difference = None
    if val1 is None:
        val1 = Decimal('0.0')
    if val2 is None:
        val2 = Decimal('0.0')
    difference = val2 - val1
    return difference

def setDurationTime(request, duration):
    result = None
    if duration is not None:
        if str(duration).startswith('0:'):
            _ , hours, minutes  = map(int, str(duration).split(':'))
        else:
            hours, minutes, _  = map(int, str(duration).split(':'))
        result = timedelta(hours=hours, minutes=minutes)

    return result

def searchProductionGoal(request):
    if 'mill_id' in request.GET and 'line_type_id' in request.GET and 'created' in request.GET and 'pd_id' in request.GET:
        mill_id = request.GET.get('mill_id')
        line_type_id = request.GET.get('line_type_id')
        created =  request.GET.get('created')
        pd_id =  request.GET.get('pd_id')

        date_object = datetime.strptime(created, "%Y-%m-%d")

        #เอาออก line_type__id = line_type_id เพราะโรงโม่เดียวกันใช้เป้าผลิตเท่ากัน
        pd_goal = ProductionGoal.objects.filter(date__year = f'{date_object.year}' , date__month = f'{date_object.month}' , mill__mill_id = mill_id).values('mill', 'line_type', 'date' , 'accumulated_goal', 'id')
        #if pd_id == '' create mode , else edit mode
        if pd_id == '':
            have_production = Production.objects.filter(created = created, mill__mill_id = mill_id, line_type__id = line_type_id ).exists()
        else:
            have_production = Production.objects.filter(~Q(id = pd_id), created = created, mill__mill_id = mill_id, line_type__id = line_type_id ).exists()
        #ดึงข้อมูล line 1 มาเพื่อไป set default ใน line อื่นๆ
        pd_line1 = Production.objects.filter(created = created, mill__mill_id = mill_id, line_type__id = 1).values('plan_start_time', 'plan_end_time')
        
        
    data = {
        'pd_goal_list': list(pd_goal),
        'have_production' :have_production,
        'pd_line1': list(pd_line1),
    }
    
    return JsonResponse(data)

def createProduction(request):
    base_loss_type = BaseLossType.objects.all()

    ProductionLossItemFormSet = modelformset_factory(ProductionLossItem, fields=('loss_type', 'loss_time'), extra=len(base_loss_type), widgets={'loss_time': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time'}),})
    if request.method == 'POST':
        pd_goal_form = ProductionGoalForm(request.POST)
        production_form = ProductionForm(request.POST)
        formset = ProductionLossItemFormSet(request.POST)
        if production_form.is_valid() and formset.is_valid() and pd_goal_form.is_valid():
            production = production_form.save()

            if pd_goal_form.cleaned_data['pk']:
                pd_goal = ProductionGoal.objects.get(id = pd_goal_form.cleaned_data['pk'])
                pd_goal.accumulated_goal = pd_goal_form.cleaned_data['accumulated_goal']
            else:
                pd_goal = ProductionGoal.objects.create(accumulated_goal = pd_goal_form.cleaned_data['accumulated_goal'])
            
            pd_goal.mill = production.mill
            pd_goal.line_type = production.line_type
            pd_goal.date = production.created
            pd_goal.save()

            production.pd_goal = pd_goal

            formset_instances = formset.save(commit=False)
            for instance in formset_instances:
                instance.production = production
                instance.save()

            #คำนวนเวลารวมในการสูญเสีย
            total_loss_time = ProductionLossItem.objects.filter(production = production).aggregate(s=Sum("loss_time"))["s"]
            production.total_loss_time = total_loss_time if total_loss_time else timedelta(hours=0, minutes=0)
            production.save()

            return redirect('viewProduction')
    else:
        production_form = ProductionForm()
        pd_goal_form = ProductionGoalForm()
        formset = ProductionLossItemFormSet(queryset=ProductionLossItem.objects.none())

    context = {'production_page':'active', 'pd_goal_form': pd_goal_form, 'form': production_form, 'formset': formset, 'base_loss_type':base_loss_type,}
    return render(request, "production/createProduction.html",context)

def editProduction(request, pd_id):
    pd_data = Production.objects.get(id = pd_id)

    #หาบันทึกปฎิบัติการของวันนี้ เพื่อเช็คไม่ให้ save mill และ line ซ้ำกัน
    production_on_day = Production.objects.filter(~Q(id = pd_data.id), created = datetime.today()).values('mill', 'line_type', 'created')

    if request.method == "POST":
        formset = ProductionLossItemInlineFormset(request.POST, request.FILES, instance=pd_data)
        form = ProductionForm(request.POST, request.FILES, instance=pd_data)
        pd_goal_form = ProductionGoalForm(request.POST, request.FILES, instance=pd_data.pd_goal)

        if form.is_valid() and formset.is_valid() and pd_goal_form.is_valid():
            # save production
            production = form.save()

            if pd_goal_form.cleaned_data['pk']:
                pd_goal = ProductionGoal.objects.get(id = pd_goal_form.cleaned_data['pk'])
                pd_goal.accumulated_goal = pd_goal_form.cleaned_data['accumulated_goal']
            else:
                pd_goal = ProductionGoal.objects.create(accumulated_goal = pd_goal_form.cleaned_data['accumulated_goal'])
            
            pd_goal.mill = production.mill
            pd_goal.line_type = production.line_type
            pd_goal.date = production.created
            pd_goal.save()

            production.pd_goal = pd_goal

            # save ProductionLossItem
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()

            #คำนวนเวลารวมในการสูญเสีย
            total_loss_time = ProductionLossItem.objects.filter(production = production).aggregate(s=Sum("loss_time"))["s"]
            production.total_loss_time = total_loss_time if total_loss_time else timedelta(hours=0, minutes=0)
            production.save()
            return redirect('viewProduction')
    else:
        formset = ProductionLossItemInlineFormset(instance=pd_data)
        form = ProductionForm(instance=pd_data)
        pd_goal_form = ProductionGoalForm(instance=pd_data.pd_goal)

    context = {'production_page':'active', 'pd_goal_form': pd_goal_form, 'form': form, 'formset': formset, 'pd': pd_data, 'production_on_day': production_on_day}
    return render(request, "production/editProduction.html",context)

def removeProduction(request, pd_id):
    pd = Production.objects.get(id = pd_id)
    #ลบ ProductionLossItem ใน Production ด้วย
    items = ProductionLossItem.objects.filter(production = pd)
    items.delete()
    #ลบ Production ทีหลัง
    pd.delete()
    return redirect('viewProduction')

#หาวันแรกของเดือนนี้
def startDateInMonth(day):
    dt = datetime.strptime(f"{day}", '%Y-%m-%d')
    result = dt.replace(day=1).date()
    return f"{result}"

#หาวันสุดท้ายของเดือนนี้
def endDateInMonth(day):
    dt = datetime.strptime(f"{day}", '%Y-%m-%d')
    day = calendar.monthrange(dt.year, dt.month)[1]
    result = dt.replace(day=day).date()
    return f"{result}"

def calculatCapacityPerHour(request, data_sum_produc, accumulated_produc):
    result = Decimal('0.0')
    if data_sum_produc and accumulated_produc:
        result = data_sum_produc/accumulated_produc/24
    return result

def formatHourMinute(time):
    result = None
    if time:
       #result = (datetime.min + time).strftime("%H:%M") or None
       result = f'{time}'[:-3]
    return result

def excelProductionAndLoss(request, my_q):
    count_loss = BaseLossType.objects.all()
    pd_mills = Production.objects.filter(my_q).values_list('mill', flat=True).distinct()
    mills = BaseMill.objects.filter(mill_id__in = pd_mills)

    workbook = openpyxl.Workbook()
    for mill in mills:
        sheet = workbook.create_sheet(title=mill.mill_name)

        # Fetch distinct line types for the current mill
        line_types = Production.objects.filter(my_q, mill=mill).values_list('line_type', flat=True).distinct()

        line_type =  BaseLineType.objects.filter(id__in=line_types)

        # Create a list of colors for each line_type
        line_type_colors = [generate_pastel_color() for i  in range(len(line_type) + 1)]

        column_index = 2
        for line in line_type:
            sheet.cell(row=1, column = column_index, value = line.name)
            sheet.merge_cells(start_row=1, start_column = column_index, end_row=1, end_column= (column_index + len(count_loss) + 14) -1 )
            sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')
            column_index += len(count_loss) + 14

        headers2 = ['Date']
        for i in  range(len(line_type)):
            headers2.extend(['เป้าต่อวัน','เป้าสะสม(ตัน)', 'ชั่วโมงตามแผน', 'ชั่วโมงตามแผน', 'ชั่วโมงทำงาน', 'ชั่วโมงเดินเครื่อง', 'ชั่วโมงเดินเครื่อง', 'ชั่วโมงเดินเครื่อง'])
            headers2.extend(['เวลาในการสูญเสีย' for i in range(len(count_loss))])
            headers2.extend(['รวม','ชั่วโมงการทำงานจริง', 'ยอดผลิต (ตัน)','ยอดผลิตสะสม','กำลังการผลิต (ตัน/ชั่วโมง)','หมายเหตุ',])

        sheet.append(headers2)

        merge_cells_num = 0
        headers3 = ['Date']
        for i in  range(len(line_type)):
            headers3.extend(['เป้าต่อวัน','เป้าสะสม(ตัน)', '(เริ่ม)', '(สิ้นสุด)', 'ชั่วโมงทำงาน', '(เริ่ม)', '(สิ้นสุด)', 'ชั่วโมงเดินเครื่อง'])
            headers3.extend([loss_type.name for loss_type in BaseLossType.objects.all()])
            headers3.extend(['รวมเวลา','ชั่วโมงการทำงานจริง', 'ยอดผลิต (ตัน)','ยอดผลิตสะสม','กำลังการผลิต (ตัน/ชั่วโมง)','หมายเหตุ',])
            # merge_cells headers เป้าต่อวัน, เป้าสะสม(ตัน),ชั่วโมงทำงาน,ชั่วโมงเดินเครื่อง
            sheet.merge_cells(start_row=2, start_column = 2 + merge_cells_num , end_row=3, end_column = 2 + merge_cells_num)
            sheet.merge_cells(start_row=2, start_column = 3 + merge_cells_num , end_row=3, end_column = 3 + merge_cells_num)
            sheet.merge_cells(start_row=2, start_column = 6 + merge_cells_num , end_row=3, end_column = 6 + merge_cells_num)
            sheet.merge_cells(start_row=2, start_column = 9 + merge_cells_num , end_row=3, end_column = 9 + merge_cells_num)
            sheet.merge_cells(start_row=2, start_column = 10 + merge_cells_num + len(count_loss) , end_row=3, end_column = 10 + merge_cells_num + len(count_loss))
            sheet.merge_cells(start_row=2, start_column = 11 + merge_cells_num + len(count_loss) , end_row=3, end_column = 11 + merge_cells_num + len(count_loss))
            sheet.merge_cells(start_row=2, start_column = 12 + merge_cells_num + len(count_loss) , end_row=3, end_column = 12 + merge_cells_num + len(count_loss))
            sheet.merge_cells(start_row=2, start_column = 13 + merge_cells_num + len(count_loss) , end_row=3, end_column = 13 + merge_cells_num + len(count_loss))
            sheet.merge_cells(start_row=2, start_column = 14 + merge_cells_num + len(count_loss) , end_row=3, end_column = 14 + merge_cells_num + len(count_loss))
            sheet.merge_cells(start_row=2, start_column = 15 + merge_cells_num + len(count_loss) , end_row=3, end_column = 15 + merge_cells_num + len(count_loss))

            # merge_cells headers loos_type
            sheet.merge_cells(start_row = 2, start_column = 4 + merge_cells_num , end_row = 2, end_column = 5 + merge_cells_num)
            sheet.merge_cells(start_row = 2, start_column = 7 + merge_cells_num , end_row = 2, end_column = 8 + merge_cells_num)
            sheet.merge_cells(start_row = 2, start_column = 10 + merge_cells_num , end_row = 2, end_column = 9 + merge_cells_num + len(count_loss))
            
            merge_cells_num += len(count_loss) + 14

        sheet.cell(row=1, column = 1, value = 'วัน/เดือน/ปี')
        sheet.merge_cells(start_row=1, start_column = 1, end_row=3, end_column=1)
        sheet.append(headers3)

        # Fetch distinct 'created' dates for the current mill
        created_dates = Production.objects.filter(my_q, mill=mill).values_list('created', flat=True).order_by('created').distinct()

        for created_date in created_dates:
            row = [created_date]
            row_sum = ['']
            row_persent_loss = ['']
            row_persent_accumulated_produc = ['']
            sum_capacity_per_hour = Decimal('0.0')
            
            date_from_accumulated = startDateInMonth(created_date)

            for line_type in BaseLineType.objects.filter(id__in=line_types):
                production = Production.objects.filter(mill = mill, line_type = line_type, created = created_date).first()
                accumulated_goal = Production.objects.filter(mill = mill, line_type = line_type, created__range=(date_from_accumulated, created_date)).aggregate(s=Sum("goal"))["s"]

                data_sum_produc = Weight.objects.filter(mill_name=mill ,date = created_date, bws__weight_type = 2, stone_type_name__icontains = 'เข้าโม่').aggregate(s=Sum("weight_total"))["s"]
                accumulated_produc = Weight.objects.filter(mill_name=mill ,date__range=(date_from_accumulated, created_date) , bws__weight_type = 2, stone_type_name__icontains = 'เข้าโม่').aggregate(s=Sum("weight_total"))["s"]

                sum_by_mill = Production.objects.filter(my_q, mill=mill, line_type = line_type).distinct().aggregate(Sum('plan_time'),Sum('run_time'),Sum('total_loss_time'))
                cal_by_mill = Production.objects.filter(my_q, mill=mill, line_type = line_type).distinct().annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']

                capacity_per_hour = calculatCapacityPerHour(request, data_sum_produc, accumulated_produc)
                if production:
                    row.extend([production.goal, accumulated_goal , formatHourMinute(production.plan_start_time), formatHourMinute(production.plan_end_time), formatHourMinute(production.plan_time), formatHourMinute(production.run_start_time) if production.run_start_time else production.mile_run_start_time  , formatHourMinute(production.run_end_time) if production.run_end_time else production.mile_run_end_time, formatHourMinute(production.run_time)])
                    row.extend([formatHourMinute(pd_loos_item.loss_time) for pd_loos_item in ProductionLossItem.objects.filter(production = production).order_by('loss_type__id')])
                    row.extend([formatHourMinute(production.total_loss_time), formatHourMinute(calculatorDiffTime(request, production.total_loss_time, production.run_time)), data_sum_produc, accumulated_produc, capacity_per_hour, production.note,])
                    sum_capacity_per_hour += capacity_per_hour
                else:
                    row.extend(['' for i in range(len(count_loss) + 14)])

                row_sum.extend([len(created_dates), '' , '', 'ชั่วโมงทำงานรวม', formatHourMinute(sum_by_mill['plan_time__sum']), '', '', formatHourMinute(sum_by_mill['run_time__sum'])])
                row_sum.extend([formatHourMinute(pd_loos_item['sum_loss_time']) for pd_loos_item in ProductionLossItem.objects.filter(production__mill=mill, production__line_type = line_type).order_by('loss_type__id').values('loss_type__id').annotate(sum_loss_time=Coalesce(Sum('loss_time'), None))])

                row_sum.extend([formatHourMinute(sum_by_mill['total_loss_time__sum']), formatHourMinute(cal_by_mill), 'diff จากเป้า' , calculatorDiff(request, accumulated_goal , accumulated_produc) , sum_capacity_per_hour/len(created_dates),''])

                loss_items = ProductionLossItem.objects.filter(
                    production__mill=mill,
                    production__line_type=line_type
                ).order_by('loss_type__id').values('loss_type__id').annotate(
                    sum_loss_time=Coalesce(Sum('loss_time'), None)
                )

                row_persent_accumulated_produc.extend(['', '' , '', '', '', '', '', ''])
                row_persent_accumulated_produc.extend(['' for i in range(len(count_loss))])
                row_persent_accumulated_produc.extend(['', '', '' , str(round(calculatorDiff(request, accumulated_goal , accumulated_produc) / accumulated_goal, 2)) + "%" if accumulated_goal and accumulated_produc else None , '',''])

                row_persent_loss.extend(['', '' , '', '', '', '', '% ชม.สูญเสีย ต่อ ชม.ทำงานจริง', ''])
                row_persent_loss.extend([str(round(pd_loos_item['sum_loss_time'] / sum_by_mill['total_loss_time__sum'] * 100, 2)) + "%" if pd_loos_item['sum_loss_time'] else None for pd_loos_item in loss_items])
                row_persent_loss.extend(['100%', '', '' , '' , '',''])

            sheet.append(row)

        if len(created_dates) > 0:
            sheet.append(row_sum)
            sheet.append(row_persent_accumulated_produc)
            sheet.append(row_persent_loss)
            sheet.cell(row = len(created_dates) + 4, column = 1, value = f'จำนวนวันทำงาน' )

        # Set column width and border for all columns
        for column in sheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)  # Get the letter of the current column
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass

            adjusted_width = (max_length + 2) * 1.2  # Adjust the width based on content length
            sheet.column_dimensions[column_letter].width = adjusted_width
            
            # Set border for each cell in the column
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            for cell in column:
                cell.alignment = Alignment(horizontal='center')

                # 2 row สุดท้าย ไม่ใส่ border และ set ตัวหนังสือสีแดง
                if cell.row > sheet.max_row - 3:
                    cell.font = Font(color="FF0000")
                else:
                    cell.border = border
        
        column_index = 2
        for line_index, line in enumerate(line_types):
            # Set the background color for the current line_type
            fill = PatternFill(start_color=line_type_colors[line_index % len(line_type_colors)], fill_type="solid")
            sheet.cell(row=1, column=column_index).fill = fill
            column_index += len(count_loss) + 14


        for row in sheet.iter_rows(min_row=1, max_row=3):
            # Set the background color for each cell in the column
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(horizontal='center')
                line_index = (cell.column - 2) // (len(count_loss) + 14)
                fill_color = line_type_colors[line_index % len(line_type_colors)]
                fill = PatternFill(start_color=fill_color, fill_type="solid")
                cell.fill = fill

    workbook.remove(workbook['Sheet'])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="production_data.xlsx"'

    workbook.save(response)
    return response

def exportExcelProductionAndLoss(request):
    start_created = request.GET.get('start_created') or None
    end_created = request.GET.get('end_created') or None
    mill = request.GET.get('mill') or None

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    
    response = excelProductionAndLoss(request, my_q)
    return response

def exportExcelProductionAndLossDashboard(request):
    #ดึงรายงานของเดือนนั้นๆ
    end_created = datetime.today().strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    
    response = excelProductionAndLoss(request, my_q)
    return response

def viewStoneEstimate(request):
    data = StoneEstimate.objects.all().order_by('-created', 'mill')

    #กรองข้อมูล
    myFilter = StoneEstimateFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    stone_estimate = p.get_page(page)

    context = {'stone_estimate_page':'active', 'stone_estimate': stone_estimate,'filter':myFilter, }
    return render(request, "stoneEstimate/viewStoneEstimate.html",context)

def createStoneEstimate(request):
    base_stone_type = BaseStoneType.objects.filter(is_stone_estimate = True)
    StoneEstimateItemFormSet = modelformset_factory(StoneEstimateItem, fields=('stone_type', 'percent'), extra=len(base_stone_type), widgets={})
    if request.method == 'POST':
        se_form = StoneEstimateForm(request.POST)
        formset = StoneEstimateItemFormSet(request.POST)
        if se_form.is_valid() and formset.is_valid():
            se = se_form.save()

            formset_instances = formset.save(commit=False)
            for instance in formset_instances:
                instance.se = se
                instance.save()
            return redirect('viewStoneEstimate')
    else:
        se_form = StoneEstimateForm()
        formset = StoneEstimateItemFormSet(queryset=StoneEstimateItem.objects.none())

    context = {'stone_estimate_page':'active', 'se_form': se_form, 'formset' : formset, 'base_stone_type': base_stone_type,}
    return render(request, "stoneEstimate/createStoneEstimate.html",context)

def editStoneEstimate(request, se_id):
    se_data = StoneEstimate.objects.get(id = se_id)

    if request.method == "POST":
        formset = StoneEstimateItemInlineFormset(request.POST, request.FILES, instance=se_data)
        se_form = StoneEstimateForm(request.POST, request.FILES, instance=se_data)
        if se_form.is_valid() and formset.is_valid():
            # save StoneEstimate
            se = se_form.save()

            # save StoneEstimateItem
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()

            return redirect('viewStoneEstimate')
    else:
        formset = StoneEstimateItemInlineFormset(instance=se_data)
        se_form = StoneEstimateForm(instance=se_data)

    context = {'stone_estimate_page':'active', 'se_form': se_form, 'formset' : formset,'se': se_data,}
    return render(request, "stoneEstimate/editStoneEstimate.html",context)

def removeStoneEstimate(request, se_id):
    se = StoneEstimate.objects.get(id = se_id)
    #ลบ StoneEstimateItem ใน StoneEstimate ด้วย
    items = StoneEstimateItem.objects.filter(se = se)
    items.delete()
    #ลบ StoneEstimate ทีหลัง
    se.delete()
    return redirect('viewStoneEstimate')

def searchStoneEstimate(request):
    if 'mill_id' in request.GET and 'created' in request.GET and 'se_id' in request.GET:
        mill_id = request.GET.get('mill_id')
        created =  request.GET.get('created')
        se_id =  request.GET.get('se_id')

        #if se_id == '' create mode , else edit mode
        if se_id == '':
            have_estimate = StoneEstimate.objects.filter(created = created, mill__mill_id= mill_id).exists()
        else:
            have_estimate = StoneEstimate.objects.filter(~Q(id = se_id), created = created, mill__mill_id = mill_id).exists()
        #ดึงเปอร์เซ็นคำนวนหินเปอร์ที่คีย์ไปล่าสุด
        last_se = StoneEstimate.objects.filter(mill__mill_id = mill_id).order_by('-created').first()
        last_se_item = StoneEstimateItem.objects.filter(se = last_se).values('stone_type', 'percent')
        
    data = {
        'have_estimate' :have_estimate,
        'last_se_item': list(last_se_item),
    }
    
    return JsonResponse(data)

def calculateEstimate(percent, sum_all):
    result = None
    if percent and sum_all:
        result = Decimal(sum_all) * Decimal(percent)/100
        result = f"{result:.2f}"
    return result

def exportExcelStoneEstimateAndProduction(request):
    date_style = NamedStyle(name='custom_datetime', number_format='DD/MM/YYYY')

    end_created = datetime.today().strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)

    se_mills = StoneEstimate.objects.filter(my_q).values_list('mill', flat=True).distinct()
    mills = BaseMill.objects.filter(mill_id__in = se_mills)

    base_stone_type = BaseStoneType.objects.all().values_list('base_stone_type_name', flat=True)

    #list_customer_name = ['สมัย','วีระวุฒิ','NCK']
    list_customer_name = BaseCustomer.objects.filter(is_stone_estimate = True).values_list('customer_name', flat=True)

    workbook = openpyxl.Workbook()
    for mill in mills:
        sheet = workbook.create_sheet(title=mill.mill_name)

        list_time = BaseTimeEstimate.objects.filter(mill = mill).values('time_from', 'time_to', 'time_name')
        #ดึงชนิดหินที่มีคำว่าเข้าโม่
        weight_stone_types = Weight.objects.filter(Q(stone_type_name__icontains = 'เข้าโม่') | Q(stone_type_name = 'กองสต็อก'), bws__weight_type = 2, date__range=('2023-02-01', '2023-02-28'), mill_name = mill.mill_name).order_by('stone_type_name').values_list('stone_type_name', flat=True).distinct()
        #weight_stone_type = BaseStoneType.objects.filter(base_stone_type_name__in=weight_stone_types)

        column_index = 2
        sheet.cell(row=1, column = column_index, value = "พนักงาน")
        sheet.merge_cells(start_row=1, start_column = column_index, end_row=2, end_column= (column_index + 2) -1 )
        sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')

        column_index += 2
        sheet.cell(row=1, column = column_index, value = "ชม.ทำงาน")
        sheet.merge_cells(start_row=1, start_column = column_index, end_row=2, end_column= column_index)
        sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')

        column_index += 1
        sheet.cell(row=1, column = column_index, value = "หินเขา")
        sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')

        column_index += 1
        for wst in weight_stone_types:
            sheet.cell(row=1, column = column_index, value = wst)
            sheet.merge_cells(start_row=1, start_column = column_index, end_row=1, end_column= (column_index + 2) -1 )
            sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')
            column_index += 2

        sheet.cell(row=1, column = column_index, value = "หินเข้าโม่ทั้งหมด")
        sheet.merge_cells(start_row=1, start_column = column_index, end_row=1, end_column= (column_index + 2) -1 )
        sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')

        column_index += 2
        sheet.cell(row=1, column = column_index, value = "สต็อกคงเหลือ")

        column_index += 1
        sheet.cell(row=1, column = column_index, value = 'ประเภทหินตัน')
        sheet.merge_cells(start_row=1, start_column = column_index, end_row=1, end_column= (column_index + len(base_stone_type)) -1 )
        sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')
        column_index += len(base_stone_type)

        sheet.cell(row=1, column = column_index, value = 'หินเข้าโม่รวม(ตัน)')
        sheet.merge_cells(start_row=1, start_column = column_index, end_row=2, end_column= column_index)
        sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')


        headers2 = ['Date','พนักงาน', 'กะ', 'ชม.ทำงาน', 'ที่ผลิตได้',]
        for i in range(len(weight_stone_types) + 1):
            headers2.extend(['เที่ยว','ตัน',])

        headers2.extend(['AAA'])
        headers2.extend([i for i in base_stone_type])
        headers2.extend(['หินเข้าโม่รวม(ตัน)', 'ผลิตตัน/ชม.', 'หมายเหตุ'])

        sheet.cell(row=1, column = 1, value = 'วัน/เดือน/ปี')
        #merge_cells วัน/เดือน/ปี
        sheet.merge_cells(start_row=1, start_column = 1, end_row=2, end_column=1)
        sheet.append(headers2)

        # Fetch distinct 'created' dates for the current mill
        created_dates = StoneEstimate.objects.filter(my_q, mill=mill).values_list('created', flat=True).order_by('created').distinct()

        row_index = 3
        for created_date in created_dates:
            len_row_index = 0
            total_working_time = None
            production_note = None
            for i in range(len(list_customer_name)):
                for j, time in enumerate(list_time):
                    len_row_index +=1

                    #ชั่วโมงทำงาน
                    total_working_time = Production.objects.filter(created = created_date, mill=mill).distinct().annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']
                    #หมายเหตุ
                    production_note = Production.objects.filter(mill = mill, created = created_date).values_list('note', flat=True).first()
                    #หินเขา
                    mountain1  = Weight.objects.filter(Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), Q(stone_type_name = 'เข้าโม่') | Q(stone_type_name = 'กองสต็อก'), bws__weight_type = 2, mill_name = mill.mill_name, date = created_date, customer_name = list_customer_name[i]).aggregate(s_weight = Sum("weight_total"))
                    #หินเข้าโม่ทั้งหมด
                    crush1 = Weight.objects.filter(Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), Q(stone_type_name__contains = 'เข้าโม่'), bws__weight_type = 2, mill_name = mill.mill_name, date = created_date, customer_name = list_customer_name[i]).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))

                    #สร้างแถว 1
                    row1 = [created_date, list_customer_name[i], str(time['time_name']), formatHourMinute(total_working_time), mountain1['s_weight']]

                    for stone_type_name in weight_stone_types:

                        weight_time1 = Weight.objects.filter(Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), bws__weight_type = 2, stone_type_name = stone_type_name, mill_name = mill.mill_name, date = created_date, customer_name = list_customer_name[i]).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))
                        if weight_time1:
                            row1.extend([weight_time1['c_weight'], weight_time1['s_weight']])
                        else:
                            row1.extend(['' for i in range(3)])

                    row1.extend([crush1['c_weight'], crush1['s_weight']])
                    row1.extend(['1'])
                    row1.extend([calculateEstimate(se_item, crush1['s_weight']) for se_item in StoneEstimateItem.objects.filter(se__created = created_date, se__mill = mill).values_list('percent', flat=True)])
                    sheet.append(row1)

                #merge_cells พนักงาน
                sheet.merge_cells(start_row = row_index + len_row_index -2 , start_column = 2, end_row = row_index + len_row_index -1, end_column=2)

            sheet.cell(row = row_index + len_row_index, column=1, value='รวมทั้งหมด')
            sum_by_col = Decimal('0.00')
            for col in range(5, column_index):
                for row in range(row_index, len_row_index + row_index):
                    sum_by_col = sum_by_col + Decimal( sheet.cell(row=row, column=col).value or '0.00' )
                sheet.cell(row=row_index + len_row_index, column=col, value=sum_by_col).number_format = '#,##0.00'
                sheet.cell(row=row_index + len_row_index, column=col).font = Font(bold=True)
                sum_by_col = Decimal('0.00')
            row_index +=  len_row_index + 1

            sum_in_row = Decimal('0.00')
            for row in range(3, row_index):
                for col in range(column_index - len(base_stone_type), column_index):
                    sum_in_row = sum_in_row + Decimal( sheet.cell(row=row, column=col).value or '0.00' )
                sheet.cell(row=row, column=column_index, value=sum_in_row).number_format = '#,##0.00'
                sheet.cell(row=row, column=column_index).font = Font(color="FF0000", bold=True)
                sum_in_row = Decimal('0.00')

            #หินเข้าโม่รวม(ตัน) ของวันนั้นๆ
            sum_crush = sheet.cell(row=row_index-1, column=column_index).value
            if total_working_time:
                (h, m, s) = str(total_working_time).split(':')
                decimal_time = int(h) + (int(m) / 100)
                decimal_time = Decimal(decimal_time)
                #ผลิตตัน/ชม
                capacity_per_hour = sum_crush/decimal_time
                sheet.cell(row = (row_index - 1 ) - len_row_index, column=column_index+1, value = f"{capacity_per_hour:.2f}")
                sheet.merge_cells(start_row = (row_index - 1 ) - len_row_index, start_column = column_index+1, end_row = (row_index - 1 ), end_column=column_index+1)
            #หมายเหตุ
            sheet.cell(row = (row_index - 1 ) - len_row_index, column=column_index+2, value = production_note)
            sheet.merge_cells(start_row = (row_index - 1 ) - len_row_index, start_column = column_index+2, end_row = (row_index - 1 ), end_column=column_index+2)

            #merge_cells วันที่, ชม.ทำงาน
            sheet.merge_cells(start_row = (row_index - 1 ) - len_row_index, start_column = 1, end_row = (row_index - 1 ), end_column=1)
            sheet.merge_cells(start_row = (row_index - 1 ) - len_row_index, start_column = 4, end_row = (row_index - 1 ), end_column=4)

            # Set column width and border for all columns
            for column in sheet.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)  # Get the letter of the current column

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value) + 2
                    except:
                        pass

                    if cell.column == 5:
                        cell.fill = PatternFill(start_color='93eef5', end_color='93eef5', fill_type='solid')

                    column_crush = len(weight_stone_types) * 2 + 6
                    if cell.column == column_crush or cell.column == column_crush + 1:
                        cell.fill = PatternFill(start_color='FFD548', end_color='FFD548', fill_type='solid')

                    if cell.column == column_crush + 2:
                        cell.fill = PatternFill(start_color='F7BF94', end_color='F7BF94', fill_type='solid')

                adjusted_width = (max_length + 2) * 1.2  # Adjust the width based on content length
                sheet.column_dimensions[column_letter].width = adjusted_width

                # Set border for each cell in the column
                border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                for cell in column:
                    if cell.row < 3:
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                    else:
                        cell.alignment = Alignment(horizontal='right', vertical='center')
                    cell.border = border
        
    workbook.remove(workbook['Sheet'])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="stone_estimate.xlsx"'

    workbook.save(response)
    return response

################### BaesMill ####################
def settingBaseMill(request):
    data = BaseMill.objects.all().order_by('-mill_id')

    #กรองข้อมูล
    myFilter = BaseMillFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_mill = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_mill_page': 'active', 'base_mill': base_mill,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseMill.html",context)


def createBaseMill(request):
    form = BaseMillForm(request.POST or None)
    if form.is_valid():
        form = BaseMillForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseMill')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_mill_page': 'active',
        'table_name' : 'ต้นทาง',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseMill(request, id):
    data = BaseMill.objects.get(mill_id = id)
    form = BaseMillForm(instance=data)
    if request.method == 'POST':
        form = BaseMillForm(request.POST, instance=data)
        if form.is_valid():
            try:
                mill_form = form.save()

                # update weight ด้วย
                weights = Weight.objects.filter(mill_id = mill_form.pk) #iiiiiiiiiiiii
                weights.update(mill_name = mill_form.mill_name)
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseMill')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_mill_page': 'active',
        'table_name' : 'ต้นทาง',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaseJobType ####################
def settingBaseJobType(request):
    data = BaseJobType.objects.all().order_by('base_job_type_id')

    #กรองข้อมูล
    myFilter = BaseJobTypeFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_job_type = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_job_type_page': 'active', 'base_job_type': base_job_type,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseJobType.html",context)


def createBaseJobType(request):
    form = BaseJobTypeForm(request.POST or None)
    if form.is_valid():
        form = BaseJobTypeForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseJobType')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_job_type_page': 'active',
        'table_name' : 'ประเภทงานของลูกค้า',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseJobType(request, id):
    data = BaseJobType.objects.get(base_job_type_id = id)
    form = BaseJobTypeForm(instance=data)
    if request.method == 'POST':
        form = BaseJobTypeForm(request.POST, instance=data)
        if form.is_valid():
            try:
                job_type_form = form.save()
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseJobType')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_job_type_page': 'active',
        'table_name' : 'ประเภทงานของลูกค้า',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaesStoneType ####################
def settingBaseStoneType(request):
    data = BaseStoneType.objects.all().order_by('-base_stone_type_id')

    #กรองข้อมูล
    myFilter = BaseStoneTypeFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_stone_type = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_stone_type_page': 'active', 'base_stone_type': base_stone_type,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseStoneType.html",context)

def createBaseStoneType(request):
    form = BaseStoneTypeForm(request.POST or None)
    if form.is_valid():
        form = BaseStoneTypeForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseStoneType')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_stone_type_page': 'active',
        'table_name' : 'ชนิดหิน',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseStoneType(request, id):
    data = BaseStoneType.objects.get(base_stone_type_id = id)
    
    form = BaseStoneTypeForm(instance=data)
    if request.method == 'POST':
        form = BaseStoneTypeForm(request.POST, instance=data)
        if form.is_valid():
            try:
                stone_type_form = form.save()

                # update weight ด้วย
                weights = Weight.objects.filter(stone_type_id = stone_type_form.pk)# iiiiiiiiiii
                weights.update(stone_type_name = stone_type_form.base_stone_type_name)
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseStoneType')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_stone_type_page': 'active',
        'table_name' : 'ชนิดหิน',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaesScoop ####################
def settingBaseScoop(request):
    data = BaseScoop.objects.all().order_by('-scoop_id')

    #กรองข้อมูล
    myFilter = BaseScoopFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_scoop = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_scoop_page': 'active', 'base_scoop': base_scoop,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseScoop.html",context)

def createBaseScoop(request):
    form = BaseScoopForm(request.POST or None)
    if form.is_valid():
        form = BaseScoopForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseScoop')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_scoop_page': 'active',
        'table_name' : 'ผู้ตัก',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseScoop(request, id):
    data = BaseScoop.objects.get(scoop_id = id)
    
    form = BaseScoopForm(instance=data)
    if request.method == 'POST':
        form = BaseScoopForm(request.POST, instance=data)
        if form.is_valid():
            try:
                scoop_form = form.save()

                # update weight ด้วย
                weights = Weight.objects.filter(scoop_id = scoop_form.pk) # iiiiiiiiii
                weights.update(scoop_name = scoop_form.scoop_name)
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseScoop')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_scoop_page': 'active',
        'table_name' : 'ผู้ตัก',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaseCarTeam ####################
def settingBaseCarTeam(request):
    data = BaseCarTeam.objects.all().order_by('-car_team_id')

    #กรองข้อมูล
    myFilter = BaseCarTeamFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_car_team = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_car_team_page': 'active', 'base_car_team': base_car_team,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseCarTeam.html",context)

def createBaseCarTeam(request):
    form = BaseCarTeamForm(request.POST or None)
    if form.is_valid():
        form = BaseCarTeamForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseCarTeam')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_team_page': 'active',
        'table_name' : 'ทีม',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseCarTeam(request, id):
    data = BaseCarTeam.objects.get(car_team_id = id)
    
    form = BaseCarTeamForm(instance=data)
    if request.method == 'POST':
        form = BaseCarTeamForm(request.POST, instance=data)
        if form.is_valid():
            try:
                car_team_form = form.save()

                # update weight ด้วย
                weights = Weight.objects.filter(car_team_id = car_team_form.pk)# iiiiiiiiiii
                weights.update(car_team_name = car_team_form.car_team_name)
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseCarTeam')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_team_page': 'active',
        'table_name' : 'ทีม',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaseCar ####################
def settingBaseCar(request):
    data = BaseCar.objects.all().order_by('-car_id')

    #กรองข้อมูล
    myFilter = BaseCarFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_car = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_car_page': 'active', 'base_car': base_car,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseCar.html",context)

def createBaseCar(request):
    form = BaseCarForm(request.POST or None)
    if form.is_valid():
        form = BaseCarForm(request.POST or None, request.FILES)
        form.save()
        return redirect('settingBaseCar')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_page': 'active',
        'table_name' : 'รถร่วม',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseCar(request, id):
    data = BaseCar.objects.get(car_id = id)
    
    form = BaseCarForm(instance=data)
    if request.method == 'POST':
        form = BaseCarForm(request.POST, instance=data)
        if form.is_valid():
            car_form = form.save()

            '''
            # update weight ด้วย
            weights = Weight.objects.filter(scoop_id = scoop_form.pk)
            weights.update(scoop_name = scoop_form.scoop_name)         
            '''
            return redirect('settingBaseCar')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_page': 'active',
        'table_name' : 'รถร่วม',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaesSite ####################
def settingBaseSite(request):
    data = BaseSite.objects.all().order_by('-base_site_id')

    #กรองข้อมูล
    myFilter = BaseSiteFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_site = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_site_page': 'active', 'base_site': base_site,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/BaseSite/baseSite.html",context)

def createBaseSite(request):
    form = BaseSiteForm(request.POST or None)
    if form.is_valid():
        form = BaseSiteForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseSite')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_site_page': 'active',
        'table_name' : 'ปลายทาง',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/BaseSite/formBaseSite.html", context)

def editBaseSite(request, id):
    data = BaseSite.objects.get(base_site_id = id)
    
    form = BaseSiteForm(instance=data)
    if request.method == 'POST':
        form = BaseSiteForm(request.POST, instance=data)
        if form.is_valid():
            try:
                site_form = form.save()

                # update weight ด้วย
                weights = Weight.objects.filter(site_id = site_form.pk) # iiiiiiiiiiiiiii
                weights.update(site_name = site_form.base_site_name)   
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseSite')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_site_page': 'active',
        'table_name' : 'ปลายทาง',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/BaseSite/formBaseSite.html", context)

################### BaesCustomer ####################
def settingBaseCustomer(request):
    data = BaseCustomer.objects.filter(is_disable = False).order_by('-weight_type_id','-customer_id')

    #กรองข้อมูล
    myFilter = BaseCustomerFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_customer = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_customer_page': 'active', 'base_customer': base_customer,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/BaseCustomer/baseCustomer.html",context)

def createBaseCustomer(request):
    form = BaseCustomerForm(request.POST or None)
    if form.is_valid():
        form = BaseCustomerForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseCustomer')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_customer_page': 'active',
        'table_name' : 'ลูกค้า',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/BaseCustomer/formBaseCustomer.html", context)

def editBaseCustomer(request, id):
    data = BaseCustomer.objects.get(customer_id = id)
    
    form = BaseCustomerForm(instance=data)
    if request.method == 'POST':
        form = BaseCustomerForm(request.POST, instance=data)
        if form.is_valid():
            try:
                customer_form = form.save()

                # update weight ด้วย iiiiiiiiiiiiiii
                weights = Weight.objects.filter(customer_id = customer_form.pk)
                weights.update(customer_name = customer_form.customer_name)
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseCustomer')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_customer_page': 'active',
        'table_name' : 'ลูกค้า',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/BaseCustomer/formBaseCustomer.html", context)

################### BaseDriver ####################
def settingBaseDriver(request):
    data = BaseDriver.objects.all().order_by('-driver_id')

    #กรองข้อมูล
    myFilter = BaseDriverFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_driver = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_driver_page': 'active', 'base_driver': base_driver,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseDriver.html",context)

def createBaseDriver(request):
    form = BaseDriverForm(request.POST or None)
    if form.is_valid():
        form = BaseDriverForm(request.POST or None, request.FILES)
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseDriver')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_driver_page': 'active',
        'table_name' : 'ผู้ขับ',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseDriver(request, id):
    data = BaseDriver.objects.get(driver_id = id)
    
    form = BaseDriverForm(instance=data)
    if request.method == 'POST':
        form = BaseDriverForm(request.POST, instance=data)
        if form.is_valid():
            try:
                driver_form = form.save()

                # update weight ด้วย
                weights = Weight.objects.filter(driver_id = driver_form.pk)
                weights.update(driver_name = driver_form.driver_name)
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseDriver')
    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_driver_page': 'active',
        'table_name' : 'ผู้ขับ',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaseCarRegistration ####################
def settingBaseCarRegistration(request):
    data = BaseCarRegistration.objects.all().order_by('-car_registration_id')

    #กรองข้อมูล
    myFilter = BaseCarRegistrationFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_car_registration = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_car_registration_page': 'active', 'base_car_registration': base_car_registration,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/baseCarRegistration.html",context)

def createBaseCarRegistration(request):
    form = BaseCarRegistrationForm(request.POST or None)
    if form.is_valid():
        form = BaseCarRegistrationForm(request.POST or None, request.FILES)
        form.save()
        return redirect('settingBaseCarRegistration')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_registration_page': 'active',
        'table_name' : 'ทะเบียนรถ',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/formBase.html", context)

def editBaseCarRegistration(request, id):
    data = BaseCarRegistration.objects.get(car_registration_id = id)
    
    form = BaseCarRegistrationForm(instance=data)
    if request.method == 'POST':
        form = BaseCarRegistrationForm(request.POST, instance=data)
        if form.is_valid():
            car_registration_form = form.save()

            # update weight ด้วย
            weights = Weight.objects.filter(car_registration_id = car_registration_form.pk)
            weights.update(car_registration_name = car_registration_form.car_registration_name)

            return redirect('settingBaseCarRegistration')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_registration_page': 'active',
        'table_name' : 'ทะเบียนรถ',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/formBase.html", context)

################### BaseCustomerSite ####################
def settingBaseCustomerSite(request):
    data = BaseCustomerSite.objects.all().order_by('id')

    #กรองข้อมูล
    myFilter = BaseCustomerSiteFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_customer_site = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_customer_site_page': 'active', 'base_customer_site': base_customer_site,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user)}
    return render(request, "manage/BaseCustomerSite/baseCustomerSite.html",context)

def createBaseCustomerSite(request):
    if request.method == 'POST':
        form = BaseCustomerSiteForm(request.POST or None, request.FILES)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error(None, 'This combination of field1 and field2 is not unique.')
            else:
                return redirect('settingBaseCustomerSite')
    else:
        form = BaseCustomerSiteForm()

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_customer_site_page': 'active',
        'table_name' : 'ลูกค้าและหน้างาน',
        'text_mode' : 'เพิ่ม',
    }

    return render(request, "manage/BaseCustomerSite/formBaseCustomerSite.html", context)

def editBaseCustomerSite(request, id):
    data = BaseCustomerSite.objects.get(id = id)
    
    form = BaseCustomerSiteForm(instance=data)
    if request.method == 'POST':
        form = BaseCustomerSiteForm(request.POST, instance=data)
        if form.is_valid():
            try:
                customer_site_form = form.save()
            except IntegrityError:
                form.add_error(None, 'This combination of field1 and field2 is not unique.')
            else:
                return redirect('settingBaseCustomerSite')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_customer_site_page': 'active',
        'table_name' : 'ลูกค้าและหน้างาน',
        'text_mode' : 'เปลี่ยน',
    }

    return render(request, "manage/BaseCustomerSite/formBaseCustomerSite.html", context)

#################################
############# API ###############
#################################

############# Login API ###############
class LoginApiView(APIView):
    permission_classes = []

    def post(self, request: Request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is not None:
            tokens = create_jwt_pair_for_user(user)

            response = {"message": "Login Successfull", "tokens": tokens}
            return Response(data=response, status=status.HTTP_200_OK)

        else:
            return Response(data={"message": "Invalid email or password"})

    def get(self, request: Request):
        content = {"user": str(request.user), "auth": str(request.auth)}

        return Response(data=content, status=status.HTTP_200_OK)

############# SignUp API ###############   
class SignUpApiView(generics.GenericAPIView):
    serializer_class = SignUpSerializer
    permission_classes = []

    def post(self, request: Request):
        data = request.data

        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()

            response = {"message": "User Created Successfully", "data": serializer.data}

            return Response(data=response, status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############# Weight API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiWeightOverview(request):
    api_urls = {
        'List':'/weight/api/list/',
        'Detail View':'/weight/api/detail/<str:pk>/',
        'Detail By Date':'/weight/api/detail/date/<str:str_date>/',
        'Create':'/weight/api/create/',
        'Update':'/weight/api/update/<str:pk>/',
        'VStamp':'/weight/api/vStamp/<str:dt>/<str:str_lc>/',
        'Detail By Date Between and Weight Type':'/weight/api/between/<str:start_date>/<str:end_date>/<str:weight_type/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightList(request):
    queryset = Weight.objects.all()
    serializer = WeightSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightDetail(request, pk):
    queryset = Weight.objects.get(weight_id = pk)
    serializer = WeightSerializer(queryset, many = False)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightDetailByDate(request, str_date , str_lc):
    latest_weights = WeightHistory.objects.filter(date = str_date, bws__id = str_lc).values('weight_id').distinct()
    queryset = Weight.objects.filter(weight_id__in = latest_weights)

    serializer = WeightSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightVStamp(request, dt, str_lc):
    latest_weights = WeightHistory.objects.filter(v_stamp__gte = dt, bws__id = str_lc).order_by('v_stamp').values('weight_id').distinct()
    queryset = Weight.objects.filter(weight_id__in = latest_weights)
    
    serializer = WeightSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightVStampAll(request, dt):
    latest_weights = WeightHistory.objects.filter(v_stamp__gte = dt).order_by('v_stamp').values('weight_id').distinct()
    queryset = Weight.objects.filter(weight_id__in = latest_weights)
    
    serializer = WeightSerializer(queryset, many = True)
    return Response(serializer.data)

# For Insert Report weight 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightDetailBetween(request, start_date, end_date , weight_type):
    queryset = Weight.objects.filter(date__range=[start_date, end_date], bws__weight_type__id = weight_type)

    serializer = WeightSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def weightCreate(request):
    serializer = WeightSerializer(data = request.data)
    
    if serializer.is_valid():
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response(serializer.data, status=status.HTTP_409_CONFLICT)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def weightUpdate(request, pk):
    queryset = Weight.objects.get(weight_id = pk)
    serializer = WeightSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

############# BaseScoop API ###############
class BaseScoopView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = BaseScoop.objects.all()
    serializer_class = BaseScoopSerializer

class BaseScoopViewById(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = BaseScoop.objects.all()
    def get_queryset(self):
        queryset = BaseScoop.objects.filter(scoop_id=self.kwargs["pk"])
        return queryset
    serializer_class = BaseScoopSerializer

class CreateBaseScoop(APIView):
    permission_classes = [IsAuthenticated]

    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'manage/formBase.html'

    serializer_class = BaseScoopSerializer

    def post(self, request):
        scoop_id = request.data.get("scoop_id")
        scoop_name = request.data.get("scoop_name")

        data = {'scoop_id': scoop_id, 'scoop_name': scoop_name}

        serializer = BaseScoopSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseScoopDetail(request, pk):
    queryset = BaseScoop.objects.get(scoop_id=pk)
    serializer = BaseScoopSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseScoopVStamp(request, dt):
    queryset = BaseScoop.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseScoopSerializer(queryset, many = True)
    return Response(serializer.data)
        
############# BaseMill API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseMillOverview(request):
    api_urls = {
        'List':'/baseMill/api/list/',
        'Detail View':'/baseMill/api/detail/<str:pk>/',
        'Create':'/baseMill/api/create/',
        'Update':'/baseMill/api/update/<str:pk>/',
        'Delete':'/baseMill/api/delete/<str:pk>/',
        'VStamp':'/baseMill/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseMillList(request):
    queryset = BaseMill.objects.all()
    serializer = BaseMillSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseMillDetail(request, pk):
    queryset = BaseMill.objects.get(mill_id=pk)
    serializer = BaseMillSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseMillCreate(request):
    serializer = BaseMillSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseMillUpdate(request, pk):
    queryset = BaseMill.objects.get(mill_id=pk)
    serializer = BaseMillSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseMillDelete(request, pk):
    queryset = BaseMill.objects.get(mill_id=pk)
    queryset.delete()

    return Response("Item successfully delete!")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseMillVStamp(request, dt):
    queryset = BaseMill.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseMillSerializer(queryset, many = True)
    return Response(serializer.data)

############# base customer API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseCustomerOverview(request):
    api_urls = {
        'List':'/baseCustomer/api/list/',
        'Detail View':'/baseCustomer/api/detail/<str:pk>/',
        'Create':'/baseCustomer/api/create/',
        'Update':'/baseCustomer/api/update/<str:pk>/',
        'VStamp':'/baseCustomer/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCustomerList(request):
    queryset = BaseCustomer.objects.all()
    serializer = BaseCustomerSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCustomerDetail(request, pk):
    queryset = BaseCustomer.objects.get(customer_id = pk)
    serializer = BaseCustomerSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseCustomerCreate(request):
    serializer = BaseCustomerSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseCustomerUpdate(request, pk):
    try:
        base_customer = BaseCustomer.objects.get(customer_id=pk)
        weights = Weight.objects.filter(customer_id = pk) #iiiiiiiiii

        # Update BaseCustomer
        base_customer_serializer = BaseCustomerSerializer(instance=base_customer, data=request.data)
        if base_customer_serializer.is_valid():
            base_customer_serializer.save()

            customer_name = request.data.get("customer_name")
            # 1 Update Weight
            weights.update(customer_name = customer_name)
            
            # 2 Update Weight ไม่ต้องแล้ว
            '''
            data_weight = {'customer_id': pk, 'customer_name': customer_name}
            for weight in weights:
                weight_serializer = WeightSerializer(instance=weight, data=data_weight)
                if weight_serializer.is_valid():
                    weight_serializer.save()         
            '''
        return Response({'message': 'Data updated successfully'})
    except BaseCustomer.DoesNotExist or Weight.DoesNotExist:
        return Response({'error': 'Record not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCustomerVStamp(request, dt):
    # รายการ disable ไม่ให้อัพเดท (เนื่องจากไม่ได้ใช้งานแล้ว แต่ต้องเก็บข้อมูลไว้)
    queryset = BaseCustomer.objects.filter(v_stamp__gte = dt, is_disable = False).order_by('v_stamp')
    serializer = BaseCustomerSerializer(queryset, many = True)
    return Response(serializer.data)

############# BaseStoneType API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseStoneTypeOverview(request):
    api_urls = {
        'List':'/baseStoneType/api/list/',
        'Detail View':'/baseStoneType/api/detail/<str:pk>/',
        'Create':'/baseStoneType/api/create/',
        'Update':'/baseStoneType/api/update/<str:pk>/',
        'Delete':'/baseStoneType/api/delete/<str:pk>/',
        'VStamp':'/baseStoneType/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseStoneTypeList(request):
    queryset = BaseStoneType.objects.all()
    serializer = BaseStoneTypeSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseStoneTypeDetail(request, pk):
    queryset = BaseStoneType.objects.get(base_stone_type_id=pk)
    serializer = BaseStoneTypeSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseStoneTypeCreate(request):
    serializer = BaseStoneTypeSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseStoneTypeUpdate(request, pk):
    queryset = BaseStoneType.objects.get(base_stone_type_id=pk)
    serializer = BaseStoneTypeSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseStoneTypeVStamp(request, dt):
    queryset = BaseStoneType.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseStoneTypeSerializer(queryset, many = True)
    return Response(serializer.data)

class BaseStoneTypeList(generics.ListCreateAPIView):
    queryset = BaseStoneType.objects.all()
    serializer_class = BaseStoneTypeTestSerializer
    

############# BaseCarTeam API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseCarTeamOverview(request):
    api_urls = {
        'List':'/baseCarTeam/api/list/',
        'Detail View':'/baseCarTeam/api/detail/<str:pk>/',
        'Create':'/baseCarTeam/api/create/',
        'Update':'/baseCarTeam/api/update/<str:pk>/',
        'Delete':'/baseCarTeam/api/delete/<str:pk>/',
        'VStamp':'/baseCarTeam/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarTeamList(request):
    queryset = BaseCarTeam.objects.all()
    serializer = BaseCarTeamSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarTeamDetail(request, pk):
    queryset = BaseCarTeam.objects.get(car_team_id=pk)
    serializer = BaseCarTeamSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseCarTeamCreate(request):
    serializer = BaseCarTeamSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseCarTeamUpdate(request, pk):
    queryset = BaseCarTeam.objects.get(car_team_id=pk)
    serializer = BaseCarTeamSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarTeamVStamp(request, dt):
    queryset = BaseCarTeam.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseCarTeamSerializer(queryset, many = True)
    return Response(serializer.data)

############# BaseDriver API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseDriverOverview(request):
    api_urls = {
        'List':'/baseDriver/api/list/',
        'Detail View':'/baseDriver/api/detail/<str:pk>/',
        'Create':'/baseDriver/api/create/',
        'Update':'/baseDriver/api/update/<str:pk>/',
        'Delete':'/baseDriver/api/delete/<str:pk>/',
        'VStamp':'/baseDriver/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseDriverList(request):
    queryset = BaseDriver.objects.all()
    serializer = BaseDriverSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseDriverDetail(request, pk):
    queryset = BaseDriver.objects.get(driver_id=pk)
    serializer = BaseDriverSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseDriverCreate(request):
    serializer = BaseDriverSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseDriverUpdate(request, pk):
    queryset = BaseDriver.objects.get(driver_id=pk)
    serializer = BaseDriverSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseDriverVStamp(request, dt):
    queryset = BaseDriver.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseDriverSerializer(queryset, many = True)
    return Response(serializer.data)

############# BaseCarRegistration API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseCarRegistrationOverview(request):
    api_urls = {
        'List':'/baseCarRegistration/api/list/',
        'Detail View':'/baseCarRegistration/api/detail/<str:pk>/',
        'Create':'/baseCarRegistration/api/create/',
        'Update':'/baseCarRegistration/api/update/<str:pk>/',
        'Delete':'/baseCarRegistration/api/delete/<str:pk>/',
        'VStamp':'/baseCarRegistration/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarRegistrationList(request):
    queryset = BaseCarRegistration.objects.all()
    serializer = BaseCarRegistrationSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarRegistrationDetail(request, pk):
    queryset = BaseCarRegistration.objects.get(car_registration_id=pk)
    serializer = BaseCarRegistrationSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseCarRegistrationCreate(request):
    serializer = BaseCarRegistrationSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseCarRegistrationUpdate(request, pk):
    queryset = BaseCarRegistration.objects.get(car_registration_id=pk)
    serializer = BaseCarRegistrationSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarRegistrationVStamp(request, dt):
    queryset = BaseCarRegistration.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseCarRegistrationSerializer(queryset, many = True)
    return Response(serializer.data)

############# BaseSite API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseSiteOverview(request):
    api_urls = {
        'List':'/baseSite/api/list/',
        'Detail View':'/baseSite/api/detail/<str:pk>/',
        'Create':'/baseSite/api/create/',
        'Update':'/baseSite/api/update/<str:pk>/',
        'Delete':'/baseSite/api/delete/<str:pk>/',
        'VStamp':'/baseSite/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseSiteList(request):
    queryset = BaseSite.objects.all()
    serializer = BaseSiteSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseSiteDetail(request, pk):
    queryset = BaseSite.objects.get(base_site_id=pk)
    serializer = BaseSiteSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseSiteCreate(request):
    serializer = BaseSiteSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseSiteUpdate(request, pk):
    queryset = BaseSite.objects.get(base_site_id=pk)
    serializer = BaseSiteSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseSiteVStamp(request, dt):
    queryset = BaseSite.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseSiteSerializer(queryset, many = True)
    return Response(serializer.data)

############# BaseCar API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseCarOverview(request):
    api_urls = {
        'List':'/baseCar/api/list/',
        'Detail View':'/baseCar/api/detail/<str:pk>/',
        'Create':'/baseCar/api/create/',
        'Update':'/baseCar/api/update/<str:pk>/',
        'Delete':'/baseCar/api/delete/<str:pk>/',
        'VStamp':'/baseCar/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarList(request):
    queryset = BaseCar.objects.all()
    serializer = BaseCarSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarDetail(request, pk):
    queryset = BaseCar.objects.get(car_id=pk)
    serializer = BaseCarSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseCarCreate(request):
    serializer = BaseCarSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseCarUpdate(request, pk):
    queryset = BaseCar.objects.get(car_id=pk)
    serializer = BaseCarSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCarVStamp(request, dt):
    queryset = BaseCar.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseCarSerializer(queryset, many = True)
    return Response(serializer.data)

############# BaseJobType API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseJobTypeOverview(request):
    api_urls = {
        'List':'/baseJobType/api/list/',
        'Detail View':'/baseJobType/api/detail/<str:pk>/',
        'Create':'/baseJobType/api/create/',
        'Update':'/baseJobType/api/update/<str:pk>/',
        'Delete':'/baseJobType/api/delete/<str:pk>/',
        'VStamp':'/baseJobType/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseJobTypeList(request):
    queryset = BaseJobType.objects.all()
    serializer = BaseJobTypeSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseJobTypeDetail(request, pk):
    queryset = BaseJobType.objects.get(base_job_type_id =pk)
    serializer = BaseJobTypeSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseJobTypeCreate(request):
    serializer = BaseJobTypeSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseJobTypeUpdate(request, pk):
    queryset = BaseJobType.objects.get(base_job_type_id=pk)
    serializer = BaseJobTypeSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseJobTypeVStamp(request, dt):
    queryset = BaseJobType.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseJobTypeSerializer(queryset, many = True)
    return Response(serializer.data)


############# BaseCustomerSite API ###############
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def apiBaseCustomerSiteOverview(request):
    api_urls = {
        'List':'/baseCustomerSite/api/list/',
        'Detail View':'/baseCustomerSite/api/detail/<str:pk>/',
        'Create':'/baseCustomerSite/api/create/',
        'Update':'/baseCustomerSite/api/update/<str:pk>/',
        'Delete':'/baseCustomerSite/api/delete/<str:pk>/',
        'VStamp':'/baseCustomerSite/api/vStamp/<str:dt>/',
    }
    return Response(api_urls)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCustomerSiteList(request):
    queryset = BaseCustomerSite.objects.all()
    serializer = BaseCustomerSiteSerializer(queryset, many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCustomerSiteDetail(request, pk):
    queryset = BaseCustomerSite.objects.get(id = pk)
    serializer = BaseCustomerSiteSerializer(queryset, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def baseCustomerSiteCreate(request):
    serializer = BaseCustomerSiteSerializer(data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def baseCustomerSiteUpdate(request, pk):
    queryset = BaseCustomerSite.objects.get(id=pk)
    serializer = BaseCustomerSiteSerializer(instance=queryset, data = request.data)
    
    if serializer.is_valid():
        serializer.save()

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def baseCustomerSiteVStamp(request, dt):
    queryset = BaseCustomerSite.objects.filter(v_stamp__gte = dt).order_by('v_stamp')
    serializer = BaseCustomerSiteSerializer(queryset, many = True)
    return Response(serializer.data)

