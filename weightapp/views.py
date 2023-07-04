from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.cache import cache_page
from weightapp.models import Weight, Production, BaseLossType, ProductionLossItem, BaseMill, BaseLineType
from django.db.models import Sum, Q
from decimal import Decimal
from django.views.decorators.cache import cache_control
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from .filters import WeightFilter, ProductionFilter
from .forms import ProductionForm, ProductionLossItemForm, ProductionModelForm, ProductionLossItemFormset, ProductionLossItemInlineFormset
import xlwt
from django.db.models import Count, Avg
import stripe, logging, datetime
import openpyxl
from openpyxl.styles import PatternFill, Alignment, Font, Color, NamedStyle, Side, Border
from openpyxl.utils import get_column_letter
from datetime import date, timedelta, datetime
from django.views import generic
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django import forms
from django.db.models import Sum
import random
from django.db.models.functions import Coalesce
from django.db.models import F, ExpressionWrapper
from django.db import models

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

def getSumByStone(request, mode, stoneType):
    w = Weight.objects.filter(base_weight_station_name__weight_type = mode, stone_type = stoneType, date__range=('2023-02-01', '2023-02-28')).aggregate(s=Sum("weight_total"))["s"]
    return w

def getNumListStoneWeightChart(request):
    sum_other_sell_no = Decimal('0.00')
    sum_other_stock_no = Decimal('0.00')

    #sell
    sum_tf_no = getSumByStone(request, 1, 'หิน 3/4')
    sum_fe_no = getSumByStone(request, 1, 'หินใหญ่ขนาด 40-80 มม.')
    sum_fex_no = getSumByStone(request, 1, 'หินใหญ่ขนาด 40-80 มม.(ส่งออก)')
    sum_du_no = getSumByStone(request, 1, 'หินฝุ่น')
    sum_dusa_no = getSumByStone(request, 1, 'หินฝุ่น(แทนทราย)')
    sum_dudo_no = getSumByStone(request, 1, 'หินฝุ่นโดโลไมท์(ส่งออก)')


    other_sell_no = Weight.objects.filter(
                ~Q(stone_type='หิน 3/4') & ~Q(stone_type='หินใหญ่ขนาด 40-80 มม.') &
                ~Q(stone_type='หินใหญ่ขนาด 40-80 มม.(ส่งออก)') & ~Q(stone_type='หินใหญ่ขนาด 40-80 มม.(กองสต๊อก)') &
                ~Q(stone_type='หินฝุ่น') & ~Q(stone_type='หินฝุ่น(แทนทราย)') &
                ~Q(stone_type='หินฝุ่นโดโลไมท์(ส่งออก)') & ~Q(stone_type='หินฝุ่น(กองสต็อก)')
                , date__range=('2023-02-01', '2023-02-28')
                , base_weight_station_name__weight_type = 1
            ).aggregate(s=Sum("weight_total"))["s"]
    sum_other_sell_no = sum_other_sell_no + other_sell_no

    #stock
    sum_fes_no = getSumByStone(request, 2, 'หินใหญ่ขนาด 40-80 มม.(กองสต๊อก)')
    sum_du_s_no = getSumByStone(request, 2, 'หินฝุ่น')
    sum_dust_no = getSumByStone(request, 2, 'หินฝุ่น(กองสต็อก)')

    other_stock_no = Weight.objects.filter(
                ~Q(stone_type='หิน 3/4') & ~Q(stone_type='หินใหญ่ขนาด 40-80 มม.') &
                ~Q(stone_type='หินใหญ่ขนาด 40-80 มม.(ส่งออก)') & ~Q(stone_type='หินใหญ่ขนาด 40-80 มม.(กองสต๊อก)') &
                ~Q(stone_type='หินฝุ่น') & ~Q(stone_type='หินฝุ่น(แทนทราย)') &
                ~Q(stone_type='หินฝุ่นโดโลไมท์(ส่งออก)') & ~Q(stone_type='หินฝุ่น(กองสต็อก)')
                , date__range=('2023-02-01', '2023-02-28')
                , base_weight_station_name__weight_type = 2
    ).aggregate(s=Sum("weight_total"))["s"]
    sum_other_stock_no = sum_other_stock_no + other_stock_no

    number_list = [sum_tf_no, sum_fe_no, sum_fex_no, sum_du_no, sum_dusa_no, sum_dudo_no, sum_du_s_no, sum_fes_no, sum_dust_no]
    return number_list

