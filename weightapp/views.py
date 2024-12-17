from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.cache import cache_page
from weightapp.models import Weight, Production, BaseLossType, ProductionLossItem, BaseMill, BaseLineType, ProductionGoal, StoneEstimate, StoneEstimateItem, BaseStoneType, BaseTimeEstimate, BaseCustomer, BaseSite, WeightHistory, BaseTransport, BaseCar, BaseScoop, BaseCarTeam, BaseCar, BaseDriver, BaseCarRegistration, BaseJobType, BaseCustomerSite, UserScale, BaseMachineType, BaseCompany, UserProfile, BaseSEC, SetWeightOY, SetCompStone, SetPatternCode, Stock, StockStone, StockStoneItem, BaseStockSource, ApproveWeight
from django.db.models import Sum, Q, Max, Value
from decimal import Decimal
from django.views.decorators.cache import cache_control
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from .filters import WeightFilter, ProductionFilter, StoneEstimateFilter, BaseMillFilter, BaseStoneTypeFilter, BaseScoopFilter, BaseCarTeamFilter, BaseCarFilter, BaseSiteFilter, BaseCustomerFilter, BaseDriverFilter, BaseCarRegistrationFilter, BaseJobTypeFilter, BaseCustomerSiteFilter, StockFilter
from .forms import ProductionForm, ProductionLossItemForm, ProductionModelForm, ProductionLossItemFormset, ProductionLossItemInlineFormset, ProductionGoalForm, StoneEstimateForm, StoneEstimateItemInlineFormset, WeightForm, WeightStockForm, BaseMillForm, BaseStoneTypeForm ,BaseScoopForm, BaseCarTeamForm, BaseCarForm, BaseSiteForm, BaseCustomerForm, BaseDriverForm, BaseCarRegistrationForm, BaseJobTypeForm, BaseCustomerSiteForm, StockForm, StockStoneForm, StockStoneItemForm, StockStoneItemInlineFormset
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
from django.db.models import Sum, Subquery
import random
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear, TruncMonth, TruncYear
from django.db.models import F, ExpressionWrapper, Case, When
from django.db import models
import pandas as pd
import calendar
from collections import defaultdict
from re import escape as reescape
from django.db.models import Value as V
from django.db.models.functions import Cast, Concat
from django.contrib.auth.decorators import login_required
from django.urls import reverse

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
from decimal import Decimal
import ast
import json
from django.conf import settings # calls the object written in settings.py
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo
from apscheduler.triggers.cron import CronTrigger
import requests

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

''' สำหรับเช็ค UserId, groupId, roomId โดยส่งข้อความไปทาง line ที่มี BOT อยู่
@csrf_exempt
def callback(request):
    if request.method == 'POST':
        body = request.body.decode('utf-8')
        req = json.loads(body)
        print('Full Payload:', json.dumps(req, indent=2))

        intent = req["queryResult"]["intent"]["displayName"]
        # Extract common data
        source = req['originalDetectIntentRequest']['payload']['data']['source']
        source_type = source.get('type')
        user_id = source.get('userId')
        group_id = source.get('groupId') if source_type == 'group' else None
        room_id = source.get('roomId') if source_type == 'room' else None

        # Log context
        print('Source Type:', source_type)
        print('User ID:', user_id)
        print('Group ID:', group_id)
        print('Room ID:', room_id)

        # Handle display name if userId is present
        display_name = None
        if user_id:
            profile = line_bot_api.get_profile(user_id)
            display_name = profile.display_name
            print('Display Name:', display_name)

        # Call reply function
        reply_token = req['originalDetectIntentRequest']['payload']['data']['replyToken']
        text = req['originalDetectIntentRequest']['payload']['data']['message']['text']

        # Call reply function
        reply(intent, text, reply_token, user_id, display_name)

        return JsonResponse({'status': 'OK'})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def reply(intent, text, reply_token, user_id, display_name):
        weight = (
            Weight.objects.filter(bws__weight_type = 1)
            .values('customer_name')
            .annotate(sum_weight_total=Sum('weight_total'))
            .order_by('-sum_weight_total')[:3]
        )
 
        # Prepare the message text
        messages = []
        for i in weight:
            tmp_text = f"ลูกค้า {i['customer_name']} : {i['sum_weight_total']} ตัน"
            messages.append(tmp_text)

        # Combine messages into a single text
        final_message = "\n".join(messages)

        text_message = TextSendMessage(text = final_message)
        line_bot_api.reply_message(reply_token, text_message)
'''

def send_weight_edit(start_time, end_time, target_user_id):
    today = datetime.today().strftime("วันที่ %d/%m/%Y")
    
    # Query weight data within the specified time range
    weight = (
        Weight.objects.filter(
            bws__weight_type=1,
            v_stamp__gte=start_time,
            v_stamp__lt=end_time
        )
        .values('doc_id', 'bws__company__name', 'v_stamp', 'date')
    )

    # Group the data by company name
    grouped_weights = defaultdict(list)
    for i in weight:
        grouped_weights[i['bws__company__name']].append(i)

    # Prepare the message text
    messages = []
    for company_name, weights in grouped_weights.items():
        company_message = f"============ {company_name} ============"
        messages.append(company_message)
        
        for idx, i in enumerate(weights, start=1):
            tmp_time = i['date'].strftime("วันที่ %d/%m/%Y")
            tmp_text = f"{idx}) เลขที่ชั่ง {i['doc_id']} {tmp_time}"
            messages.append(tmp_text)

        messages.append("\n")

    # Combine messages into a single text
    if messages:
        final_message = "🚨 "+ today + " มีการแก้ไขรายการชั่ง"+ "\n" + "\n".join(messages)
    else:
        final_message = "✅ ไม่มีข้อมูลการแก้ไขรายการชั่งของ " + today

    # Send the message
    text_message = TextSendMessage(text=final_message)
    line_bot_api.push_message(target_user_id, text_message)

def send_11am_summary():
    # Time range: previous day 3:00 PM to today 11:00 AM
    end_time = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=20)
    target_user_id = 'Cdcdb5eba3889c5a60da15702136b8726'  #user/group ID (Line id)
    send_weight_edit(start_time, end_time, target_user_id)

def send_3pm_summary():
    # Time range: today 11:00 AM to today 3:00 PM
    end_time = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=4)
    target_user_id = 'Cdcdb5eba3889c5a60da15702136b8726'  #user/group ID (Line id)
    send_weight_edit(start_time, end_time, target_user_id)

# Schedule the tasks
scheduler = BackgroundScheduler()
scheduler.add_job(
    send_11am_summary,
    trigger=CronTrigger(hour=11, minute=0),
    id="11am_summary",
    replace_existing=True,
)
scheduler.add_job(
    send_3pm_summary,
    trigger=CronTrigger(hour=15, minute=0),
    id="3pm_summary",
    replace_existing=True,
)
scheduler.start()

#generate Code Base
def generateCodeId(model_name, type, wt, middle):
    missing_id = None

    try:
        if wt:
            spc = SetPatternCode.objects.get(m_name = model_name, wt_id = wt)
        else:
            spc = SetPatternCode.objects.get(m_name = model_name)

        if type == 1:
            id_pt = spc.pattern
            start_id = spc.start + id_pt
            end_id = spc.end + id_pt
        elif type == 2:
            id_pt = spc.pattern
            start_id = id_pt + spc.start
            end_id = id_pt + spc.end
        elif type == 3:
            id_pt = middle + spc.pattern
            start_id = id_pt + spc.start
            end_id = id_pt + spc.end

        number_start = int(spc.start)
        number_end = int(spc.end)

        model_class = spc.get_model()
        if model_class:
            pk_field = model_class._meta.pk.name

            ids_in_range = model_class.objects.filter(
                Q(**{f"{pk_field}__gte": start_id}) & Q(**{f"{pk_field}__lte": end_id})
            ).values_list(pk_field, flat=True)

        # Convert to a set for faster lookup
        ids_set = set(ids_in_range)

        # Helper function to generate IDs in the given format
        def generate_id(number):
            tmp_id = None
            if type == 1:
                tmp_id = f"{str(number).zfill(len(spc.start)) + id_pt}"
            elif type == 2:
                tmp_id = f"{id_pt + str(number).zfill(len(spc.start))}"
            elif type == 3:
                tmp_id = f"{id_pt + str(number).zfill(len(spc.start))}"
            return tmp_id

        # Iterate from number_start to number_end to find the missing ID
        for i in range(number_start, number_end + 1):
            candidate_id = generate_id(i)
            if candidate_id not in ids_set:
                missing_id = candidate_id
                break
    except:
        pass

    return missing_id

def findCompanyIn(request):
    code = request.session['company_code']

    #หาหน้าต่างการมองเห็นบริษัททั้งหมดของ user
    user_profile = UserProfile.objects.get(user = request.user.id)
    company_all = BaseCompany.objects.filter(userprofile = user_profile).values('code')

    if code == "ALL":
        company_in = company_all
    else:
        company_in = BaseCompany.objects.filter(code = code).values('code')
    return company_in

def format_duration(duration):
    result = None
    if duration:
        hours = duration // timedelta(hours=1)
        minutes = (duration % timedelta(hours=1)) // timedelta(minutes=1)
        result = f"{hours:02d}:{minutes:02d}"
    return result

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

def getSumByStone(request, mode, stoneType, type, company_in):

    ''' เปลี่ยนเป็นเลือกระหว่างวันที่ 2024-04-10
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    start_date = datetime.strptime(startDateInMonth(str(previous_date_time.strftime('%Y-%m-%d'))), "%Y-%m-%d")
    end_date = datetime.strptime(endDateInMonth(str(previous_date_time.strftime('%Y-%m-%d'))), "%Y-%m-%d")
    '''

    start_date = request.session['db_start_date']
    end_date = request.session['db_end_date']

    #type 1 = sell, 2 = stock, 3 = produce
    if type == 1:
        w = Weight.objects.filter(bws__company__code__in = company_in, bws__weight_type = mode, stone_type = stoneType, date__range=(start_date, end_date)).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')
    elif type == 2:
        w = StockStone.objects.filter(stk__company__code__in = company_in, stone = stoneType, stk__created__range=(start_date, end_date)).aggregate(s=Sum("total"))["s"] or Decimal('0.0')
        #อันเก่าดึงข้อมูลจากกองสต็อค 09-09-2024
        #w = Weight.objects.filter(Q(site__base_site_name__contains ='สต็อค') | Q(site__base_site_name__contains ='สต๊อก'), bws__company__code__in = company_in, bws__weight_type = mode, stone_type = stoneType, date__range=(start_date, end_date)).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0') 
    elif type == 3:
        w = Decimal('0.0')
        se_item = StoneEstimateItem.objects.filter(se__created__range = (start_date, end_date), stone_type = stoneType).values('se__created','percent','se__site')
        for i in se_item:
            crush = Weight.objects.filter(bws__company__code__in = company_in, site = i['se__site'], bws__weight_type = mode , date = i['se__created']).aggregate(s = Sum("weight_total"))["s"] or Decimal('0.0')
            w += calculateEstimate(i['percent'], crush)
    return  float(w)

def getSumOther(request, mode, list_sum_stone, type, company_in):
    ''' เปลี่ยนเป็นเลือกระหว่างวันที่ 2024-04-10
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    start_date = datetime.strptime(startDateInMonth(str(previous_date_time.strftime('%Y-%m-%d'))), "%Y-%m-%d")
    end_date = datetime.strptime(endDateInMonth(str(previous_date_time.strftime('%Y-%m-%d'))), "%Y-%m-%d")    
    '''

    start_date = request.session['db_start_date']
    end_date = request.session['db_end_date']

    query_filters = Q()
    ss_query_filters = Q()
    for item_number_prefix in list_sum_stone:
        query_filters |= Q(stone_type = item_number_prefix)
        ss_query_filters |= Q(stone = item_number_prefix)

    #type 1 = sell, 2 = stock, 3 = produce
    if type == 1:
        w = Weight.objects.filter(bws__company__code__in = company_in, bws__weight_type = mode, date__range=(start_date, end_date)).exclude(query_filters).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')
    elif type == 2:
        #อันเก่าดึงข้อมูลจากกองสต็อค 09-09-2024
        #w = Weight.objects.filter(bws__company__code__in = company_in, site__base_site_name__contains='สต็อค', bws__weight_type = mode, date__range=(start_date, end_date)).exclude(query_filters).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')
        w = StockStone.objects.filter(stk__company__code__in = company_in, stk__created__range=(start_date, end_date)).exclude(ss_query_filters).aggregate(s=Sum("total"))["s"] or Decimal('0.0')
    elif type == 3:
        w = Decimal('0.0')
        se_item = StoneEstimateItem.objects.filter(se__created__range = (start_date, end_date)).exclude(query_filters).values('se__created','percent','se__site')
        for i in se_item:
            crush = Weight.objects.filter(bws__company__code__in = company_in, site = i['se__site'], bws__weight_type = mode , date = i['se__created']).aggregate(s = Sum("weight_total"))["s"] or Decimal('0.0')
            w += calculateEstimate(i['percent'], crush)
    return  float(w)

def getNumListStoneWeightChart(request, mode, stone_list_id, type, company_in):
    #sell
    list_sum_stone = []
    for stone_id in stone_list_id:
        list_sum_stone.append(getSumByStone(request, mode, stone_id, type, company_in))

    list_sum_stone.append(getSumOther(request, mode, stone_list_id, type, company_in))
    return list_sum_stone

# Create your views here.
@login_required(login_url='login')
def index(request):
    try:
        #active : active คือแท็ปบริษัท active
        active = request.session['company_code']
        company_in = findCompanyIn(request)

        start_date = request.session['db_start_date']
        end_date = request.session['db_end_date']
        now_date = datetime.strptime(start_date, "%Y-%m-%d")

        start_day = datetime.strptime(start_date, "%Y-%m-%d")
        end_day = datetime.strptime(end_date, "%Y-%m-%d")
    except:
        return redirect('logout')

    # today date
    current_date = datetime.now()
    previous_day = current_date - timedelta(days=1)

    ''' เปลี่ยนเป็นเลือกระหว่างวันที่ 2024-04-10
    #list วันที่ทั้งหมด ระหว่าง startDate และ endDate
    start_date = datetime.strptime(startDateInMonth(str(previous_day.strftime('%Y-%m-%d'))), "%Y-%m-%d")
    end_date = datetime.strptime(endDateInMonth(str(previous_day.strftime('%Y-%m-%d'))), "%Y-%m-%d")
    now_date = datetime.strptime(str(previous_day.strftime('%Y-%m-%d')), "%Y-%m-%d")
    '''

    ####################################
    ###### list customer weight ########
    ####################################
    ''' เปลี่ยนเป็นเลือกระหว่างวันที่ 2024-04-10
    weight = Weight.objects.filter(bws__company__code__in = company_in, date = previous_day, bws__weight_type = 1).values('date','customer_name').annotate(sum_weight_total=Sum('weight_total')).order_by('-sum_weight_total')
    sum_all_weight = Weight.objects.filter(bws__company__code__in = company_in, date = previous_day, bws__weight_type = 1).aggregate(s=Sum('weight_total'))["s"]
    '''
    #แสดงชื่อลูกค้าแค่ 10 อันดับแรกที่มีน้ำหนักสูงสุด
    weight = Weight.objects.filter(bws__company__code__in = company_in, date__range=(start_date, end_date), bws__weight_type = 1).values('customer_name').annotate(sum_weight_total=Sum('weight_total')).order_by('-sum_weight_total')[:10]
    sum_all_weight = Weight.objects.filter(bws__company__code__in = company_in, date__range=(start_date, end_date), bws__weight_type = 1).aggregate(s=Sum('weight_total'))["s"]

    ####################################
    ######## data weight stock #########
    ####################################
    mill_name_list = []

    s_comp_id = BaseSite.objects.filter(s_comp__code = active).values_list('base_site_id').order_by('base_site_id')
    s_comp_name = BaseSite.objects.filter(s_comp__code = active).values('base_site_name').order_by('base_site_id')

    s_comp = BaseSite.objects.filter(s_comp__code = active).values('base_site_id', 'base_site_name').order_by('base_site_id')
    # เปลี่ยนเป็นเลือกระหว่างวันที่ 2024-04-10 -> data_sum_produc_all = Weight.objects.filter(bws__company__code__in = company_in, site__in = s_comp_id, date = previous_day, bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]
    data_sum_produc_all = Weight.objects.filter(bws__company__code__in = company_in, site__in = s_comp_id, date__range=(start_date, end_date), bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]

    data_sum_produc = []
    data_sum_produc.append(('Total', data_sum_produc_all))

    for site in s_comp:
        ''' เปลี่ยนเป็นเลือกระหว่างวันที่ 2024-04-10
        aggregated_value = Weight.objects.filter(
            bws__company__code__in=company_in,
            site=site['base_site_id'],
            date=previous_day,
            bws__weight_type=2
        ).aggregate(s=Sum("weight_total"))["s"]        
        '''
        aggregated_value = Weight.objects.filter(
            bws__company__code__in=company_in,
            site=site['base_site_id'],
            date__range=(start_date, end_date),
            bws__weight_type=2
        ).aggregate(s=Sum("weight_total"))["s"] 

        
        # Append a tuple (site_id, aggregated_value) to the list
        data_sum_produc.append((site['base_site_name'], aggregated_value))
    
    ####################################
    ########### chart stone ############
    ####################################
    #ดึงชนิดหินตามบริษัท ถ้าไม่มีดึงตามนี้ 'หิน 3/4', 'หิน 40/80', 'หินฝุ่น', 'หินคลุก A', 'หินคลุก B', 'อื่นๆ',
    try:
        set_stone = SetCompStone.objects.filter(comp__code = active)
        result_list = list(set_stone.values_list('stone', flat=True))

        text_value = result_list[0]
        stone_list = text_value.replace("'", "").split(',')
    except:
        stone_list = ['01ST', '07ST', '09ST', '10ST', '16ST']

    #หาชื่อหินจาก stone_list
    stone_name_list = list(BaseStoneType.objects.filter(base_stone_type_id__in = stone_list).values_list('base_stone_type_name', flat=True).order_by('base_stone_type_id'))
    stone_name_list.append('อื่นๆ')
    
    #หาจำนวนตันจาก stone_list
    sell_list = getNumListStoneWeightChart(request, 1, stone_list, 1, company_in)
    stock_list = getNumListStoneWeightChart(request, 2, stone_list, 2, company_in)
    produce_list = getNumListStoneWeightChart(request, 2, stone_list, 3, company_in)

    ####################################
    ########### chart mill #############
    ####################################

    #สร้าง list ระหว่าง start_date และ end_date
    list_date_between = pd.date_range(start_date, end_date).tolist()
    list_date = [date.strftime("%Y-%m-%d") for date in list_date_between]

    # Define lists to store cumulative totals and goal percentages for each mill
    list_goal_mills = [[] for _ in range(len(s_comp_id))]
    cumulative_totals = [0] * len(s_comp_id)

    # Fetch sum goals for each mill
    sum_goals = {}
    for mill_id in s_comp_id:
        sum_goals[mill_id] = ProductionGoal.objects.filter(
            date__year=now_date.year,
            date__month=now_date.month,
            site=mill_id
        ).aggregate(s=Sum('accumulated_goal'))['s']

    # Fetch weights for each mill within the date range
    weights = {}
    for i, mill_id in enumerate(s_comp_id):
        weights[mill_id] = Weight.objects.filter(
            date__range=(start_date, end_date),
            site=mill_id
        ).values('date').annotate(
            cumulative_total=Sum('weight_total')
        ).order_by('date')

    # Iterate through list_date
    for date in list_date:
        for i, mill_id in enumerate(s_comp_id):
            # Iterate through weights for the current mill and update cumulative total
            for w in weights[mill_id]:
                if str(date) == str(w['date']):
                    cumulative_totals[i] += w['cumulative_total']
            # Append goal percentage to the corresponding list
            list_goal_mills[i].append(calculatePersent(cumulative_totals[i], sum_goals[mill_id]))

    list_goal_mill = []
    for i, mill in enumerate(s_comp):
        list_goal_mill.append((mill['base_site_name'], list_goal_mills[i]))

    ####################################
    ##chart loss weight เวลาที่เสีย (ผลิต)##
    ####################################
    actual_working_time = {}
    total_loss_time = {}
    persent_loss_weight = {}
    list_persent_loss_weight = []

    # Iterate over the mill site IDs
    for site_id in s_comp_id:
        # Filter Production objects for the current mill site and calculate actual working time
        actual_working_time[site_id] = Production.objects.filter(
            created__year=f'{now_date.year}',
            created__month=f'{now_date.month}',
            site=site_id
        ).annotate(
            working_time=ExpressionWrapper(F('actual_time') - F('total_loss_time'), output_field=models.DurationField())
        ).aggregate(total_working_time=Sum('working_time'))['total_working_time']

        # Filter Production objects for the current mill site and calculate total loss time
        total_loss_time[site_id] = Production.objects.filter(
            created__range=(start_date, end_date),
            site=site_id
        ).aggregate(s=Sum('total_loss_time'))["s"]

        # Calculate percentage loss weight for the current mill site
        persent_loss_weight[site_id] = calculatePersent(
            total_loss_time[site_id] if total_loss_time[site_id] else None,
            actual_working_time[site_id]
        )
        list_persent_loss_weight.append(persent_loss_weight[site_id])

    actual_working_time_all = Production.objects.filter(company__code = active, created__year = f'{now_date.year}' , created__month = f'{now_date.month}').annotate(working_time = ExpressionWrapper(F('actual_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']
    total_loss_time_all = Production.objects.filter(company__code = active, created__range = (start_date, end_date)).aggregate(s=Sum('total_loss_time'))["s"]
    persent_loss_weight_all = calculatePersent(total_loss_time_all if total_loss_time_all else None, actual_working_time_all)

    # Add list
    list_persent_loss_weight.append(persent_loss_weight_all)

    context = { 'weight': weight,
                'previous_day':previous_day,
                'start_day':start_day,
                'end_day':end_day,
                'actual_working_time_all':actual_working_time_all,
                'sum_all_weight': sum_all_weight,
                'sell_list':sell_list,
                'stock_list':stock_list,
                'produce_list':produce_list,
                'data_sum_produc_all':data_sum_produc_all,
                'data_sum_produc':data_sum_produc,
                'list_date': list_date,
                'list_goal_mill' : list_goal_mill,
                'list_persent_loss_weight':list_persent_loss_weight,
                'stone_name_list':stone_name_list,
                'dashboard_page':'active',
                active :"active",}
    return render(request, "index.html",context)

def calculatePersent(num, num_all):
    persent = 0.0
    if num_all and num:
        persent = (num/num_all)*100
    return round(persent)

def is_scale(user):
    return user.groups.filter(name='scale').exists()

def is_account(user):
    return user.groups.filter(name='account').exists()

def is_edit_weight(user):
    return user.groups.filter(name='edit_weight').exists()

def is_edit_setting(user):
    return user.groups.filter(name='edit_setting').exists()

def is_view_weight(user):
    return user.groups.filter(name='view_weight').exists()

def is_edit_base_id(user):
    return user.groups.filter(name='edit_base_id').exists()

def is_edit_stock(user):
    return user.groups.filter(name='edit_stock').exists()

def is_approve_weight(user):
    return user.groups.filter(name='approve_weight').exists()

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
                #CPT*เลือกตามบริษัท 
                try:
                    user_profile = UserProfile.objects.get(user = request.user.id)
                    company = BaseCompany.objects.filter(userprofile = user_profile).first()
                except:
                    company = None
                request.session['company_code'] = company.code
                request.session['company'] = company.name

                #set session date in dashbord
                current_date_time = datetime.today()
                previous_date_time = current_date_time - timedelta(days=1)

                start_date = datetime.strptime(startDateInMonth(str(previous_date_time.strftime('%Y-%m-%d'))), "%Y-%m-%d")
                end_date = datetime.strptime(endDateInMonth(str(previous_date_time.strftime('%Y-%m-%d'))), "%Y-%m-%d")

                request.session['db_start_date'] = f'{start_date.strftime("%Y-%m-%d")}'
                request.session['db_end_date'] = f'{end_date.strftime("%Y-%m-%d")}'

                return redirect('home')
            else:
                return redirect('signUp')
    else:
        form = AuthenticationForm()
        #CPT*เลือกตามบริษัท 
        company = BaseCompany.objects.first()
        request.session['company_code'] = company.code
        request.session['company'] = company.name

    return render(request, 'account/login.html', {'form':form,})

def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def weightTable(request):
    ''' old บริษัทเดียว
    active = None
    if is_scale(request.user):
        us = UserScale.objects.filter(user = request.user).values_list('scale_id')
        data = Weight.objects.filter(scale_id__in = us).order_by('-date','weight_id')
    elif request.user.is_superuser or is_view_weight(request.user) or is_edit_weight(request.user) or is_account(request.user):
        data = Weight.objects.all().order_by('-date','weight_id')    
    '''

    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')


    #CPT*เลือกตามบริษัท
    '''
    if is_scale(request.user):
        us = UserScale.objects.filter(user = request.user).values_list('scale_id')
        data = Weight.objects.filter(scale_id__in = us).order_by('-date','weight_id')
    elif request.user.is_superuser or is_view_weight(request.user) or is_edit_weight(request.user) or is_account(request.user):
        data = Weight.objects.filter(bws__company__code__in = company_in).order_by('-date','weight_id')    
    '''
    data = Weight.objects.filter(bws__company__code__in = company_in).order_by('-date','weight_id')

    #กรองข้อมูล
    myFilter = WeightFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    weight = p.get_page(page)

    context = {'weight':weight,'filter':myFilter, 'weightTable_page':'active', 'is_view_weight' : is_view_weight(request.user), 'is_approve_weight' : is_approve_weight(request.user), 'is_scale' : is_scale(request.user), 'is_account' :is_account(request.user), active :"active",}
    return render(request, "weight/weightTable.html",context)

@login_required(login_url='login')
def approveWeight(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = Weight.objects.filter(bws__company__code__in = company_in).values_list('date', flat=True).order_by('-date').distinct()
    ap_data = ApproveWeight.objects.filter(company__code = active)

    #กรองข้อมูล
    myFilter = WeightFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    weight = p.get_page(page)

    if request.method=='POST':
        checkbox_data = request.POST.get('checkboxData')

        if checkbox_data:
            checkbox_data = json.loads(checkbox_data)
            
            for item in checkbox_data:
                formatted_date = item['date']
                is_checked = item['isChecked']
                try:
                    ap = ApproveWeight.objects.get(company__code = active, date = formatted_date)
                    ap.is_approve = is_checked
                    ap.save()
                except ApproveWeight.DoesNotExist:
                    company = BaseCompany.objects.get(code = active)
                    ap = ApproveWeight.objects.create(
                        company = company,
                        date = formatted_date,
                        is_approve = is_checked,
                        update = datetime.now()
                    )
                
                w = Weight.objects.filter(bws__company__code = active, date = formatted_date)
                w.update(apw = ap)

        return redirect('weightTable')

    context = {'weight':weight, 'ap_data': ap_data, 'filter':myFilter, 'weightTable_page':'active', active :"active",}
    return render(request, "weight/approveWeight.html",context)

@login_required(login_url='login')
def editWeight(request, mode, weight_id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

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

    context = {'weightTable_page': 'active', 'form': form, 'weight': weight_data, 'is_edit_weight': is_edit_weight(request.user), active :"active", 'disabledTab' : 'disabled'}
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

def createCustomerId(request):
    if 'job_type_id' in request.GET:
        job_type_id = request.GET.get('job_type_id')
        weight_type_id = request.GET.get('weight_type_id')

        if weight_type_id == '1' and job_type_id:
            missing_customer_id  = generateCodeId('BaseCustomer', 3, 1, job_type_id)
        elif weight_type_id == '2':
            missing_customer_id  = generateCodeId('BaseCustomer', 1, 2, None)
        else:
            missing_customer_id  = None

        val = missing_customer_id
    data = {
        'val': val,
    }
    return JsonResponse(data)

def createCarId(request):
    if 'car_team_id' in request.GET:
        car_team_id = request.GET.get('car_team_id')
        missing_customer_id  = generateCodeId('BaseCar', 3, None, car_team_id)
        val = missing_customer_id
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
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    # Query ข้อมูลขาย
    #ดึงข้อมูลต้นทางกองสต็อค ที่มีในรายการชั่งของบริษัทนี้
    stock_name = Weight.objects.filter(my_q, Q(mill_name__contains='สต็อค') | Q(mill_name__contains='สต๊อก'), bws__weight_type = 1, bws__company__code = active).values_list('mill_id').order_by('mill_id').distinct()

    #ดึงข้อมูลต้นทางกองสต็อคและโรงโม่ของบริษัท
    m_comp_id = BaseMill.objects.filter(Q(m_comp__code = active) | Q(mill_id__in = stock_name)).values_list('mill_id').order_by('mill_id')
    data = Weight.objects.filter(my_q, mill__in = m_comp_id, bws__weight_type = 1).order_by('date','mill','stone_type').values_list('date','mill_name', 'stone_type_name').annotate(sum_weight_total = Sum('weight_total'))
    
    # Query ข้อมูลผลิตรวม
    s_comp_id = BaseSite.objects.filter(s_comp__code = active).values_list('base_site_id').order_by('base_site_id')
    data_sum_produc = Weight.objects.filter(my_q, site__in = s_comp_id, bws__weight_type = 2).order_by('date','site').values_list('date','site_name').annotate(sum_weight_total = Sum('weight_total'))

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

        column_index = 2 + len(s_comp_id)
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
                line_index = (cell.column - ( len(s_comp_id) + 2 )) // (len(stones))
                fill_color = mill_colors[line_index % len(mill_colors)]
                fill = PatternFill(start_color=fill_color, fill_type="solid")
                cell.fill = fill

        # Write headers row 2 to the worksheet
        column_index = 2 + len(s_comp_id)
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
                    column_index = 2 + len(s_comp_id)
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

        '''
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
        '''

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
        worksheet.cell(row = 1, column = 1, value = f'ไม่มีข้อมูลยอดขายตามประเภทหินของเดือนนี้')

    # Set the response headers for the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=sales_daily_({active}).xlsx'

    # Save the workbook to the response
    workbook.save(response)
    return response

def exportExcelProductionByStone(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

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

    my_q &= Q(bws__company__code__in = company_in)
    my_q &= ~Q(customer_name ='ยกเลิก')
   
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    startDate = datetime.strptime(start_created or startDateInMonth(previous_date_time.strftime('%Y-%m-%d')), "%Y-%m-%d").date()
    endDate = datetime.strptime(end_created or previous_date_time.strftime('%Y-%m-%d'), "%Y-%m-%d").date()

    #สร้าง list ระหว่าง start_date และ end_date
    list_date = [startDate+timedelta(days=x) for x in range((endDate-startDate).days + 1)]

    response = excelProductionByStone(request, my_q, list_date)
    return response

def exportExcelProductionByStoneInDashboard(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    ''' แบบเก่าดึง รายงานผลิตหิน ตามเดือนนั้นๆ 09/05/2024
    #ดึงรายงานของเดือนนั้นๆ
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    end_created = previous_date_time.strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)
    '''
    end_created = request.session['db_end_date']
    start_created = request.session['db_start_date']

    my_q = Q()
    if start_created is not None:
        my_q &= Q(date__gte = start_created)
    if end_created is not None:
        my_q &=Q(date__lte = end_created)

    my_q &= Q(bws__company__code__in = company_in)
    my_q &= ~Q(customer_name ='ยกเลิก')

    #เปลี่ยนออกเป็น ดึงรายงานของเดือนนั้นๆเท่านั้น
    startDate = datetime.strptime(start_created, "%Y-%m-%d").date()
    endDate = datetime.strptime(end_created, "%Y-%m-%d").date()

    #สร้าง list ระหว่าง start_date และ end_date
    list_date = [startDate+timedelta(days=x) for x in range((endDate-startDate).days + 1)]

    response = excelProductionByStone(request, my_q, list_date)
    return response

def excelProductionByStoneAndMonth(request, my_q, list_date):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    # Query ข้อมูลขาย
    #ดึงข้อมูลต้นทางกองสต็อค ที่มีในรายการชั่งของบริษัทนี้
    stock_name = Weight.objects.filter(my_q, Q(mill_name__contains='สต็อค') | Q(mill_name__contains='สต๊อก'), bws__weight_type = 1, bws__company__code = active).values_list('mill_id').order_by('mill_id').distinct()
    
    #ดึงข้อมูลต้นทางกองสต็อคและโรงโม่ของบริษัท
    m_comp_id = BaseMill.objects.filter(Q(m_comp__code = active) | Q(mill_id__in = stock_name)).values_list('mill_id').order_by('mill_id')
    data = Weight.objects.filter(my_q, mill__in = m_comp_id, bws__weight_type = 1).annotate(
        month=ExtractMonth('date'),
        year=ExtractYear('date')
    ).values_list('year', 'month', 'mill_name', 'stone_type_name').annotate(
        sum_weight_total=Sum('weight_total')
    ).order_by('year', 'month', 'mill_name', 'stone_type_name')
    
    # Query ข้อมูลผลิตรวม
    s_comp_id = BaseSite.objects.filter(s_comp__code = active).values_list('base_site_id').order_by('base_site_id')
    data_sum_produc = Weight.objects.filter(my_q, site__in = s_comp_id, bws__weight_type = 2).annotate(
        month=ExtractMonth('date'),
        year=ExtractYear('date')
    ).values_list('year', 'month', 'site_name').annotate(
        sum_weight_total=Sum('weight_total')
    ).order_by('year', 'month', 'site_name')

    # Create a new workbook and get the active worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active


    if data or data_sum_produc:
        date_style = NamedStyle(name='custom_datetime', number_format='DD/MM/YYYY')
        
        # Create a set of all unique mill and stone values
        mills = set()
        stones = set()
        for item in data:
            mills.add(item[2])
            stones.add(item[3]) 

        mill_col_list = []

        # Create a list of colors for each line_type
        mill_colors = [generate_pastel_color() for i  in range(len(mills) + 1)]

        column_index = 2 + len(s_comp_id)
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
                line_index = (cell.column - (len(s_comp_id) + 2)) // (len(stones))
                fill_color = mill_colors[line_index % len(mill_colors)]
                fill = PatternFill(start_color=fill_color, fill_type="solid")
                cell.fill = fill

        # Write headers row 2 to the worksheet
        column_index = 2 + len(s_comp_id)
        for mill in mills:
            for stone in stones:
                worksheet.cell(row=2, column=column_index, value=stone).alignment = Alignment(horizontal='center')
                column_index += 1

        # Create a dictionary to store data by date, mill, and stone
        date_data = {}

        # Loop through the data and populate the dictionary  
        for item in data:
            date = (item[0], item[1])
            mill = item[2]
            stone = item[3]
            value = item[4]

            if date not in date_data:
                date_data[date] = {}

            if mill not in date_data[date]:
                date_data[date][mill] = {}

            date_data[date][mill][stone] = value

        row_index = 3
        for idl, ldate in enumerate(list_date):
                #เขียนวันที่ใน worksheet column 1
                worksheet.cell(row=idl+3, column=1, value=str(ldate))
                worksheet.cell(row=idl+3, column=1).alignment = Alignment(horizontal='center')

                for date, mill_data in date_data.items():
                    #เขียน weight total ของแต่ละหินใน worksheet
                    if str(worksheet.cell(row=idl+3, column = 1).value) == str(date):
                        column_index = 2 + len(s_comp_id)
                        for mill in mills:
                            stone_data = mill_data.get(mill, {})
                            for stone in stones:
                                value = stone_data.get(stone, '')
                                worksheet.cell(row=idl+3, column=column_index, value=value).number_format = '#,##0.00'
                                column_index += 1
                        #row_index += 1
                row_index += 1
 
        #นำข้อมูลการผลิตมาเรียง
        sorted_queryset = sorted(data_sum_produc, key=lambda x: (x[0], x[1]))

        # Create a dictionary to store the summed values by date and mill_name
        summed_values = {}
        for year, month, mill_name, value in sorted_queryset:
            key = ((year, month), mill_name)
            summed_values[key] = summed_values.get(key, 0) + float(value)

        mill_produc_list = []

        # Create headers
        headers = ['Date'] + list(set(row[2] for row in sorted_queryset))
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

        '''
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
        '''


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
        worksheet.cell(row = 1, column = 1, value = f'ไม่มีข้อมูลยอดขายตามประเภทหินของเดือนนี้')

    # Set the response headers for the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=sales_monthly_({active}).xlsx'

    # Save the workbook to the response
    workbook.save(response)
    return response

def exportExcelProductionByStoneAndMonthInDashboard(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    #ดึงรายงานของเดือนนั้นๆ
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    end_created = previous_date_time.strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)

    my_q = Q()
    my_q &= Q(bws__company__code__in = company_in)
    my_q &= ~Q(customer_name ='ยกเลิก')

    #ดึงรายงานของปีนั้นๆทั้งหมด
    startDate = datetime.strptime(start_created, "%Y-%m-%d").date()
    endDate = datetime.strptime(end_created, "%Y-%m-%d").date()

    # สร้าง list ระหว่าง start_date และ end_date ในรูปแบบ (year, month)
    list_year_month = [(year, month) for year in range(startDate.year, endDate.year+1) for month in range(1, 13)]

    response = excelProductionByStoneAndMonth(request, my_q, list_year_month)
    return response

def exportExcelProductionByStoneAndMonth(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

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

    my_q &= Q(bws__company__code__in = company_in)
    my_q &= ~Q(customer_name ='ยกเลิก')
   
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    startDate = datetime.strptime(start_created or startDateInMonth(previous_date_time.strftime('%Y-%m-%d')), "%Y-%m-%d").date()
    endDate = datetime.strptime(end_created or previous_date_time.strftime('%Y-%m-%d'), "%Y-%m-%d").date()

    # สร้าง list ระหว่าง start_date และ end_date ในรูปแบบ (year, month)
    list_year_month = [(year, month) for year in range(startDate.year, endDate.year+1) for month in range(1, 13)]

    response = excelProductionByStoneAndMonth(request, my_q, list_year_month)
    return response

@login_required(login_url='login')
def viewProduction(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = Production.objects.filter(company__code__in = company_in).order_by('-created', 'site')

    #กรองข้อมูล
    myFilter = ProductionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    product = p.get_page(page)

    context = {'production_page':'active', 'product': product,'filter':myFilter, active :"active",}
    return render(request, "production/viewProduction.html",context)

@login_required(login_url='login')
def summaryProduction(request):
    #active : active คือแท็ปบริษัท active
    active = request.session['company_code']
    company_in = findCompanyIn(request)
    
    ''' แบบเก่าดึง weekly report ตามเดือนนั้นๆ 09/05/2024
    #ดึงข้อมูลย้อนหลัง 1 วัน
    previous_date_time = date_object - timedelta(days=1)

    end_created = previous_date_time.strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)
    '''
    #ดึงข้อมูลวันนี้
    date_object = datetime.today()

    end_created = request.session['db_end_date']
    start_created = request.session['db_start_date']

    start_day = datetime.strptime(start_created, "%Y-%m-%d")
    end_day = datetime.strptime(end_created, "%Y-%m-%d")

    b_site = Production.objects.filter(company__code__in = company_in).values('site').distinct()

    real_pd = Weight.objects.filter(bws__company__code__in = company_in, site__in = b_site, date__range=(start_created, end_created), bws__weight_type = 2).values('site__base_site_id', 'site__base_site_name').order_by('site__base_site_id').annotate(sum_weight = Sum("weight_total"))

    pd = Production.objects.filter(company__code__in = company_in, created__range=(start_created, end_created)).values('site__base_site_id', 'site__base_site_name', 'pd_goal__accumulated_goal').order_by('site__base_site_id').annotate(count=Count('site__base_site_id') 
        , sum_goal = Sum('goal'), sum_loss = Sum('total_loss_time'), sum_actual = Sum('actual_time'), sum_run = Sum('run_time'), percent_p = ExpressionWrapper(F('sum_run') / F('sum_actual'), output_field= models.DecimalField())
        , sum_uncontrol=Sum(Case(When(uncontrol_time__isnull=True, then=Value(timedelta(0))), default='uncontrol_time', output_field = models.DurationField()))
        , sum_loss_n_un = ExpressionWrapper(F('sum_loss') - F('sum_uncontrol'), output_field= models.DurationField())
        , working_time = ExpressionWrapper(F('sum_actual') - F('sum_uncontrol') , output_field= models.DurationField()), working_time_de = ExpressionWrapper(F('sum_actual') - F('sum_uncontrol') , output_field= models.IntegerField())
        , stone_time = ExpressionWrapper(F('working_time') - F('sum_loss_n_un') , output_field= models.DurationField()), stone_time_de = ExpressionWrapper(F('working_time') - F('sum_loss_n_un') , output_field= models.IntegerField())
        , percent_a = ExpressionWrapper(F('stone_time') / F('working_time') * 100, output_field= models.DecimalField())
        , percent_goal = ExpressionWrapper(F('sum_goal') / F('pd_goal__accumulated_goal') * 100, output_field= models.IntegerField()), loss_weight = ExpressionWrapper(F('pd_goal__accumulated_goal') - F('sum_goal'), output_field= models.FloatField())
        , capacity = ExpressionWrapper(F('sum_goal') / (F('working_time_de')/1000000/3600), output_field= models.DecimalField())
        , percent_loss = ExpressionWrapper(F('sum_loss_n_un') / F('working_time') * 100, output_field= models.DecimalField()))

    # M = เครื่องจักรหลัก, S = เครื่องจักรรอง ไว้แสดงข้อมูลเท่านั้น
    pd_loss_mc = ProductionLossItem.objects.filter(production__company__code__in = company_in, production__created__range=(start_created, end_created), mc_type__kind = 'M').order_by('production__site__base_site_id').values('production__site__base_site_id', 'mc_type').annotate(sum_time = Sum('loss_time'))
    
    mc_loos_type = ProductionLossItem.objects.filter(production__company__code__in = company_in, production__created__range=(start_created, end_created), mc_type__kind = 'S').order_by('mc_type__id').values('mc_type__name', 'loss_type__name').distinct()
    pd_loss_pro = ProductionLossItem.objects.filter(production__company__code__in = company_in, production__created__range=(start_created, end_created), mc_type__kind = 'S').order_by('production__site__base_site_id', 'mc_type__id').values('production__site__base_site_id', 'mc_type__id', 'mc_type__name', 'loss_type__name').annotate(sum_time = Sum('loss_time'))
    mc_type  = BaseMachineType.objects.filter(kind = 'M')

    s_comp_id = BaseSite.objects.filter(s_comp__code = active).values_list('base_site_id').order_by('base_site_id')

    s_target = BaseSite.objects.filter(s_comp__code = active).values('base_site_id', 'target').order_by('base_site_id')
    
    list_ls_name = [[] for _ in range(len(s_comp_id))]
    list_ls_val = [[] for _ in range(len(s_comp_id))]
    list_ls = []

    for i, mill_id in enumerate(s_comp_id):
        list_ls_name[i] = getLossNameByMill(company_in, mill_id, start_created, end_created, 1)
        list_ls_val[i] = getLossNameByMill(company_in, mill_id, start_created, end_created, 2)
        list_ls.append((list_ls_name[i], list_ls_val[i]))

    pd_loss_all = ProductionLossItem.objects.filter(production__company__code__in = company_in, production__created__range=(start_created, end_created)).order_by('production__site__base_site_id').values('production__site__base_site_id', 'mc_type__name').annotate(sum_time = Sum('loss_time'))

    context = {'dashboard_page':'active','pd':pd,
               'pd_loss_mc':pd_loss_mc, 'pd_loss_pro':pd_loss_pro,
               'date_object':date_object, 'mc_type':mc_type,
               'list_ls': list_ls,
               'pd_loss_all':pd_loss_all,
               'mc_loos_type':mc_loos_type,
               'real_pd':real_pd,
               's_target':s_target,
               'start_day':start_day,
               'end_day': end_day,
               active :"active",
    }
    return render(request, "production/summaryProduction.html",context)

def extract_month_year(date):
    return date.strftime("%Y-%m")

@login_required(login_url='login')
def monthlyProduction(request):
    #active : active คือแท็ปบริษัท active
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    #ดึงข้อมูล 2024 ขึ้นไป   
    current_date_time = datetime.now()
    current_year = current_date_time.year - 1

    s_comp = BaseSite.objects.filter(s_comp__code = active).order_by('base_site_id')
    #ดึงข้อมูล 2024 ขึ้นไป
    date_data = StoneEstimate.objects.filter(site__in = s_comp, created__year__gt = current_year).values_list('created', 'site' , 'site__base_site_name').order_by('site', 'created')

    stone_name = BaseStoneType.objects.filter(is_stone_estimate = True).values_list('base_stone_type_name', flat=True).order_by('base_stone_type_id')

    results = {}
    for dt in date_data:
        created_date, site_id, site_name = dt
        crush = Weight.objects.filter(bws__weight_type=2, date=created_date, site=site_id).order_by('date').aggregate(s_weight=Sum("weight_total"), c_weight=Count('weight_total'))

        stone_types = StoneEstimateItem.objects.filter(se__site__in = s_comp).order_by('stone_type').values_list('stone_type', 'stone_type__base_stone_type_name').distinct()
        for st in stone_types:
            stone_type , stone_type_name = st
            percent = StoneEstimateItem.objects.filter(se__created = created_date, se__site = site_id, stone_type = stone_type).order_by(
                'stone_type').values_list('percent', flat=True).first()
            
            if crush['s_weight'] is not None and percent is not None:
                result = Decimal(crush['s_weight']) * Decimal(percent) / 100
            else:
                result = Decimal(0)
            
            if site_name not in results:
                results[site_name] = {}
            if stone_type_name not in results[site_name]:
                results[site_name][stone_type_name] = {}
            
            results[site_name][stone_type_name][created_date] = result

    totals = {}  # Initialize a dictionary to hold totals for each stone type
    for site_name, stone_data in results.items():
        for stone_type_name, date_data in stone_data.items():
            for created_date, value in date_data.items():
                if stone_type_name not in totals:
                    totals[stone_type_name] = {}
                if created_date not in totals[stone_type_name]:
                    totals[stone_type_name][created_date] = Decimal(0)
                totals[stone_type_name][created_date] += value

    # Add totals to results under a special key like "Total"
    total_values = {}
    for stone_type_name, date_data in totals.items():
        total_values[stone_type_name] = {}
        for created_date, total_value in date_data.items():
            total_values[stone_type_name][created_date] = total_value

    results["Total"] = total_values

    '''
    #only print
    for site_name, site_data in results.items():
        print(f"Site: {site_name}")
        for stone_type, stone_type_data in site_data.items():
            for date, result in stone_type_data.items():
                print(f"  Date: {date}, stone ID: {stone_type}, Result: {result}")        
    '''
    
    aggregated_results = {}

    for site_name, site_data in results.items():
        for stone_type, stone_type_data in site_data.items():
            for created_date, result in stone_type_data.items():

                month_year = extract_month_year(created_date)
                
                if site_name not in aggregated_results:
                    aggregated_results[site_name] = {}
                if stone_type not in aggregated_results[site_name]:
                    aggregated_results[site_name][stone_type] = {}
                if month_year not in aggregated_results[site_name][stone_type]:
                    aggregated_results[site_name][stone_type][month_year] = 0
                
                aggregated_results[site_name][stone_type][month_year] += result

    '''
    #only print
    for site_name, site_data in aggregated_results.items():
        for stone_type, stone_type_data in site_data.items():
            for month_year, result in stone_type_data.items():
                print(f"  Month-Year: {month_year}, stone ID: {stone_type}, Result: {result}")    
    '''

    sum_aggregated = {}
    for site_name, site_data in aggregated_results.items():
        for stone_type, stone_type_data in site_data.items():
            for month_year, result in stone_type_data.items():
                if site_name not in sum_aggregated:
                    sum_aggregated[site_name] = {}
                if month_year not in sum_aggregated[site_name]:
                    sum_aggregated[site_name][month_year] = 0
                    
                sum_aggregated[site_name][month_year] += result

    unique_month_years = {}
    for site_name, site_data in aggregated_results.items():
        for stone_type_data in site_data.values():
            for month_year in stone_type_data.keys():
                if month_year not in unique_month_years:
                    unique_month_years[month_year] = set()
                unique_month_years[month_year].add(site_name)

    tmp_date_data = StoneEstimate.objects.filter(
        site__in=s_comp, created__year__gt = current_year
    ).annotate(
        month_year=TruncMonth('created')
    ).values('site', 'site__base_site_name', 'month_year').annotate(
        count=Count('id')
    ).order_by('site', 'month_year')

    produc_run_results = {}
    produc_work_results = {}
    produc_capacity_results = {}
    produc_hour_per_day_results = {}

    for tmp in tmp_date_data:
        month = tmp['month_year'].month
        year = tmp['month_year'].year

        produc = Production.objects.filter(site=tmp['site'], created__year=year, created__month=month).annotate(
            working_time=ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field=models.DurationField()),
            working_time_de=ExpressionWrapper(F('actual_time') - F('total_loss_time'), output_field=models.DecimalField())
        ).aggregate(
            sum_run=Sum("run_time"),
            total_working_time=Sum('working_time'),
            total_working_time_de=Sum('working_time_de')
        )

        crush = Weight.objects.filter(bws__weight_type=2, date__year=year, date__month=month, site=tmp['site']).order_by(
            'date').aggregate(
            s_weight=Sum("weight_total"),
            c_weight=Count('weight_total')
        )
        
        #capacity 
        try:
            capacity = crush['s_weight'] / (produc['total_working_time_de']/1000000/3600)
        except:
            capacity = Decimal(0)

        #hourPerDay 
        try:
            hourPerDay = produc['sum_run']/(produc['total_working_time']/24)
        except:
            hourPerDay = Decimal(0)

        update_results(produc_run_results, tmp['site__base_site_name'], tmp['month_year'], produc['sum_run'])
        update_results(produc_work_results, tmp['site__base_site_name'], tmp['month_year'], produc['total_working_time'])
        update_results(produc_capacity_results, tmp['site__base_site_name'], tmp['month_year'], capacity)
        update_results(produc_hour_per_day_results, tmp['site__base_site_name'], tmp['month_year'], hourPerDay)

    data_stone_old_year = strToArrList(active, 'weight')
    data_run_old_year = strToArrList(active, 'prod_run')
    data_work_old_year = strToArrList(active, 'prod_work')
    data_cap_old_year = strToArrList(active, 'prod_cap')
    data_hpd_old_year = strToArrList(active, 'prod_hpd')

    context = {'stone_name': stone_name,
               'aggregated_results':aggregated_results,
               'unique_month_years': unique_month_years,
               'produc_run_results': produc_run_results,
               'produc_work_results': produc_work_results,
               'produc_capacity_results': produc_capacity_results,
               'produc_hour_per_day_results': produc_hour_per_day_results,
               'sum_aggregated': sum_aggregated,
               'data_stone_old_year': data_stone_old_year,
               'data_run_old_year': data_run_old_year,
               'data_work_old_year': data_work_old_year,
               'data_cap_old_year': data_cap_old_year,
               'data_hpd_old_year': data_hpd_old_year,
               'current_year': current_year,
                active :"active",
              }
    return render(request, "production/monthlyProduction.html",context)

def strToArrList(active, field):
    try:
        queryset_string = SetWeightOY.objects.filter(comp__code = active).values_list(field)
        data = list(queryset_string[0])
        data_old_year = ast.literal_eval(data[0])
    except IndexError:
        data_old_year = None

    return data_old_year

def update_results(dictionary, key1, key2, value):
    if key1 not in dictionary:
        dictionary[key1] = {}
    if key2 not in dictionary[key1]:
        dictionary[key1][key2] = {}
    dictionary[key1][key2] = value

def getLossNameByMill(company_in, site, start_created, end_created, mode):
    list_loss = []
    pd_loss = ProductionLossItem.objects.filter(production__company__code__in = company_in, production__site = site, production__created__range=(start_created, end_created)).order_by('mc_type').values('production__site__base_site_id', 'mc_type__name').annotate(sum_time = Sum('loss_time'))
    pd_loss_all = ProductionLossItem.objects.filter(production__company__code__in = company_in, production__site = site, production__created__range=(start_created, end_created)).aggregate(s=Sum('loss_time'))["s"]
    for i in pd_loss:
        if mode == 1:
            list_loss.append(i['mc_type__name'])
        elif mode == 2:
            list_loss.append(calculatePersent(i['sum_time'], pd_loss_all))
    return list_loss

def calculatorDiffTime(request, start_time, end_time):
    difference = None
    if start_time is None:
        start_time = timedelta(hours=0, minutes=0) 
    if end_time is None:
        end_time = timedelta(hours=0, minutes=0)
    difference = end_time - start_time
    return difference

def calculatorDiffWorkRealTime(plan, uncontrol, loss):
    difference = None
    if plan is None:
        plan = timedelta(hours=0, minutes=0) 
    if uncontrol is None:
        uncontrol = timedelta(hours=0, minutes=0)
    if loss is None:
        loss = timedelta(hours=0, minutes=0)
    difference = plan - uncontrol - loss
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
    if 'site_id' in request.GET and 'line_type_id' in request.GET and 'created' in request.GET and 'pd_id' in request.GET and 'company' in request.GET:
        site_id = request.GET.get('site_id')
        line_type_id = request.GET.get('line_type_id')
        created =  request.GET.get('created')
        pd_id =  request.GET.get('pd_id')
        company =  request.GET.get('company')


        date_object = datetime.strptime(created, "%Y-%m-%d")

        #เอาออก line_type__id = line_type_id เพราะโรงโม่เดียวกันใช้เป้าผลิตเท่ากัน
        pd_goal = ProductionGoal.objects.filter(company__code = company, date__year = f'{date_object.year}' , date__month = f'{date_object.month}' , site = site_id).values('site', 'line_type', 'date' , 'accumulated_goal', 'id')
        #if pd_id == '' create mode , else edit mode
        if pd_id == '':
            have_production = Production.objects.filter(company__code = company, created = created, site = site_id, line_type__id = line_type_id ).exists()
        else:
            have_production = Production.objects.filter(~Q(id = pd_id), company__code = company, created = created, site = site_id, line_type__id = line_type_id ).exists()
        #ดึงข้อมูล line 1 มาเพื่อไป set default ใน line อื่นๆ
        pd_line1 = Production.objects.filter(company__code = company, created = created, site = site_id, line_type__id = 1).values('plan_start_time', 'plan_end_time')
        
        
    data = {
        'pd_goal_list': list(pd_goal),
        'have_production' :have_production,
        'pd_line1': list(pd_line1),
    }
    
    return JsonResponse(data)

def createProduction(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    base_loss_type = BaseLossType.objects.all()

    ProductionLossItemFormSet = modelformset_factory(ProductionLossItem, fields=('mc_type', 'loss_type', 'loss_time'), extra=1, widgets={'loss_time': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time'}),})
    if request.method == 'POST':
        pd_goal_form = ProductionGoalForm(request.POST)
        production_form = ProductionForm(request, request.POST or None, initial={'company': company})
        formset = ProductionLossItemFormSet(request.POST)
        if production_form.is_valid() and formset.is_valid() and pd_goal_form.is_valid():
            production = production_form.save()

            if pd_goal_form.cleaned_data['pk_goal']:
                pd_goal = ProductionGoal.objects.get(id = pd_goal_form.cleaned_data['pk_goal'])
                pd_goal.accumulated_goal = pd_goal_form.cleaned_data['accumulated_goal']
                pd_goal.company = production.company
                pd_goal.save()
            else:
                pd_goal = ProductionGoal.objects.create(accumulated_goal = pd_goal_form.cleaned_data['accumulated_goal'])
                pd_goal.site = production.site
                pd_goal.line_type = production.line_type
                pd_goal.date = production.created
                pd_goal.company = production.company
                pd_goal.save()

            production.pd_goal = pd_goal

            formset_instances = formset.save(commit=False)
            for instance in formset_instances:
                instance.production = production
                instance.save()

            #คำนวนเวลารวมในการสูญเสีย
            total_loss_time = ProductionLossItem.objects.filter(production = production).aggregate(s=Sum("loss_time"))["s"]
            production.total_loss_time = total_loss_time if total_loss_time else timedelta(hours=0, minutes=0)
            #คำนวนเวลารวมในการสูญเสีย uncontrol
            total_uncontrol_time = ProductionLossItem.objects.filter(production = production, mc_type = 7).aggregate(s=Sum("loss_time"))["s"]
            production.uncontrol_time = total_uncontrol_time if total_uncontrol_time else timedelta(hours=0, minutes=0)

            production.save()

            return redirect('viewProduction')
    else:
        production_form = ProductionForm(request, initial={'company': company})
        pd_goal_form = ProductionGoalForm(initial={'company': company})
        formset = ProductionLossItemFormSet(queryset=ProductionLossItem.objects.none())

    context = {'production_page':'active', 'pd_goal_form': pd_goal_form, 'form': production_form, 'formset': formset, active :"active", 'disabledTab' : 'disabled'}
    return render(request, "production/createProduction.html",context)

def editProduction(request, pd_id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    pd_data = Production.objects.get(id = pd_id)

    #หาบันทึกปฎิบัติการของวันนี้ เพื่อเช็คไม่ให้ save mill และ line ซ้ำกัน
    production_on_day = Production.objects.filter(~Q(id = pd_data.id), created = datetime.today()).values('site', 'line_type', 'created')

    if request.method == "POST":
        formset = ProductionLossItemInlineFormset(request.POST, request.FILES, instance=pd_data)
        form = ProductionForm(request, request.POST, request.FILES, instance=pd_data)
        pd_goal_form = ProductionGoalForm(request.POST, request.FILES, instance=pd_data.pd_goal)

        if form.is_valid() and formset.is_valid() and pd_goal_form.is_valid():
            # save production
            production = form.save()

            #หา id production Goal ใหม่
            find_pd_goal = ProductionGoal.objects.get(company__code = company, date__year = f'{production.created.year}', date__month = f'{production.created.month}', site = production.site)
            production.pd_goal = find_pd_goal

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
            #คำนวนเวลารวมในการสูญเสีย uncontrol
            total_uncontrol_time = ProductionLossItem.objects.filter(production = production, mc_type = 7).aggregate(s=Sum("loss_time"))["s"]
            production.uncontrol_time = total_uncontrol_time if total_uncontrol_time else timedelta(hours=0, minutes=0)

            production.save()

            #update เป้าผลิตสะสม production Goal ใหม่
            pd_goal = ProductionGoal.objects.get(id = find_pd_goal.id)
            pd_goal.accumulated_goal = pd_goal_form.cleaned_data['accumulated_goal']
            pd_goal.save()

            return redirect('viewProduction')
    else:
        formset = ProductionLossItemInlineFormset(instance=pd_data)
        form = ProductionForm(request, instance=pd_data)
        pd_goal_form = ProductionGoalForm(instance=pd_data.pd_goal)

    context = {'production_page':'active', 'pd_goal_form': pd_goal_form, 'form': form, 'formset': formset, 'pd': pd_data, 'production_on_day': production_on_day, active :"active", 'disabledTab' : 'disabled'}
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

def calculatCapacityPerHour(request, data_sum_produc, wk_time):
    result = Decimal('0.0')
    if data_sum_produc and wk_time:
        result = data_sum_produc/(wk_time/1000000/3600)
    return result

def formatHourMinute(time):
    result = None
    if time:
       #result = (datetime.min + time).strftime("%H:%M") or None
       result = f'{time}'[:-3]
    return result

def excelProductionAndLoss(request, my_q, sc_q):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    pd_sites = Production.objects.filter(my_q).values_list('site', flat=True).distinct()
    sites = BaseSite.objects.filter(base_site_id__in = pd_sites)

    workbook = openpyxl.Workbook()
    if sites:
        for site in sites:
            count_loss = ProductionLossItem.objects.filter(sc_q, production__site = site).order_by('mc_type__id', 'loss_type__id').values('production__site__base_site_id', 'mc_type__name', 'loss_type__name').annotate(sum_time = Sum('loss_time'))

            sheet = workbook.create_sheet(title=site.base_site_name)

            # Fetch distinct line types for the current mill
            line_types = Production.objects.filter(my_q, site=site).values_list('line_type', flat=True).distinct()

            line_type =  BaseLineType.objects.filter(id__in=line_types)

            # Create a list of colors for each line_type
            line_type_colors = [generate_pastel_color() for i  in range(len(line_type) + 1)]

            column_index = 2
            for line in line_type:
                sheet.cell(row=1, column = column_index, value = line.name)
                sheet.merge_cells(start_row=1, start_column = column_index, end_row=1, end_column= (column_index + len(count_loss) + 17) -1 )
                sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')
                column_index += len(count_loss) + 17

            headers2 = ['Date']
            for i in  range(len(line_type)):
                headers2.extend(['เป้าต่อวัน','เป้าสะสม(ตัน)', 'ชั่วโมงตามแผน', 'ชั่วโมงตามแผน', 'ชั่วโมงทำงาน','ชั่วโมงกำหนดจริง', 'ชั่วโมงกำหนดจริง', 'ชั่วโมงกำหนดจริง', 'ชั่วโมงเดินเครื่อง', 'ชั่วโมงเดินเครื่อง', 'ชั่วโมงเดินเครื่อง'])
                headers2.extend([cl['mc_type__name'] for cl in count_loss])
                headers2.extend(['รวม','ชั่วโมงการทำงานจริง', 'ยอดผลิต (ตัน)','ยอดผลิตสะสม','กำลังการผลิต (ตัน/ชั่วโมง)','หมายเหตุ',])

            sheet.append(headers2)

            merge_cells_num = 0
            headers3 = ['Date']
            for i in  range(len(line_type)):
                headers3.extend(['เป้าต่อวัน','เป้าสะสม(ตัน)', '(เริ่ม)', '(สิ้นสุด)', 'ชั่วโมงทำงาน', '(เริ่ม)', '(สิ้นสุด)', 'ชั่วโมงกำหนดจริง', '(เริ่ม)', '(สิ้นสุด)', 'ชั่วโมงเดินเครื่อง'])
                headers3.extend([cl['loss_type__name'] for cl in count_loss])
                headers3.extend(['รวมเวลา','ชั่วโมงการทำงานจริง', 'ยอดผลิต (ตัน)','ยอดผลิตสะสม','กำลังการผลิต (ตัน/ชั่วโมง)','หมายเหตุ',])
                # merge_cells headers เป้าต่อวัน, เป้าสะสม(ตัน),ชั่วโมงทำงาน,ชั่วโมงเดินเครื่อง
                sheet.merge_cells(start_row=2, start_column = 2 + merge_cells_num , end_row=3, end_column = 2 + merge_cells_num)
                sheet.merge_cells(start_row=2, start_column = 3 + merge_cells_num , end_row=3, end_column = 3 + merge_cells_num)
                sheet.merge_cells(start_row=2, start_column = 6 + merge_cells_num , end_row=3, end_column = 6 + merge_cells_num)
                sheet.merge_cells(start_row=2, start_column = 9 + merge_cells_num , end_row=3, end_column = 9 + merge_cells_num)
                sheet.merge_cells(start_row=2, start_column = 12 + merge_cells_num , end_row=3, end_column = 12 + merge_cells_num)

                #ช่องหลังจาก loos_item
                sheet.merge_cells(start_row=2, start_column = 13 + merge_cells_num + len(count_loss) , end_row=3, end_column = 13 + merge_cells_num + len(count_loss))
                sheet.merge_cells(start_row=2, start_column = 14 + merge_cells_num + len(count_loss) , end_row=3, end_column = 14 + merge_cells_num + len(count_loss))
                sheet.merge_cells(start_row=2, start_column = 15 + merge_cells_num + len(count_loss) , end_row=3, end_column = 15 + merge_cells_num + len(count_loss))            
                sheet.merge_cells(start_row=2, start_column = 16 + merge_cells_num + len(count_loss) , end_row=3, end_column = 16 + merge_cells_num + len(count_loss))
                sheet.merge_cells(start_row=2, start_column = 17 + merge_cells_num + len(count_loss) , end_row=3, end_column = 17 + merge_cells_num + len(count_loss))
                sheet.merge_cells(start_row=2, start_column = 18 + merge_cells_num + len(count_loss) , end_row=3, end_column = 18 + merge_cells_num + len(count_loss))     

                # merge_cells headers loos_type
                sheet.merge_cells(start_row = 2, start_column = 4 + merge_cells_num , end_row = 2, end_column = 5 + merge_cells_num)
                sheet.merge_cells(start_row = 2, start_column = 7 + merge_cells_num , end_row = 2, end_column = 8 + merge_cells_num)
                sheet.merge_cells(start_row = 2, start_column = 10 + merge_cells_num , end_row = 2, end_column = 11 + merge_cells_num)
                #sheet.merge_cells(start_row = 2, start_column = 13 + merge_cells_num , end_row = 2, end_column = 12 + merge_cells_num + len(count_loss))
                
                merge_cells_num += len(count_loss) + 17


            sheet.cell(row=1, column = 1, value = 'วัน/เดือน/ปี')
            sheet.merge_cells(start_row=1, start_column = 1, end_row=3, end_column=1)
            sheet.append(headers3)

            # Fetch distinct 'created' dates for the current mill
            created_dates = Production.objects.filter(my_q, site=site).values_list('created', flat=True).order_by('created').distinct()

            for created_date in created_dates:
                row = [created_date]
                row_sum = ['']
                row_persent_loss = ['']
                row_persent_accumulated_produc = ['']
                sum_capacity_per_hour = Decimal('0.0')
                
                date_from_accumulated = startDateInMonth(created_date)

                for line_type in BaseLineType.objects.filter(id__in=line_types):
                    production = Production.objects.filter(site = site, line_type = line_type, created = created_date).first()
                    accumulated_goal = Production.objects.filter(site = site, line_type = line_type, created__range=(date_from_accumulated, created_date)).aggregate(s=Sum("goal"))["s"]

                    data_sum_produc = Weight.objects.filter(site=site, date = created_date, bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]
                    wk_time = Production.objects.filter(site=site, line_type = line_type, created = created_date).annotate(working_time_de = ExpressionWrapper(F('actual_time') - F('total_loss_time') , output_field= models.DecimalField())).aggregate(total_working_time=Sum('working_time_de'))['total_working_time']

                    accumulated_produc = Weight.objects.filter(site=site ,date__range=(date_from_accumulated, created_date) , bws__weight_type = 2).aggregate(s=Sum("weight_total"))["s"]

                    #3) sum_by_mill = Production.objects.filter(my_q, site=site, line_type = line_type).distinct().aggregate(Sum('plan_time'),Sum('run_time'),Sum('total_loss_time'))
                    #4) cal_by_mill = Production.objects.filter(my_q, site=site, line_type = line_type).distinct().annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']

                    capacity_per_hour = calculatCapacityPerHour(request, data_sum_produc, wk_time)
                    if production:
                        row.extend([production.goal, accumulated_goal , formatHourMinute(production.plan_start_time), formatHourMinute(production.plan_end_time), formatHourMinute(production.plan_time), formatHourMinute(production.actual_start_time), formatHourMinute(production.actual_end_time) , formatHourMinute(production.actual_time), formatHourMinute(production.run_start_time) if production.run_start_time else production.mile_run_start_time  , formatHourMinute(production.run_end_time) if production.run_end_time else production.mile_run_end_time, formatHourMinute(production.run_time)])
                    else:
                        row.extend(['' for i in range(17)])

                    if  count_loss:
                        for i in range(len(count_loss)):
                            tmp_mc = sheet.cell(row=2, column = i+13).value
                            tmp_loss = sheet.cell(row=3, column = i+13).value
                            lss = ProductionLossItem.objects.filter(production = production, mc_type__name = tmp_mc, loss_type__name = tmp_loss).aggregate(s=Sum('loss_time'))['s']
                            row.extend([formatHourMinute(lss)])
                    else:
                        row.extend(['' for i in range(len(count_loss))])

                    #รวม, ชั่วโมงการทำงานจริง, ยอดผลิต (ตัน), ยอดผลิตสะสม, กำลังการผลิต (ตัน/ชั่วโมง), หมายเหตุ
                    if  production:
                        row.extend([formatHourMinute(production.total_loss_time), formatHourMinute(calculatorDiffWorkRealTime(production.plan_time, production.uncontrol_time, production.total_loss_time)), data_sum_produc, accumulated_produc, capacity_per_hour, production.note,])
                        sum_capacity_per_hour += capacity_per_hour

                    ''' 1) ล่างสุดตัวหนังสือสีแดง sum ทั้งหมด
                    row_sum.extend([len(created_dates), '' , '', 'ชั่วโมงทำงานรวม', formatHourMinute(sum_by_mill['plan_time__sum']), '', '', formatHourMinute(sum_by_mill['run_time__sum'])])
                    row_sum.extend(['eiei'+formatHourMinute(pd_loos_item['sum_loss_time']) for pd_loos_item in ProductionLossItem.objects.filter(production__site=site, production__line_type = line_type).order_by('mc_type__id', 'loss_type__id').values('loss_type__id').annotate(sum_loss_time=Coalesce(Sum('loss_time'), None))])

                    row_sum.extend([formatHourMinute(sum_by_mill['total_loss_time__sum']), formatHourMinute(cal_by_mill), 'diff จากเป้า' , calculatorDiff(request, accumulated_goal , accumulated_produc) , sum_capacity_per_hour/len(created_dates),''])

                    loss_items = ProductionLossItem.objects.filter(
                        production__site=site,
                        production__line_type=line_type
                    ).order_by('loss_type__id').values('loss_type__id').annotate(
                        sum_loss_time=Coalesce(Sum('loss_time'), None)
                    )

                    row_persent_accumulated_produc.extend(['', '' , '', '', '', '', '', ''])
                    row_persent_accumulated_produc.extend(['C' for i in range(len(count_loss))])
                    row_persent_accumulated_produc.extend(['', '', '' , str(round(calculatorDiff(request, accumulated_goal , accumulated_produc) / accumulated_goal, 2)) + "%" if accumulated_goal and accumulated_produc else None , '',''])

                    row_persent_loss.extend(['', '' , '', '', '', '', '% ชม.สูญเสีย ต่อ ชม.ทำงานจริง', ''])
                    row_persent_loss.extend([str(round(pd_loos_item['sum_loss_time'] / sum_by_mill['total_loss_time__sum'] * 100, 2)) + "%" if pd_loos_item['sum_loss_time'] else None for pd_loos_item in loss_items])
                    row_persent_loss.extend(['100%', '', '' , '' , '',''])                
                    '''


                sheet.append(row)

            if len(created_dates) > 0:
                sheet.append(row_sum)
                sheet.append(row_persent_accumulated_produc)
                sheet.append(row_persent_loss)
                # 2) ล่างสุดตัวหนังสือสีแดง sum ทั้งหมด sheet.cell(row = len(created_dates) + 4, column = 1, value = f'จำนวนวันทำงาน' )        

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
                column_index += len(count_loss) + 17

            for row in sheet.iter_rows(min_row=1, max_row=3):
                # Set the background color for each cell in the column
                for cell in row:
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center')
                    line_index = (cell.column - 2) // (len(count_loss) + 17)
                    fill_color = line_type_colors[line_index % len(line_type_colors)]
                    fill = PatternFill(start_color=fill_color, fill_type="solid")
                    cell.fill = fill

            #1) merge_cells loos header mc_type
            num_loss = 0
            for col_index in range(12, sheet.max_column):
                if sheet.cell(row=2, column=col_index).value == sheet.cell(row=2, column=col_index + 1).value:
                    num_loss += 1
                else:
                    sheet.merge_cells(start_row=2, start_column=col_index - num_loss, end_row=2, end_column=col_index)
                    num_loss = 0

        workbook.remove(workbook['Sheet'])
    else:
        worksheet = workbook.active
        worksheet.cell(row = 1, column = 1, value = f'ไม่มีข้อมูลบันทึกปฎิบัติการโรงโม่ดือนนี้')


    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="production_record_({active}).xlsx"'

    workbook.save(response)
    return response

def exportExcelProductionAndLoss(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    start_created = request.GET.get('start_created') or None
    end_created = request.GET.get('end_created') or None
    site = request.GET.get('site') or None

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    if site is not None:
        my_q &=Q(site = site)
    my_q &=Q(company__code__in = company_in)

    sc_q = Q()
    if start_created is not None:
        sc_q &= Q(production__created__gte = start_created)
    if end_created is not None:
        sc_q &=Q(production__created__lte = end_created)
    sc_q &=Q(production__company__code__in = company_in)
    
    response = excelProductionAndLoss(request, my_q, sc_q)
    return response

def exportExcelProductionAndLossDashboard(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    '''แบบเก่าดึง บันทึกปฏิบัติการงานโรงโม่ ตามเดือนนั้นๆ 09/05/2024
    #ดึงรายงานของเดือนนั้นๆ
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)


    end_created = previous_date_time.strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)
    '''
    end_created = request.session['db_end_date']
    start_created = request.session['db_start_date']

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    my_q &=Q(company__code__in = company_in)

    sc_q = Q()
    if start_created is not None:
        sc_q &= Q(production__created__gte = start_created)
    if end_created is not None:
        sc_q &=Q(production__created__lte = end_created)
    sc_q &=Q(production__company__code__in = company_in)
    
    response = excelProductionAndLoss(request, my_q, sc_q)
    return response

@login_required(login_url='login')
def viewStoneEstimate(request):
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = StoneEstimate.objects.filter(company__code__in = company_in).order_by('-created', 'site')

    #กรองข้อมูล
    myFilter = StoneEstimateFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    stone_estimate = p.get_page(page)

    context = {'stone_estimate_page':'active', 'stone_estimate': stone_estimate,'filter':myFilter, active :"active",}
    return render(request, "stoneEstimate/viewStoneEstimate.html",context)

def createStoneEstimate(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    base_stone_type = BaseStoneType.objects.filter(is_stone_estimate = True)
    StoneEstimateItemFormSet = modelformset_factory(StoneEstimateItem, fields=('stone_type', 'percent'), extra=len(base_stone_type), widgets={})
    if request.method == 'POST':
        se_form = StoneEstimateForm(request, request.POST)
        formset = StoneEstimateItemFormSet(request.POST)
        if se_form.is_valid() and formset.is_valid():
            se = se_form.save()

            formset_instances = formset.save(commit=False)
            for instance in formset_instances:
                instance.se = se
                instance.save()
            return redirect('viewStoneEstimate')
    else:
        se_form = StoneEstimateForm(request, initial={'company': company})
        formset = StoneEstimateItemFormSet(queryset=StoneEstimateItem.objects.none())

    context = {'stone_estimate_page':'active', 'se_form': se_form, 'formset' : formset, 'base_stone_type': base_stone_type, active :"active", 'disabledTab' : 'disabled'}
    return render(request, "stoneEstimate/createStoneEstimate.html",context)

def editStoneEstimate(request, se_id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    se_data = StoneEstimate.objects.get(id = se_id)

    if request.method == "POST":
        formset = StoneEstimateItemInlineFormset(request.POST, request.FILES, instance=se_data)
        se_form = StoneEstimateForm(request, request.POST, request.FILES, instance=se_data)
        if se_form.is_valid() and formset.is_valid():
            # save StoneEstimate
            se = se_form.save()

            # save StoneEstimateItem
            instances = formset.save(commit=False)
            for instance in instances:
                #ให้ save ถ้ามีชนิดหิน
                if instance.stone_type:
                    instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()

            return redirect('viewStoneEstimate')
    else:
        formset = StoneEstimateItemInlineFormset(instance=se_data)
        se_form = StoneEstimateForm(request, instance=se_data)

    context = {'stone_estimate_page':'active', 'se_form': se_form, 'formset' : formset,'se': se_data, active :"active", 'disabledTab' : 'disabled'}
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
    if 'site_id' in request.GET and 'created' in request.GET and 'se_id' in request.GET and 'company' in request.GET:
        site_id = request.GET.get('site_id')
        created =  request.GET.get('created')
        se_id =  request.GET.get('se_id')
        company =  request.GET.get('company')

        #if se_id == '' create mode , else edit mode
        if se_id == '':
            have_estimate = StoneEstimate.objects.filter(company__code = company, created = created, site = site_id).exists()
        else:
            have_estimate = StoneEstimate.objects.filter(~Q(id = se_id),company__code = company, created = created, site = site_id).exists()
        #ดึงเปอร์เซ็นคำนวนหินเปอร์ที่คีย์ไปล่าสุด
        last_se = StoneEstimate.objects.filter(company__code = company, site = site_id).order_by('-created').first()
        last_se_item = StoneEstimateItem.objects.filter(se = last_se).values('stone_type', 'percent')
        
    data = {
        'have_estimate' :have_estimate,
        'last_se_item': list(last_se_item),
    }
    
    return JsonResponse(data)

def calculateEstimate(percent, sum_all):
    result = Decimal(0.0)
    if percent and sum_all:
        result = Decimal(sum_all) * Decimal(percent)/100
    return result

def calculateEstimateToString(percent, sum_all):
    #result = Decimal(0.0) ลดการปริ้น 0
    result = None
    if percent and sum_all:
        result = Decimal(sum_all) * Decimal(percent)/100
        result = f"{result:.2f}"
    return result

def calculateSumEstimateToString(stone_type, site, customer_name, list_date, time_in, time_out):
    result = Decimal(0)
    tmp = Decimal(0)

    for ld in list_date:
        try:
            percent = StoneEstimateItem.objects.get(se__created = ld, se__site = site, stone_type = stone_type).percent
        except:
            percent = None
        sum_all = Weight.objects.filter( Q(time_out__gte=time_in) & Q(time_out__lte=time_out) , bws__weight_type = 2 , date = ld, customer_name = customer_name, site = site).aggregate(s_weight = Sum("weight_total"))['s_weight']
        
        if percent and sum_all:
            tmp = Decimal(sum_all) * Decimal(percent)/100
            result = result + tmp
    return f"{result:.2f}" if result != 0.00 else None

def exportExcelStoneEstimateAndProduction(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    start_created = request.GET.get('start_created') or None
    end_created = request.GET.get('end_created') or None

    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    tmp_end_created = previous_date_time.strftime('%Y-%m-%d')
    tmp_start_created = startDateInMonth(tmp_end_created)

    if start_created is None:
        start_created = tmp_start_created
    if end_created is None:
        end_created = tmp_end_created

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    my_q &=Q(company__code__in = company_in)

    sc_q = Q()
    if start_created is not None:
        sc_q &= Q(date__gte = start_created)
    if end_created is not None:
        sc_q &=Q(date__lte = end_created)
    sc_q &=Q(bws__company__code__in = company_in)
    
    response = excelStoneEstimateAndProduction(request, my_q, sc_q)
    return response

def exportExcelStoneEstimateAndProductionDashboard(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    ''' แบบเก่าดึง รายงานการผลิตหิน ตามเดือนนั้นๆ 09/05/2024
    #ดึงรายงานของเดือนนั้นๆ
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    end_created = previous_date_time.strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)
    '''
    
    end_created = request.session['db_end_date']
    start_created = request.session['db_start_date']

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    my_q &=Q(company__code__in = company_in)

    sc_q = Q()
    if start_created is not None:
        sc_q &= Q(date__gte = start_created)
    if end_created is not None:
        sc_q &=Q(date__lte = end_created)
    sc_q &=Q(bws__company__code__in = company_in)
    
    response = excelStoneEstimateAndProduction(request, my_q, sc_q)
    return response


def excelStoneEstimateAndProduction(request, my_q, sc_q):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    date_style = NamedStyle(name='custom_datetime', number_format='DD/MM/YYYY')

    se_site = StoneEstimate.objects.filter(my_q).values_list('site',flat=True).distinct()
    sites = BaseSite.objects.filter(base_site_id__in = se_site)

    se_id = StoneEstimate.objects.filter(my_q).values_list('id',flat=True).distinct()
    #ดึงเฉพาะชนิดหิน estimate
    base_stone_type = StoneEstimateItem.objects.select_related('stone_type').filter(se__in = se_id).order_by('stone_type').values_list('stone_type__base_stone_type_name', flat=True).distinct()

    #list_customer_name = ['สมัย','วีระวุฒิ','NCK']
    #เปลี่ยนการตั้งค่า 13-02-2024 list_customer_name = BaseCustomer.objects.filter(is_stone_estimate = True).values_list('customer_name', flat=True)
    list_customer_name = BaseSEC.objects.filter(company__code__in = company_in).values_list('customer__customer_name', flat=True)

    workbook = openpyxl.Workbook()
    if sites:
        for site in sites:
            sheet = workbook.create_sheet(title=site.base_site_name)

            list_time = BaseTimeEstimate.objects.filter(site = site).values('time_from', 'time_to', 'time_name')
            #ดึงชนิดหินที่มีคำว่าเข้าโม่
            mill_type = Weight.objects.filter(sc_q, bws__weight_type = 2, site = site).order_by('mill_name').values_list('mill_name', flat=True).distinct()

            tmp_stock_name = "กองสต็อค" + site.base_site_name
            try:
                stock_type = BaseSite.objects.get(base_site_name = tmp_stock_name)
                stock_type_name = stock_type.base_site_name
            except:
                stock_type_name = "ไม่มีกองสต็อค"

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
            for mt in mill_type:
                sheet.cell(row=1, column = column_index, value = mt)
                sheet.merge_cells(start_row=1, start_column = column_index, end_row=1, end_column= (column_index + 2) -1 )
                sheet.cell(row=1, column=column_index).alignment = Alignment(horizontal='center')
                column_index += 2

            sheet.cell(row=1, column = column_index, value = stock_type_name)
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
            for i in range(len(mill_type) + 1):
                headers2.extend(['เที่ยว','ตัน',])

            headers2.extend(['เที่ยว','ตัน',])

            headers2.extend(['AAA'])
            headers2.extend([i for i in base_stone_type])
            headers2.extend(['หินเข้าโม่รวม(ตัน)', 'ผลิตตัน/ชม.', 'หมายเหตุ'])

            sheet.cell(row=1, column = 1, value = 'วัน/เดือน/ปี')
            #merge_cells วัน/เดือน/ปี
            sheet.merge_cells(start_row=1, start_column = 1, end_row=2, end_column=1)
            sheet.append(headers2)

            # Fetch distinct 'created' dates for the current site
            created_dates = StoneEstimate.objects.filter(my_q, site = site).values_list('created', flat=True).order_by('created').distinct()

            row_index = 3
            for created_date in created_dates:
                len_row_index = 0
                total_working_time = None
                production_note = None
                for i in range(len(list_customer_name)):
                    for j, time in enumerate(list_time):
                        len_row_index +=1

                        #ชั่วโมงทำงาน
                        total_working_time = Production.objects.filter(created = created_date, site = site).distinct().annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']
                        #หมายเหตุ
                        production_note = Production.objects.filter(site = site, created = created_date).values_list('note', flat=True).first()
                        #หินเขา
                        mountain1  = Weight.objects.filter(Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), Q(mill = '001MA') | Q(mill = '002MA'), Q(site = site) | Q(site__base_site_name = stock_type_name), bws__weight_type = 2, date = created_date, customer_name = list_customer_name[i]).aggregate(s_weight = Sum("weight_total"))

                        #หินเข้าโม่ทั้งหมด
                        crush1 = Weight.objects.filter(Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), bws__weight_type = 2 , date = created_date, customer_name = list_customer_name[i], site = site).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))

                        #กองสต็อกตามโรงโม่
                        stock1 = Weight.objects.filter(Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), bws__weight_type = 2 , date = created_date, customer_name = list_customer_name[i], site__base_site_name = stock_type_name).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))

                        #สร้างแถว 1
                        row1 = [created_date, list_customer_name[i], str(time['time_name']), formatHourMinute(total_working_time), mountain1['s_weight']]

                        for mill in mill_type:

                            weight_time1 = Weight.objects.filter(Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), bws__weight_type = 2, mill_name = mill, site = site, date = created_date, customer_name = list_customer_name[i]).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))
                            if weight_time1:
                                row1.extend([weight_time1['c_weight'], weight_time1['s_weight']])
                            else:
                                row1.extend(['' for i in range(3)])

                        row1.extend([stock1['c_weight'], stock1['s_weight']])
                        row1.extend([crush1['c_weight'], crush1['s_weight']])
                        row1.extend(['1'])
                        row1.extend([calculateEstimateToString(se_item, crush1['s_weight']) for se_item in StoneEstimateItem.objects.filter(se__created = created_date, se__site = site).order_by('stone_type').values_list('percent', flat=True)])
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
                    (h, m) = str(format_duration(total_working_time)).split(':')
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

            # Total last
            len_row_index_total = 0
            for i in range(len(list_customer_name)):

                for j, time in enumerate(list_time):
                    len_row_index_total += 1

                    #ชั่วโมงทำงาน
                    total_working_time_tt = Production.objects.filter(my_q, site = site).distinct().annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']

                    #หินเขา
                    mountain_tt  = Weight.objects.filter(sc_q, Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), Q(mill = '001MA') | Q(mill = '002MA'), Q(site = site) | Q(site__base_site_name = stock_type_name), bws__weight_type = 2, customer_name = list_customer_name[i]).aggregate(s_weight = Sum("weight_total"))

                    #หินเข้าโม่ทั้งหมด
                    crush_tt = Weight.objects.filter(sc_q, Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), bws__weight_type = 2, customer_name = list_customer_name[i], site = site).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))

                    #กองสต็อกตามโรงโม่
                    stock_tt = Weight.objects.filter(sc_q, Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), bws__weight_type = 2, customer_name = list_customer_name[i], site__base_site_name = stock_type_name).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))
                    
                    #สร้างแถว
                    row_tt = ["รวม", list_customer_name[i], str(time['time_name']), formatHourMinute(total_working_time_tt), mountain_tt['s_weight']]

                    for mill in mill_type:

                        weight_time_tt = Weight.objects.filter(sc_q, Q(time_out__gte=time['time_from']) & Q(time_out__lte=time['time_to']), bws__weight_type = 2, mill_name = mill, site = site, customer_name = list_customer_name[i]).aggregate(s_weight = Sum("weight_total"), c_weight=Count('weight_total'))
                        if weight_time_tt:
                            row_tt.extend([weight_time_tt['c_weight'], weight_time_tt['s_weight']])
                        else:
                            row_tt.extend(['' for i in range(3)])

                    row_tt.extend([stock_tt['c_weight'], stock_tt['s_weight']])
                    row_tt.extend([crush_tt['c_weight'], crush_tt['s_weight']])
                    row_tt.extend(['1'])
                    row_tt.extend([calculateSumEstimateToString(stone_type , site, list_customer_name[i], created_dates, time['time_from'], time['time_to']) for stone_type in StoneEstimateItem.objects.filter(se__created = created_date, se__site = site).order_by('stone_type').values_list('stone_type', flat=True)])
                    row_tt.extend([crush_tt['s_weight']])
                    sheet.append(row_tt)

                #merge_cells พนักงาน
                sheet.merge_cells(start_row = row_index + len_row_index_total -2 , start_column = 2, end_row = row_index + len_row_index_total -1, end_column=2)

            #merge_cells วันที่, ชม.ทำงาน
            sheet.merge_cells(start_row = row_index, start_column = 1, end_row = (row_index + len_row_index_total -1), end_column=1)
            sheet.merge_cells(start_row = row_index, start_column = 4, end_row = (row_index + len_row_index_total -1), end_column=4)
            sheet.merge_cells(start_row = row_index, start_column = column_index+1, end_row = (row_index + len_row_index_total -1), end_column=column_index+1)
            sheet.merge_cells(start_row = row_index, start_column = column_index+2, end_row = (row_index + len_row_index_total -1), end_column=column_index+2)


            # Set background color for the merged cells
            fill = PatternFill(start_color='F5CBA7', end_color='F5CBA7', fill_type='solid')  # Replace 'FF0000' with your desired color code
            sheet.cell(row = row_index + len_row_index_total, column=1, value='รวมทั้งหมด').fill = fill
            sheet.merge_cells(start_row = row_index + len_row_index_total, start_column = 1, end_row = row_index + len_row_index_total, end_column=4)

            sum_by_col_tt = Decimal('0.00')
            for col in range(5, column_index):
                for row in range(row_index, len_row_index_total + row_index):
                    sum_by_col_tt = sum_by_col_tt + Decimal( sheet.cell(row=row, column=col).value or '0.00' )
                sheet.cell(row=row_index + len_row_index_total, column=col, value=sum_by_col_tt).number_format = '#,##0.00'
                sheet.cell(row=row_index + len_row_index_total, column=col).font = Font(bold=True)
                sum_by_col_tt = Decimal('0.00')
            row_index +=  len_row_index_total + 1

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

                    column_crush = len(mill_type) * 2 + 8
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
    else:
        worksheet = workbook.active
        worksheet.cell(row = 1, column = 1, value = f'ไม่มีข้อมูลรายงานการผลิตหินดือนนี้')

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Prod_daily_({active}).xlsx"'

    workbook.save(response)
    return response