# Create your views here.
@cache_page(60 * 15)
@login_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    weight = Weight.objects.filter(date='2023-03-02', base_weight_station_name__weight_type = 1).values('date','customer_name').order_by('customer_name').annotate(sum_weight_total=Sum('weight_total'))
    sum_all_weight = Weight.objects.filter(date='2023-03-02', base_weight_station_name__weight_type = 1).aggregate(s=Sum('weight_total'))["s"]

    tf_to_day = Weight.objects.filter(stone_type = 'หิน 3/4', date ='2023-03-02').aggregate(Sum('weight_total'))
    fex_to_day = Weight.objects.filter(stone_type = 'หินใหญ่ขนาด 40-80 มม.(ส่งออก)', date ='2023-03-02').aggregate(Sum('weight_total'))
    du_to_day = Weight.objects.filter( Q(stone_type='หินฝุ่น') & Q(stone_type='หินฝุ่น(แทนทราย)'), date ='2023-03-02').aggregate(Sum('weight_total'))
    mix_to_day = Weight.objects.filter(Q(stone_type='หินคลุก A') & Q(stone_type='หินคลุก B'), date ='2023-03-02').aggregate(Sum('weight_total'))

    stone_type_list = ['หิน 3/4','หินใหญ่ขนาด 40-80 มม.', 'หินใหญ่ขนาด 40-80 มม.(ส่งออก)','หินฝุ่น','หินฝุ่น(แทนทราย)','หินฝุ่นโดโลไมท์(ส่งออก)','หินใหญ่ขนาด 40-80 มม.(กองสต๊อก)','หินฝุ่น', 'หินฝุ่น(กองสต็อก)']
    number_list = getNumListStoneWeightChart(request)

    context = {'weight': weight,
               'sum_all_weight': sum_all_weight,
                'stone_type_list': stone_type_list,
                'number_list': number_list,
                'tf_to_day':tf_to_day,
                'fex_to_day':fex_to_day,
                'du_to_day':du_to_day,
                'mix_to_day':mix_to_day,
                'dashboard_page':'active',}
    return render(request, "index.html",context)

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
    data = Weight.objects.filter(date__gte='2023-01-01', date__lte='2023-03-31').order_by('date')

    #กรองข้อมูล
    myFilter = WeightFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    weight = p.get_page(page)

    context = {'weight':weight,'filter':myFilter, 'weightTable_page':'active', }
    return render(request, "weightTable.html",context)

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
        my_q &=Q(stone_type__icontains = stone_type)

    my_q &= ~Q(customer_name ='ยกเลิก') & Q(mill_name__in = ["โรงโม่ 1", "โรงโม่ 2", "โรงโม่ 3"])

    # Query ข้อมูลขาย
    data = Weight.objects.filter( my_q, base_weight_station_name__weight_type = 1).order_by('date','mill_name').values_list('date','mill_name', 'stone_type').annotate(sum_weight_total = Sum('weight_total'))
    # Query ข้อมูลผลิตรวม
    data_sum_produc = Weight.objects.filter( my_q, base_weight_station_name__weight_type = 2, stone_type__icontains = 'เข้าโม่').order_by('date','mill_name').values_list('date','mill_name').annotate(sum_weight_total = Sum('weight_total'))


    startDate = datetime.strptime(start_created or '2023-01-01', "%Y-%m-%d").date()
    endDate = datetime.strptime(end_created or datetime.today().strftime('%Y-%m-%d'), "%Y-%m-%d").date()
    #list วันที่ทั้งหมด ระหว่าง startDate และ endDate
    list_date_between = [startDate + timedelta(days=x) for x in range((endDate - startDate).days)]

    # Create a new workbook and get the active worksheet
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

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

    # Loop through the dates and write data to the worksheet
    row_index = 3
    for date, mill_data in date_data.items():
        #เขียนวันที่ใน worksheet column 1
        worksheet.cell(row=row_index, column=1, value=date).style = date_style
        worksheet.cell(row=row_index, column=1).alignment = Alignment(horizontal='center')
        #เขียน weight total ของแต่ละหินใน worksheet
        column_index = 2 + len(mills)
        for mill in mills:
            stone_data = mill_data.get(mill, {})
            for stone in stones:
                value = stone_data.get(stone, '')
                worksheet.cell(row=row_index, column=column_index, value=value).number_format = '#,##0.00'
                column_index += 1
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
    for row_num, date in enumerate(sorted(set(row[0] for row in data)), 2):
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

    '''
    for col in range(1, column_index):
        worksheet.cell(1 , col).fill = PatternFill(start_color='FFEAAD', end_color='FFEAAD', fill_type="solid") #used hex code for red color
        worksheet.cell(2 , col).fill = PatternFill(start_color='FFEAAD', end_color='FFEAAD', fill_type="solid") #used hex code for red color    
    '''

    # Set the response headers for the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=export.xlsx'

    # Save the workbook to the response
    workbook.save(response)

    return response

def viewProduction(request):
    data = Production.objects.all()

    #กรองข้อมูล
    myFilter = ProductionFilter(request.GET, queryset = data)
    data = myFilter.qs

    #สร้าง page
    p = Paginator(data, 10)
    page = request.GET.get('page')
    product = p.get_page(page)

    context = {'production_page':'active', 'product': product,'filter':myFilter, }
    return render(request, "production/viewProduction.html",context)

def calculatorDiff(request, start_time, end_time):
    difference = None
    if start_time and end_time:
        difference = end_time - start_time
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

def createProduction(request):
    base_loss_type = BaseLossType.objects.all()

    #หาบันทึกปฎิบัติการของวันนี้ เพื่อเช็คไม่ให้ save mill และ line ซ้ำกัน
    production_on_day = Production.objects.filter(created = datetime.today()).values('mill', 'line_type', 'created')

    ProductionLossItemFormSet = modelformset_factory(ProductionLossItem, fields=('loss_type', 'loss_time'), extra=len(base_loss_type), widgets={'loss_time': forms.TimeInput(format='%H:%M', attrs={'class':'form-control', 'type': 'time'}),})
    if request.method == 'POST':
        production_form = ProductionForm(request.POST)
        formset = ProductionLossItemFormSet(request.POST)
        if production_form.is_valid() and formset.is_valid():
            production = production_form.save()

            formset_instances = formset.save(commit=False)
            for instance in formset_instances:
                instance.production = production
                instance.save()

            #คำนวนเวลารวมในการสูญเสีย
            total_loss_time = ProductionLossItem.objects.filter(production = production).aggregate(s=Sum("loss_time"))["s"]
            production.total_loss_time = total_loss_time
            production.save()

            return redirect('viewProduction')
    else:
        production_form = ProductionForm()
        formset = ProductionLossItemFormSet(queryset=ProductionLossItem.objects.none())

    context = {'production_page':'active', 'form': production_form, 'formset': formset, 'base_loss_type':base_loss_type, 'production_on_day' : production_on_day}
    return render(request, "production/createProduction.html",context)

def editProduction(request, pd_id):
    pd_data = Production.objects.get(id = pd_id)

    #หาบันทึกปฎิบัติการของวันนี้ เพื่อเช็คไม่ให้ save mill และ line ซ้ำกัน
    production_on_day = Production.objects.filter(~Q(id = pd_data.id), created = datetime.today()).values('mill', 'line_type', 'created')

    if request.method == "POST":
        formset = ProductionLossItemInlineFormset(request.POST, request.FILES, instance=pd_data)
        form = ProductionForm(request.POST, request.FILES, instance=pd_data)

        if form.is_valid() and formset.is_valid():
            # save production
            production = form.save(commit=False)

            # save ProductionLossItem
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()

            #คำนวนเวลารวมในการสูญเสีย
            total_loss_time = ProductionLossItem.objects.filter(production = production).aggregate(s=Sum("loss_time"))["s"]
            production.total_loss_time = total_loss_time
            production.save()
            return redirect('viewProduction')
    else:
        formset = ProductionLossItemInlineFormset(instance=pd_data)
        form = ProductionForm(instance=pd_data)

    context = {'production_page':'active', 'form': form, 'formset': formset, 'pd': pd_data, 'production_on_day': production_on_day}
    return render(request, "production/editProduction.html",context)