################### BaesMill ####################
@login_required(login_url='login')
def settingBaseMill(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseMill.objects.all().order_by('-mill_id')

    #กรองข้อมูล
    myFilter = BaseMillFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_mill = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_mill_page': 'active', 'base_mill': base_mill,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/baseMill.html",context)


def createBaseMill(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    form = BaseMillForm(request.POST or None, initial={'mill_id': generateCodeId('BaseMill', 1, None, None), 'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseMill.objects.filter(mill_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_mill_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

def editBaseMill(request, id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    obj = get_object_or_404(BaseMill, mill_id = id)
 
    form = BaseMillForm(request.POST or None, instance = obj)
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
        'id_name' : '#id_mill_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

################### BaseJobType ####################
@login_required(login_url='login')
def settingBaseJobType(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseJobType.objects.all().order_by('base_job_type_id')

    #กรองข้อมูล
    myFilter = BaseJobTypeFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_job_type = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_job_type_page': 'active', 'base_job_type': base_job_type,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/baseJobType.html",context)

def createBaseJobType(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    form = BaseJobTypeForm(request.POST or None, initial={'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseJobType.objects.filter(base_job_type_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_base_job_type_id',
        'mode' : 0,
        active :"active",
    }
    return render(request, "manage/formBase.html", context)

def editBaseJobType(request, id):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    obj = get_object_or_404(BaseJobType, base_job_type_id = id)
 
    form = BaseJobTypeForm(request.POST or None, instance = obj)
    if form.is_valid():
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
        'text_mode' : 'เปลี่ยน',
        'id_name' : '#id_base_job_type_id',
        'mode' : 1,
        active :"active",
    }
 
    return render(request, "manage/formBase.html", context)

################### BaesStoneType ####################
@login_required(login_url='login')
def settingBaseStoneType(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseStoneType.objects.all().order_by('-base_stone_type_id')

    #กรองข้อมูล
    myFilter = BaseStoneTypeFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_stone_type = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_stone_type_page': 'active', 'base_stone_type': base_stone_type,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/baseStoneType.html",context)

def createBaseStoneType(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    form = BaseStoneTypeForm(request.POST or None, initial={'base_stone_type_id': generateCodeId('BaseStoneType', 1, None, None), 'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseStoneType.objects.filter(base_stone_type_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_base_stone_type_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

def editBaseStoneType(request, id):
    active = request.session['company_code']
    company_in = findCompanyIn(request)            

    obj = get_object_or_404(BaseStoneType, base_stone_type_id = id)
 
    form = BaseStoneTypeForm(request.POST or None, instance = obj)
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
        'id_name' : '#id_base_stone_type_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

################### BaesScoop ####################
@login_required(login_url='login')
def settingBaseScoop(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseScoop.objects.all().order_by('-scoop_id')

    #กรองข้อมูล
    myFilter = BaseScoopFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_scoop = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_scoop_page': 'active', 'base_scoop': base_scoop,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/baseScoop.html",context)

def createBaseScoop(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)
        
    form = BaseScoopForm(request.POST or None, initial={'scoop_id': generateCodeId('BaseScoop', 1, None, None), 'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseScoop.objects.filter(scoop_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_scoop_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

def editBaseScoop(request, id):
    active = request.session['company_code']
    company_in = findCompanyIn(request) 
            
    obj = get_object_or_404(BaseScoop, scoop_id = id)
 
    form = BaseScoopForm(request.POST or None, instance = obj)
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
        'id_name' : '#id_scoop_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

################### BaseCarTeam ####################
@login_required(login_url='login')
def settingBaseCarTeam(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseCarTeam.objects.all().order_by('-car_team_id')

    #กรองข้อมูล
    myFilter = BaseCarTeamFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_car_team = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_car_team_page': 'active', 'base_car_team': base_car_team,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/baseCarTeam.html",context)

def createBaseCarTeam(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    form = BaseCarTeamForm(request.POST or None, initial={'car_team_id': generateCodeId('BaseCarTeam', 2, None, None), 'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseCarTeam.objects.filter(car_team_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_car_team_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

def editBaseCarTeam(request, id):
    active = request.session['company_code']
    company_in = findCompanyIn(request) 

    obj = get_object_or_404(BaseCarTeam, car_team_id = id)
 
    form = BaseCarTeamForm(request.POST or None, instance = obj)
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
        'id_name' : '#id_car_team_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

################### BaseCar ####################
@login_required(login_url='login')
def settingBaseCar(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseCar.objects.all().order_by('-car_id')

    #กรองข้อมูล
    myFilter = BaseCarFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_car = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_car_page': 'active', 'base_car': base_car,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/BaseCar/baseCar.html",context)

def createBaseCar(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    form = BaseCarForm(request.POST or None, initial={'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseCar.objects.filter(car_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseCar')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_page': 'active',
        'table_name' : 'รถร่วม',
        'text_mode' : 'เพิ่ม',
        'id_name' : '#id_car_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/BaseCar/formBaseCar.html", context)

def editBaseCar(request, id):
    active = request.session['company_code']
    company_in = findCompanyIn(request)         

    obj = get_object_or_404(BaseCar, car_id = id)
 
    form = BaseCarForm(request.POST or None, instance = obj)
    if form.is_valid():
        try:
            car_form = form.save()

            '''
            # update weight ด้วย
            weights = Weight.objects.filter(scoop_id = scoop_form.pk)
            weights.update(scoop_name = scoop_form.scoop_name)         
            '''
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseCar')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_page': 'active',
        'table_name' : 'รถร่วม',
        'text_mode' : 'เปลี่ยน',
        'id_name' : '#id_car_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/BaseCar/formBaseCar.html", context)

################### BaesSite ####################
@login_required(login_url='login')
def settingBaseSite(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseSite.objects.all().order_by('-base_site_id')

    #กรองข้อมูล
    myFilter = BaseSiteFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_site = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_site_page': 'active', 'base_site': base_site,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/BaseSite/baseSite.html",context)

def createBaseSite(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    form = BaseSiteForm(request.POST or None, initial={'base_site_id': generateCodeId('BaseSite', 1, None, None), 'user_created': request.user})
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseSite.objects.filter(base_site_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_base_site_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/BaseSite/formBaseSite.html", context)

def editBaseSite(request, id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    obj = get_object_or_404(BaseSite, base_site_id = id)
 
    form = BaseSiteForm(request.POST or None, instance = obj)
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
        'id_name' : '#id_base_site_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/BaseSite/formBaseSite.html", context)

################### BaesCustomer ####################
@login_required(login_url='login')
def settingBaseCustomer(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseCustomer.objects.filter(is_disable = False).order_by('-weight_type_id','-customer_id')

    #กรองข้อมูล
    myFilter = BaseCustomerFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_customer = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_customer_page': 'active', 'base_customer': base_customer,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/BaseCustomer/baseCustomer.html",context)

def createBaseCustomer(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    form = BaseCustomerForm(request.POST or None, initial={'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseCustomer.objects.filter(customer_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_customer_id',
        'is_edit_base_id': is_edit_base_id(request.user),
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/BaseCustomer/formBaseCustomer.html", context)

def editBaseCustomer(request, id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    obj = get_object_or_404(BaseCustomer, customer_id = id)
 
    form = BaseCustomerForm(request.POST or None, instance = obj)
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
        'id_name' : '#id_customer_id',
        'is_edit_base_id': is_edit_base_id(request.user),
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/BaseCustomer/formBaseCustomer.html", context)

################### BaseDriver ####################
@login_required(login_url='login')
def settingBaseDriver(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseDriver.objects.all().order_by('-driver_id')

    #กรองข้อมูล
    myFilter = BaseDriverFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_driver = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_driver_page': 'active', 'base_driver': base_driver,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/baseDriver.html",context)

def createBaseDriver(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    form = BaseDriverForm(request.POST or None, initial={'driver_id': generateCodeId('BaseDriver', 1, None, None), 'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseDriver.objects.filter(driver_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
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
        'id_name' : '#id_driver_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

def editBaseDriver(request, id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)
            
    obj = get_object_or_404(BaseDriver, driver_id = id)
 
    form = BaseDriverForm(request.POST or None, instance = obj)
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
        'id_name' : '#id_driver_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

################### BaseCarRegistration ####################
@login_required(login_url='login')
def settingBaseCarRegistration(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseCarRegistration.objects.all().order_by('-car_registration_id')

    #กรองข้อมูล
    myFilter = BaseCarRegistrationFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_car_registration = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_car_registration_page': 'active', 'base_car_registration': base_car_registration,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/baseCarRegistration.html",context)

def createBaseCarRegistration(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    form = BaseCarRegistrationForm(request.POST or None, initial={'car_registration_id': generateCodeId('BaseCarRegistration', 1, None, None), 'user_created': request.user}) 
    if form.is_valid(): 
        new_contact = form.save(commit = False)
        duplicate = BaseCarRegistration.objects.filter(car_registration_id = new_contact.pk).exists()
        if duplicate:
            form.add_error(None, 'มีรหัสนี้อยู่แล้ว กรุณาเปลี่ยนรหัสใหม่.')
        else:
            try:
                new_contact.save()
            except IntegrityError:
                form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
            else:
                return redirect('settingBaseCarRegistration')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_registration_page': 'active',
        'table_name' : 'ทะเบียนรถ',
        'text_mode' : 'เพิ่ม',
        'id_name' : '#id_car_registration_id',
        'mode' : 0,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

def editBaseCarRegistration(request, id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    obj = get_object_or_404(BaseCarRegistration, car_registration_id = id)
 
    form = BaseCarRegistrationForm(request.POST or None, instance = obj)
    if form.is_valid():
        try:
            car_registration_form = form.save()

            # update weight ด้วย
            weights = Weight.objects.filter(car_registration_id = car_registration_form.pk)
            weights.update(car_registration_name = car_registration_form.car_registration_name)
        except IntegrityError:
            form.add_error(None, 'มีชื่อนี้อยู่แล้ว กรุณาตั้งชื่อใหม่.')
        else:
            return redirect('settingBaseCarRegistration')

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_car_registration_page': 'active',
        'table_name' : 'ทะเบียนรถ',
        'text_mode' : 'เปลี่ยน',
        'id_name' : '#id_car_registration_id',
        'mode' : 1,
        active :"active",
    }

    return render(request, "manage/formBase.html", context)

################### BaseCustomerSite ####################
@login_required(login_url='login')
def settingBaseCustomerSite(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = BaseCustomerSite.objects.all().order_by('id')

    #กรองข้อมูล
    myFilter = BaseCustomerSiteFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 15)
    page = request.GET.get('page')
    base_customer_site = p.get_page(page)

    context = {'setting_page':'active', 'setting_base_customer_site_page': 'active', 'base_customer_site': base_customer_site,'filter':myFilter, 'is_edit_setting': is_edit_setting(request.user), active :"active",}
    return render(request, "manage/BaseCustomerSite/baseCustomerSite.html",context)

def createBaseCustomerSite(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

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
        form = BaseCustomerSiteForm(initial={'user_created': request.user})

    context = {
        'form':form,
        'setting_page':'active',
        'setting_base_customer_site_page': 'active',
        'table_name' : 'ลูกค้าและหน้างาน',
        'text_mode' : 'เพิ่ม',
        active :"active",
    }

    return render(request, "manage/BaseCustomerSite/formBaseCustomerSite.html", context)

def editBaseCustomerSite(request, id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

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
        active :"active",
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
        'Detail By Date Between and Weight Type':'/weight/api/between/<str:start_date>/<str:end_date>/<str:weight_type>/',
        'Detail By BWS':'/weight/api/between/<str:start_date>/<str:end_date>/<str:bws>/',
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

# For Insert Report weight for SLC
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightDetailBetween(request, start_date, end_date , weight_type):
    #อันนี้ถ้าเป็นเครื่องขายให้รวมข้อมูลของ uni ด้วย ในโปรแกรมตาชั่งรวม (Report Center) เฉพาะเครื่องขาย
    if weight_type == 1:
        queryset = Weight.objects.filter(date__range=[start_date, end_date], bws__weight_type__id = weight_type, bws__company__code__in = ['SLC', 'UNI'])
    elif weight_type == 2:
       queryset = Weight.objects.filter(date__range=[start_date, end_date], bws__weight_type__id = weight_type, bws__company__code = 'SLC')
    
    #09-09-2024 อันเก่าไม่ครอบคลุมเคส
    #queryset = Weight.objects.filter(date__range=[start_date, end_date], bws__weight_type__id = weight_type, bws__company__code = 'SLC')

    serializer = WeightSerializer(queryset, many = True)
    return Response(serializer.data)

# For get between date by bws
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weightDetailBetweenByBWS(request, start_date, end_date , bws):
    queryset = Weight.objects.filter(date__range=[start_date, end_date], bws = bws)

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

def searchDetailMcType(request):
    #ดึงรายงานของเดือนนั้นๆ
    '''ดึงวันที่ตามหน้า dashbord
    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    end_created = previous_date_time.strftime('%Y-%m-%d')
    start_created = startDateInMonth(end_created)    
    '''

    start_created = request.session['db_start_date']
    end_created = request.session['db_end_date']

    site_id = request.GET.get('site_id', None)
    mc_id = request.GET.get('mc_id', None)
    loss = ProductionLossItem.objects.filter(production__site = site_id, mc_type = mc_id, production__created__range=[start_created, end_created]).values('loss_type__name', 'production__site__base_site_name', 'mc_type__name').annotate(sum_time = Sum('loss_time'))

    index = 1
    try:
        strName = "<table class='table'><thead class='table-info'><tr><th colspan='4'>"+ loss[0]['mc_type__name'] +"</th></thead></tr>"
        for i in loss:
            strName = ''.join([strName, "<tr>"])
            strName = ''.join([strName, "<td>" + str(index) + ")</td><td><b>"+ i['loss_type__name'] + "</td><td>"+ str(i['sum_time'])  + "</td><td> ชม./เดือน </td>"])
            strName = ''.join([strName, "</tr>"])
            index += 1
        strName = ''.join([strName, "</table>"])
    except:
        strName = ''

    data = {
        'instance': strName,
    }
    return JsonResponse(data)

def exportWeightToExpress(request):
    active = request.session['company_code']
    company_in = findCompanyIn(request)

    start_created = request.GET.get('start_created') or None
    end_created = request.GET.get('end_created') or None
    weight_type = request.GET.get('weight_type') or None

    current_date_time = datetime.today()
    previous_date_time = current_date_time - timedelta(days=1)

    if start_created is None and end_created is None:
        start_created = previous_date_time.strftime("%Y-%m-%d")
        end_created = previous_date_time.strftime("%Y-%m-%d")

    my_q = Q()
    if start_created is not None:
        my_q &= Q(date__gte = start_created)
    if end_created is not None:
        my_q &=Q(date__lte = end_created)
    if weight_type is not None:
        my_q &=Q(bws__weight_type = weight_type)

    my_q &=Q(bws__company__code__in = company_in)

    queryset = Weight.objects.filter(my_q)
    if not queryset.exists():
        return HttpResponse("No data to export.")

    data = {'docid': queryset.values_list('doc_id', flat=True),
            'docdat': queryset.values_list('date', flat=True),
            'datin': queryset.values_list('date_in', flat=True),
            'datout': queryset.values_list('date_out', flat=True),
            'tmin': queryset.values_list('time_in', flat=True),
            'tmout': queryset.values_list('time_out', flat=True),
            'truck': queryset.values_list('car_registration_name', flat=True),
            'cuscod': queryset.values_list('customer_id', flat=True),
            'cusname': queryset.values_list('customer_name', flat=True),
            'depcod': queryset.values_list('base_weight_station_name', flat=True),
            'stkcod': queryset.values_list('stone_type_id', flat=True),
            'stkdes': queryset.values_list('stone_type_name', flat=True),
            'trnqty': queryset.values_list('weight_total', flat=True),
            'unitpr': queryset.values_list('price_per_ton', flat=True),
            'amount': queryset.values_list('amount', flat=True),
            'vat': queryset.values_list('vat', flat=True),
            'stonenam': queryset.values_list('stone_color', flat=True),
            'transport': queryset.values_list('transport', flat=True),
            'nillnam': queryset.values_list('mill_name', flat=True),
            'iscancle': queryset.values_list('is_cancel', flat=True),
            'sttcod': queryset.values_list('base_weight_station_name', flat=True),
            'scaleid': queryset.values_list('scale_id', flat=True),
            'scalenam': queryset.values_list('scale_name', flat=True),
            'scoopnam': queryset.values_list('scoop_name', flat=True),
            'siteid': queryset.values_list('site_id', flat=True),
            'sitenam': queryset.values_list('site_name', flat=True),
            'isvat': queryset.values_list('is_s', flat=True),
            'vattyp': queryset.values_list('vat_type', flat=True),
            'pay': queryset.values_list('pay', flat=True),
            'company': queryset.values_list('bws__company__code', flat=True),
            'bws': queryset.values_list('bws', flat=True),
            'note': queryset.values_list('note', flat=True),
            }

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=weight_express({active}) '+ start_created + " to "+ end_created +'.xlsx'

    df.to_excel(response, index=False, engine='openpyxl')

    return response

def setSessionCompany(request):
    name = request.GET.get('title', None)
    request.session['company_code'] = name
    try:
        company = BaseCompany.objects.get(code=request.session['company_code'])
        request.session['company'] = company.name
    except BaseCompany.DoesNotExist:
        print(f"Company with code {request.session['company_code']} not found.")

    data = {
        'instance': request.session['company_code'],
    }

    return JsonResponse(data)

def setDateInDashbord(request):
    db_start_date = request.GET.get('db_start_date', None)
    db_end_date = request.GET.get('db_end_date', None)

    request.session['db_start_date'] = db_start_date
    request.session['db_end_date'] = db_end_date

    data = {
        'db_start_date' : db_start_date,
        'db_end_date' : db_end_date,
    }
    return JsonResponse(data)

@login_required(login_url='login')
def viewStock(request):
    #active : active คือแท็ปบริษัท active
    try:
        active = request.session['company_code']
        company_in = findCompanyIn(request)
    except:
        return redirect('logout')

    data = Stock.objects.filter(company__code__in = company_in).order_by('-created')

    #กรองข้อมูล
    myFilter = StockFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    stock = p.get_page(page)

    context = {'stock_page':'active', 'stock': stock,'filter':myFilter, active :"active",}
    return render(request, "stock/viewStock.html",context)

@login_required(login_url='login')
def removeStock(request, stock_id):
    stk = Stock.objects.get(id = stock_id)
    #ลบ ProductionLossItem ใน Production ด้วย
    ssn = StockStone.objects.filter(stk = stk)
    for sn in ssn:
        items = StockStoneItem.objects.filter(ssn = sn)
        items.delete()

    ssn.delete()
    stk.delete()
    return redirect('viewStock')

@login_required(login_url='login')
def removeStockStone(request, ssn_id):

    #ลบ ProductionLossItem ใน Production ด้วย
    ssn = StockStone.objects.get(id = ssn_id)
    stock_id = ssn.stk

    items = StockStoneItem.objects.filter(ssn = ssn)
    items.delete()

    ssn.delete()
    return HttpResponseRedirect(reverse('editStep2Stock', args=(stock_id,)))

@login_required(login_url='login')
def createStock(request):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    base_stock_source = BaseStockSource.objects.all().order_by('step')
    StockStoneItemFormSet = modelformset_factory(StockStoneItem, fields=('source', 'quantity'), extra=len(base_stock_source), widgets={})
    
    if request.method == 'POST':
        form = StockForm(request.POST)
        ss_form = StockStoneForm(request.POST)
        formset = StockStoneItemFormSet(request.POST)
        if form.is_valid() and ss_form.is_valid() and formset.is_valid():
            form = form.save()

            ssn = ss_form.save()
            ssn.stk = form
            ssn.save()

            total = 0
            formset_instances = formset.save(commit=False)
            for instance in formset_instances:
                instance.ssn = ssn

                if instance.quantity:
                    if instance.source.symbol == "+":
                        total += instance.quantity
                    elif instance.source.symbol == "-":
                        total -= instance.quantity
                else:
                    instance.quantity = 0
                instance.save()

            ssn.total = total
            ssn.save()

            return HttpResponseRedirect(reverse('editStep2Stock', args=(ssn.stk,)))
    else:
        form = StockForm(initial={'company': company})
        ss_form = StockStoneForm()
        formset = StockStoneItemFormSet(queryset=StockStoneItem.objects.none())

    context = {'stock_page':'active', 'form': form, 'ss_form': ss_form, 'formset' : formset, 'base_stock_source': base_stock_source, active :"active", 'disabledTab' : 'disabled', 'is_edit_stock': is_edit_stock(request.user)}
    return render(request, "stock/createStock.html",context)

@login_required(login_url='login')
def editStep2Stock(request, stock_id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    base_stock_source = BaseStockSource.objects.all().order_by('step')
    StockStoneItemFormSet = modelformset_factory(StockStoneItem, fields=('source', 'quantity'), extra=len(base_stock_source), widgets={})
    
    try:
        stock_data = Stock.objects.get(id=stock_id)
    except Stock.DoesNotExist:
        return redirect('viewProduction')

    ssn_data = StockStone.objects.filter(stk=stock_data)

    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock_data)
        ss_form = StockStoneForm(request.POST)
        formset = StockStoneItemFormSet(request.POST)
        
        if form.is_valid() and ss_form.is_valid() and formset.is_valid():
            form = form.save()

            ssn = ss_form.save(commit=False)
            if  ss_form.cleaned_data.get('stone'):
                ssn.stk = form
                ssn.save()

                total = 0
                formset_instances = formset.save(commit=False)
                for instance in formset_instances:
                    instance.ssn = ssn

                    if instance.quantity:
                        if instance.source.symbol == "+":
                            total += instance.quantity
                        elif instance.source.symbol == "-":
                            total -= instance.quantity
                    else:
                        instance.quantity = 0
                    instance.save()

                ssn.total = total
                ssn.save()

            return HttpResponseRedirect(reverse('editStep2Stock', args=(stock_id,)))
    else:
        form = StockForm(instance=stock_data)
        ss_form = StockStoneForm()
        formset = StockStoneItemFormSet(queryset=StockStoneItem.objects.none())

    context = {'stock_page':'active', 'form': form, 'ss_form': ss_form, 'formset' : formset, 'base_stock_source': base_stock_source, 'ssn_data': ssn_data,'stock_data':stock_data, active :"active", 'disabledTab' : 'disabled', 'is_edit_stock': is_edit_stock(request.user)}
    return render(request, "stock/editStep2Stock.html",context)

@login_required(login_url='login')
def editStockStoneItem(request, stock_id, ssn_id):
    active = request.session['company_code']
    company = BaseCompany.objects.get(code = active)

    base_stock_source = BaseStockSource.objects.all().order_by('step')
    
    try:
        stock_data = Stock.objects.get(id=stock_id)
    except Stock.DoesNotExist:
        return redirect('viewProduction')

    ssn_data = StockStone.objects.filter(stk = stock_id)#ssn all in stock id
    data = StockStone.objects.get(id = ssn_id)#id edit

    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock_data)
        ss_form = StockStoneForm(request.POST, instance=data)
        formset = StockStoneItemInlineFormset(request.POST, instance=data)
        
        if form.is_valid() and ss_form.is_valid() and formset.is_valid():
            form = form.save()

            ssn = ss_form.save(commit=False)
            if  ss_form.cleaned_data.get('stone'):
                ssn.stk = form
                ssn.save()

                formset_instances = formset.save(commit=False)
                for instance in formset_instances: #อันนี้ไม่มี deleted_objects นะ
                    if instance.quantity is None:
                        instance.quantity = 0
                    instance.save()

                # add function calculate total stock
                ssn.total = calculateTotalStock(ssn_id)
                ssn.save()

            return HttpResponseRedirect(reverse('editStep2Stock', args=(stock_id,)))
    else:
        form = StockForm(instance=stock_data)
        ss_form = StockStoneForm(instance=data)
        formset = StockStoneItemInlineFormset(instance=data)

    context = {'stock_page':'active', 'form': form, 'ss_form': ss_form, 'formset' : formset, 'base_stock_source': base_stock_source, 'ssn_data': ssn_data, 'ss_id': data.id, 'ss_stone_id': data.stone.base_stone_type_id, 'stock_data':stock_data, active :"active", 'disabledTab' : 'disabled', 'is_edit_stock': is_edit_stock(request.user)}
    return render(request, "stock/editStockStoneItem.html",context)

def calculateTotalStock(ssn_id):
    total = 0
    items = StockStoneItem.objects.filter(ssn = ssn_id)
    for i in items:
        if i.quantity:
            if i.source.symbol == "+":
                total += i.quantity
            elif i.source.symbol == "-":
                total -= i.quantity
    return total

def searchStockInDay(request):
    if 'created' in request.GET and 'company' in request.GET and 'stock_id' in request.GET:
        created =  request.GET.get('created')
        company =  request.GET.get('company')
        stock_id =  request.GET.get('stock_id')

        if stock_id == '':
            have_stock = Stock.objects.filter(company = company, created = created).exists()
        else:
            have_stock = Stock.objects.filter(~Q(id = stock_id), company = company, created = created).exists()
    data = {
        'have_stock' :have_stock,
    }
    return JsonResponse(data)

def searchDataWeightToStock(request):
    if 'created' in request.GET and 'company' in request.GET and 'stone' in request.GET:
        created =  request.GET.get('created')
        company =  request.GET.get('company')
        stone =  request.GET.get('stone')

        sell = 0
        prod = 0
        #ยกมา
        try:
            quot = StockStone.objects.filter(~Q(stk__created = created), stk__company = company, stone = stone).order_by('-stk__created').values('total').first()['total'] or Decimal('0.0')
        except TypeError:
            quot = Decimal('0.0')

        #ผลิต
        se_item = StoneEstimateItem.objects.filter(se__created = created, stone_type = stone).values('se__created','percent','se__site')
        for i in se_item:
            crush = Weight.objects.filter(bws__company = company, site = i['se__site'], bws__weight_type = 2 , date = i['se__created']).aggregate(s = Sum("weight_total"))["s"] or Decimal('0.0')
            prod += calculateEstimate(i['percent'], crush)

        #ขาย
        sell = Weight.objects.filter(bws__company = company, bws__weight_type = 1, stone_type = stone, date = created).aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')

        #อนุเคราะห์ (ปลายทาง 300PL)
        aid = Weight.objects.filter(bws__company = company, bws__weight_type = 1, stone_type = stone, date = created, site = '300PL').aggregate(s=Sum("weight_total"))["s"] or Decimal('0.0')

    data = {'sell' : sell, 'prod' : prod, 'aid' : aid, 'quot': quot,}
    return JsonResponse(data)