def removeProduction(request, pd_id):
    pd = Production.objects.get(id = pd_id)
    #ลบ ProductionLossItem ใน Production ด้วย
    items = ProductionLossItem.objects.filter(production = pd)
    items.delete()
    #ลบ Production ทีหลัง
    pd.delete()
    return redirect('viewProduction')

def dateFromAccumulated(request, day):
    dt = datetime.strptime(f"{day}", '%Y-%m-%d')
    result = dt.replace(day=1).date()
    return f"{result}"

def calculatCapacityPerHour(request, data_sum_produc, accumulated_produc):
    result = Decimal('0.0')
    if data_sum_produc and accumulated_produc:
        result = data_sum_produc/accumulated_produc/24
    return result

def formatHourMinute(time):
    result = None
    if time:
       result = (datetime.min + time).strftime("%H:%M") or None
    return result

def exportExcelProductionAndLoss(request):
    start_created = request.GET.get('start_created') or None
    end_created = request.GET.get('end_created') or None
    mill = request.GET.get('mill') or None

    my_q = Q()
    if start_created is not None:
        my_q &= Q(created__gte = start_created)
    if end_created is not None:
        my_q &=Q(created__lte = end_created)
    
    count_loss = BaseLossType.objects.all()
    pd_mills = Production.objects.filter(my_q).values_list('mill', flat=True).distinct()
    mills = BaseMill.objects.filter(id__in = pd_mills)

    workbook = openpyxl.Workbook()
    for mill in mills:
        sheet = workbook.create_sheet(title=mill.name)

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
            
            date_from_accumulated = dateFromAccumulated(request, created_date)

            for line_type in BaseLineType.objects.filter(id__in=line_types):
                production = Production.objects.filter(mill = mill, line_type = line_type, created = created_date).first()
                accumulated_goal = Production.objects.filter(mill = mill, line_type = line_type, created__range=(date_from_accumulated, created_date)).aggregate(s=Sum("goal"))["s"]

                data_sum_produc = Weight.objects.filter(mill_name=mill ,date = created_date, base_weight_station_name__weight_type = 2, stone_type__icontains = 'เข้าโม่').aggregate(s=Sum("weight_total"))["s"]
                accumulated_produc = Weight.objects.filter(mill_name=mill ,date__range=(date_from_accumulated, created_date) , base_weight_station_name__weight_type = 2, stone_type__icontains = 'เข้าโม่').aggregate(s=Sum("weight_total"))["s"]

                sum_by_mill = Production.objects.filter(my_q, mill=mill, line_type = line_type).distinct().aggregate(Sum('plan_time'),Sum('run_time'),Sum('total_loss_time'))
                cal_by_mill = Production.objects.filter(my_q, mill=mill, line_type = line_type).distinct().annotate(working_time = ExpressionWrapper(F('run_time') - F('total_loss_time'), output_field= models.DurationField())).aggregate(total_working_time=Sum('working_time'))['total_working_time']

                capacity_per_hour = calculatCapacityPerHour(request, data_sum_produc, accumulated_produc)
                if production:
                    row.extend([production.goal, accumulated_goal , formatHourMinute(production.plan_start_time), formatHourMinute(production.plan_end_time), formatHourMinute(production.plan_time), formatHourMinute(production.run_start_time) if production.run_start_time else production.mile_run_start_time  , formatHourMinute(production.run_end_time) if production.run_end_time else production.mile_run_end_time, formatHourMinute(production.run_time)])
                    row.extend([formatHourMinute(pd_loos_item.loss_time) for pd_loos_item in ProductionLossItem.objects.filter(production = production).order_by('loss_type__id')])
                    row.extend([formatHourMinute(production.total_loss_time), calculatorDiff(request, production.total_loss_time, production.run_time), data_sum_produc, accumulated_produc, capacity_per_hour, production.note,])
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