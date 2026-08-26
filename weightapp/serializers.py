from rest_framework import serializers
from weightapp.models import BaseScoop, BaseMill, Weight, BaseCustomer, BaseStoneType, BaseCarTeam, BaseDriver, BaseCarRegistration, BaseCar, BaseSite, BaseJobType, BaseCustomerSite, DeliveryOrder, WeightDelivery, AppRelease, ClientUpdateLog, UserScale, BaseCompanyMapBaseCustomer, InternationalFreightRate, InternationalFreightRateTeam, InternationalFreightRateFuelPrice, InternationalFreightRateStatus, InternationalFreightRateApproval, InternationalFreightRateApprovalAction, INTERNATIONAL_FREIGHT_RATE_FIRST_DATE
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone
from datetime import date
from rest_framework.validators import ValidationError
from rest_framework.authtoken.models import Token

class CustomField(serializers.CharField):
    def to_representation(self, obj):
        # Custom logic to represent the field
        return obj.custom_field_value
    
class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=80)
    username = serializers.CharField(max_length=45)
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "password"]

    def validate(self, attrs):

        email_exists = User.objects.filter(email=attrs["email"]).exists()

        if email_exists:
            raise ValidationError("Email has already been used")

        return super().validate(attrs)

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = super().create(validated_data)

        user.set_password(password)

        user.save()

        Token.objects.create(user=user)

        return user
    
class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ('username', 'email', 'password')
		
		extra_kwargs = {'password': {'write_only': True}}
	def create(self, validated_data):
		user = User(
			email=validated_data['email'],
			username=validated_data['username']
		)
		user.set_password(validated_data['password'])
		user.save()
		return user

class WeightSerializer(serializers.ModelSerializer):
    weight_id = serializers.IntegerField(required=False)
    class Meta:
        model = Weight
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Iterate through all fields in the serializer's model
        for field_name, field in self.fields.items():
            # Check if the field's value is null (None)
            if field_name in data and data[field_name] is None:
                data[field_name] = None

        return data

class UserScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserScale
        #exclude = ('password',)
        fields = '__all__'

class BaseScoopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseScoop
        fields = ('รหัสผู้ตัก', 'ชื่อผู้ตัก', 'v_stamp', 'company')

    # Define custom field names
    รหัสผู้ตัก = serializers.CharField(source='scoop_id')
    ชื่อผู้ตัก = serializers.CharField(source='scoop_name')
    company = serializers.CharField(source='company.code')

class BaseCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCustomer
        fields = '__all__'
        extra_fields = ['customer_id']

class BaseMillSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseMill
        fields = ('รหัสโรงโม่', 'ชื่อโรงโม่', 'weight_type', 'v_stamp')

    # Define custom field names
    รหัสโรงโม่ = serializers.CharField(source='mill_id')
    ชื่อโรงโม่ = serializers.CharField(source='mill_name')

class BaseStoneTypeSerializer(serializers.ModelSerializer):
    รหัสหิน = serializers.CharField(source='base_stone_type_id')
    ชื่อหิน = serializers.CharField(source='base_stone_type_name')

    class Meta:
        model = BaseStoneType
        fields = ('รหัสหิน', 'ชื่อหิน', 'cal_q', 'v_stamp', 'inactive')

class ThaiEnglishField(serializers.Field):
    def to_representation(self, obj):
        return {
            'ค่าคำนวณคิว': str(obj),
            'cal_q': str(obj),
        }

    def to_internal_value(self, data):
        return data

class BaseStoneTypeTestSerializer(serializers.ModelSerializer):
    cal_q = ThaiEnglishField()
    รหัสหิน = serializers.CharField(source='base_stone_type_id')
    ชื่อหิน = serializers.CharField(source='base_stone_type_name')
    ประเภทหิน = serializers.CharField(source='type')

    class Meta:
        model = BaseStoneType
        fields = ('รหัสหิน', 'ชื่อหิน', 'ประเภทหิน', 'cal_q',)

class BaseCarTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCarTeam
        fields = ('รหัสทีม', 'ชื่อทีม', 'v_stamp')

    # Define custom field names
    รหัสทีม = serializers.CharField(source='car_team_id')
    ชื่อทีม = serializers.CharField(source='car_team_name')

class BaseDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDriver
        fields = ('รหัสผู้ขับ', 'ชื่อผู้ขับ', 'v_stamp', 'company')

    # Define custom field names
    รหัสผู้ขับ = serializers.CharField(source='driver_id')
    ชื่อผู้ขับ = serializers.CharField(source='driver_name')
    company = serializers.CharField(source='company.code')

class BaseCarRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCarRegistration
        fields = ('รหัสทะเบียนรถ', 'ชื่อทะเบียนรถ','ประเภทรถ', 'v_stamp', 'company')

    # Define custom field names
    รหัสทะเบียนรถ = serializers.CharField(source='car_registration_id')
    ชื่อทะเบียนรถ = serializers.CharField(source='car_registration_name')
    ประเภทรถ = serializers.CharField(source='car_type')
    company = serializers.CharField(source='company.code')

class BaseCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCar
        fields = ('รหัสรถร่วม', 'ชื่อรถร่วม','รหัสทีม', 'v_stamp')

    # Define custom field names
    รหัสรถร่วม = serializers.CharField(source='car_id')
    ชื่อรถร่วม = serializers.CharField(source='car_name')
    รหัสทีม = serializers.CharField(source='base_car_team.car_team_id')

class CarPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCar
        fields = ('code', 'name','oil_cus')

    # Define custom field names
    code = serializers.CharField(source='car_id')
    name = serializers.CharField(source='car_name')
    oil_cus = serializers.CharField(source='base_car_team.oil_customer_id')

class BaseSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseSite
        fields = ('base_site_id', 'base_site_name', 'weight_type', 'v_stamp')


class BaseJobTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseJobType
        fields = '__all__'
        extra_fields = ['base_job_type_id']


class BaseCustomerSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCustomerSite
        fields = '__all__'
        extra_fields = ['id']

class DeliveryOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryOrder
        fields = '__all__'
        extra_fields = ['id']


class K2MDSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryOrder
        fields = ('docNo', 'deliveryDate', 'carCompany','carCustomer', 'carCompanyRem', 'carCustomerRem', 'carCompanyTot', 'carCustomerTot', 'qty', 'qtyTot', 'unitName', 'compCode', 'status')

    # Define custom field names
    docNo = serializers.CharField(source='doc_no')
    deliveryDate = serializers.DateField(source='delivery_date')

    carCompany = serializers.IntegerField(source='car_company')
    carCustomer = serializers.IntegerField(source='car_customer')

    carCompanyRem = serializers.IntegerField(source='car_company_rem')
    carCustomerRem = serializers.IntegerField(source='car_customer_rem')

    carCompanyTot = serializers.IntegerField(source='car_company_tot')
    carCustomerTot = serializers.IntegerField(source='car_customer_tot')

    qtyTot = serializers.DecimalField(source='qty_tot', max_digits=10, decimal_places=2)

    unitName = serializers.CharField(source='unit_name')

    compCode = serializers.CharField(source='comp_code')


class WeightDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightDelivery
        fields = '__all__'
        extra_fields = ['id']

class AppReleaseSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    sql_script_url = serializers.SerializerMethodField()

    class Meta:
        model = AppRelease
        fields = ['product_code', 'version', 'channel', 'release_notes', 'download_url', 'file_hash_sha256',
                  'sql_script_url', 'sql_script_hash_sha256', 'is_mandatory', 'released_at']

    def get_download_url(self, obj):
        request = self.context.get('request')
        if obj.installer_file and request:
            return request.build_absolute_uri(obj.installer_file.url)
        return obj.installer_file.url if obj.installer_file else None

    def get_sql_script_url(self, obj):
        request = self.context.get('request')
        if obj.sql_script and request:
            return request.build_absolute_uri(obj.sql_script.url)
        return obj.sql_script.url if obj.sql_script else None


class ClientUpdateLogSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product_code', required=False, allow_blank=True, default='slcblue')

    class Meta:
        model = ClientUpdateLog
        fields = ['product', 'weight_station', 'machine_name', 'from_version', 'to_version', 'update_applied', 'sql_applied']

class BaseCompanyMapBaseCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCompanyMapBaseCustomer
        fields = '__all__'

class InternationalFreightRateTeamSerializer(serializers.ModelSerializer):
    # ฟิลด์ในโมเดลชื่อ team แต่รับ/ส่ง JSON ด้วยคีย์ team_id ให้ตรงกับชื่อคอลัมน์ใน db
    # ส่ง null หรือไม่ส่งมาเลย = แถวนี้ใช้กับ "ทุกทีม"
    team_id = serializers.PrimaryKeyRelatedField(
        source='team',
        queryset=BaseCarTeam.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )

    class Meta:
        model = InternationalFreightRateTeam
        # ไม่รับ international_freight_rate จาก client เพราะตัวแม่เป็นคนใส่ให้ตอนสร้าง
        exclude = ['international_freight_rate', 'team']
        extra_kwargs = {
            'weight_carried_id': {'required': True, 'allow_null': False, 'allow_blank': False},
        }


THAI_MONTH_NAMES = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม',
]


def _thaiMonthLabel(month_date):
    """date -> 'พฤษภาคม 2569' ให้ข้อความ error ตรงกับที่หน้าเว็บแสดง"""
    if not month_date:
        return '-'
    return '%s %s' % (THAI_MONTH_NAMES[month_date.month - 1], month_date.year + 543)


class InternationalFreightRateFuelPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternationalFreightRateFuelPrice
        # ตัวแม่เป็นคนใส่ root (เส้นทาง) ให้ตอนสร้าง เหมือนฝั่ง teams
        exclude = ['root']
        extra_kwargs = {
            'month': {'required': True, 'allow_null': False},
            'average_fuel_price': {'required': True, 'allow_null': False},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class InternationalFreightRateSerializer(serializers.ModelSerializer):
    teams = InternationalFreightRateTeamSerializer(many=True, required=False)
    fuel_prices = InternationalFreightRateFuelPriceSerializer(many=True, required=False)
    # หมายเหตุตอนขออนุมัติ ไม่ใช่คอลัมน์ของใบ แต่ไปลงตาราง approval เป็นข้อความรอบแรกของบทสนทนา
    comment = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                    allow_null=True, trim_whitespace=True)

    class Meta:
        model = InternationalFreightRate
        fields = '__all__'
        # โมเดลอนุญาต null/blank ไว้เผื่อกรณีอื่น (เช่นแถว log) แต่ตอนสร้างรายการใหม่
        # ต้องกรอกให้ครบทุกช่อง ห้ามสร้างรายการที่มีค่าว่าง/null
        extra_kwargs = {
            # origin/destination เป็น FK แล้ว รับเป็น id ของ BaseCompanyMapBaseCustomer
            # ห้ามใส่ allow_blank เพราะเป็น option ของฟิลด์ข้อความเท่านั้น จะ error ตอนสร้าง serializer
            'origin': {'required': True, 'allow_null': False},
            'destination': {'required': True, 'allow_null': False},
            'base_fuel_price': {'required': True, 'allow_null': False},
            'distance': {'required': True, 'allow_null': False},
            'payload_weight': {'required': True, 'allow_null': False},
            'fuel_freight_adjustment': {'required': True, 'allow_null': False},
            'fuel_used_per_trip': {'required': True, 'allow_null': False},
            # ระบบเป็นคนใส่เวลาเอง ไม่ให้ client ส่งมาทับ
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            # ฟิลด์ของระบบเวอร์ชัน/การอนุมัติ ระบบกำหนดเองทั้งหมด client ส่งมาไม่ได้
            # ต้องเป็น read_only ด้วยอีกเหตุผลหนึ่ง : unique_together ('root','version')
            # ทำให้ DRF สร้าง UniqueTogetherValidator ซึ่งบังคับให้ส่งทั้งสองช่องมาเสมอ
            # DRF จะข้าม validator นั้นก็ต่อเมื่อฟิลด์ไม่ได้อยู่ในชุดที่เขียนได้
            'root': {'read_only': True},
            'version': {'read_only': True},
            'status': {'read_only': True},
            # effective_date ให้ผู้ใช้กรอกได้ ตั้งวันเริ่มใช้เองตอนสร้าง/ตอนออกใบใหม่
            # ใบที่อนุมัติแล้วแก้ไม่ได้ (กดบันทึกจะกลายเป็นใบใหม่ ค่านี้จึงเป็นของใบใหม่)
            'effective_date': {'required': False, 'allow_null': True},
            'user_created': {'read_only': True},
        }

    @staticmethod
    def _teamLabel(team_pk):
        """แสดงชื่อทีมในข้อความ error ไม่ใช่รหัส คนอ่านจะได้รู้ว่าทีมไหน"""
        if team_pk is None:
            return 'ทุกทีม'
        team = BaseCarTeam.objects.filter(pk=team_pk).first()
        return team.car_team_name if team and team.car_team_name else str(team_pk)

    def validate_teams(self, teams_data):
        """ทีมเดียวกันในเส้นทางเดียวกัน ห้ามมีช่วงน้ำหนักที่ทับกัน

        ถ้าทับกันแปลว่าน้ำหนักค่าเดียวไปเข้าได้สองราคา ระบบเลือกไม่ได้ว่าจะคิดอันไหน
        เคสที่เจอบ่อยคือทีมที่คิดแบบเหมาทุกช่วงอยู่แล้ว (0 ถึง 999999.99)
        แล้วมาเพิ่มช่วงย่อยทับอีก เช่น 35.01-40 คนละราคา แบบนี้ต้องเลือกอย่างใดอย่างหนึ่ง
        """
        by_team = {}
        for team_data in teams_data:
            band = team_data.get('weight_carried')
            if band is None:
                continue
            # team = None คือแถว "ทุกทีม" ก็ต้องไม่ทับกันเองเหมือนกัน
            team = team_data.get('team')
            by_team.setdefault(team.pk if team else None, []).append(band)

        for team_pk, bands in by_team.items():
            for i, first in enumerate(bands):
                for second in bands[i + 1:]:
                    if (first.min_weight <= second.max_weight
                            and second.min_weight <= first.max_weight):
                        raise serializers.ValidationError(
                            'ทีม "%s" มีช่วงน้ำหนักทับกัน : "%s" กับ "%s" '
                            '— ทีมเดียวกันต้องไม่มีช่วงซ้อนกัน ให้ลบออกอันหนึ่ง'
                            % (self._teamLabel(team_pk), first.name, second.name))
        return teams_data

    def validate_fuel_prices(self, fuel_data):
        """ตัดวันทิ้งให้เหลือวันที่ 1 ทุกแถว

        ต้องตัดตรงนี้ ไม่ใช่รอ save() ของโมเดล เพราะฝั่งอ่านจับกลุ่มด้วยค่า month ตรง ๆ
        ถ้าบางแถวเป็นวันที่ 17 เดือนเดียวกันจะแตกเป็นคนละกลุ่ม
        ไม่ต้องกันเดือนซ้ำแล้ว เพราะออกแบบให้ 1 เดือนมีได้หลายแถว (เก็บทุกครั้งที่แก้)
        """
        for fuel in fuel_data:
            month = fuel.get('month')
            if month is not None:
                fuel['month'] = month.replace(day=1)
        return fuel_data

    def _currentUser(self):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return user if user is not None and user.is_authenticated else None

    def _logApproval(self, rate, action, comment, user):
        return InternationalFreightRateApproval.objects.create(
            international_freight_rate=rate, action=action,
            comment=(comment or None), user=user)

    def _autoApprove(self, rate, comment, user):
        """เฟสนี้ยังไม่เปิดหน้าอนุมัติของผู้บริหาร ใบที่ออกมาจึงอนุมัติให้อัตโนมัติ

        ถึงจะอนุมัติเอง ก็ยังเขียนบทสนทนาไว้ครบทั้ง 2 รอบ (ขอ + อนุมัติ)
        พอเปิดหน้าอนุมัติจริง ประวัติจะต่อกันได้เลย ไม่มีช่วงที่ข้อมูลขาด
        แถว approve ตั้ง user = None ไว้ตั้งใจ เพื่อให้แยกออกว่าอันไหนระบบอนุมัติเอง
        """
        self._logApproval(rate, InternationalFreightRateApprovalAction.SUBMIT, comment, user)
        self._logApproval(rate, InternationalFreightRateApprovalAction.APPROVE,
                          'ระบบอนุมัติอัตโนมัติ (ยังไม่เปิดระบบอนุมัติโดยผู้บริหาร)', None)
        rate.submitted_at = timezone.now()
        rate.approved_at = timezone.now()
        rate.save(update_fields=['submitted_at', 'approved_at'])

    @transaction.atomic
    def create(self, validated_data):
        """ใบแรกของเส้นทาง : เวอร์ชัน 1 อนุมัติทันที และมีผลตั้งแต่ต้น

        ที่ต้องมีผลตั้งแต่ต้น (ไม่ใช่เดือนที่กรอก) เพราะข้อมูลการชั่งมีย้อนหลังหลายปี
        แต่แถวอัตราเพิ่งถูกกรอกเข้าระบบ ถ้าใช้เดือนที่กรอก export เดือนเก่าจะหาอัตราไม่เจอ
        """
        teams_data = validated_data.pop('teams', [])
        fuel_data = validated_data.pop('fuel_prices', [])
        comment = validated_data.pop('comment', None)

        # ไม่กรอกวันเริ่มใช้ = ตั้งแต่เริ่มระบบ ครอบคลุมทุกเดือนย้อนหลัง
        # เส้นทางที่เพิ่งบันทึกเข้าระบบมักวิ่งมาก่อนหน้านั้นแล้ว ถ้าตั้งเป็นวันนี้
        # export เดือนเก่าจะหาอัตราไม่เจอ เที่ยวหายทั้งเส้นทาง
        effective_date = (validated_data.pop('effective_date', None)
                          or INTERNATIONAL_FREIGHT_RATE_FIRST_DATE)

        rate = InternationalFreightRate.objects.create(
            version=1,
            status=InternationalFreightRateStatus.APPROVED,
            effective_date=effective_date,
            user_created=self._currentUser(),
            **validated_data)

        for team_data in teams_data:
            InternationalFreightRateTeam.objects.create(international_freight_rate=rate, **team_data)
        # ราคาน้ำมันผูกกับเส้นทาง (root) ใบแรกเป็น root ของตัวเองอยู่แล้ว
        for fuel in fuel_data:
            InternationalFreightRateFuelPrice.objects.create(root=rate.root, **fuel)

        self._autoApprove(rate, comment or 'สร้างเส้นทางใหม่', self._currentUser())
        return rate

    @transaction.atomic
    def update(self, instance, validated_data):
        """แก้ราคา = ออกใบใหม่ทั้งใบ ใบเก่าไม่ถูกแตะ เอกสารเดือนเก่าจึงได้ตัวเลขเดิม

        ยกเว้นใบที่ยังไม่เคยถูกใช้จริง (ร่าง / รออนุมัติ / ไม่อนุมัติ) แก้ทับในแถวเดิมได้เลย
        ไม่งั้นแก้คำผิด 3 รอบจะได้ 3 เวอร์ชันโดยไม่มีประโยชน์

        fuel_prices ไม่เกี่ยวกับเวอร์ชัน เพราะผูกกับเส้นทาง เพิ่มแถวใหม่ต่อท้ายเสมอ
        """
        teams_data = validated_data.pop('teams', None)
        fuel_data = validated_data.pop('fuel_prices', None)
        comment = validated_data.pop('comment', None)

        if instance.status == InternationalFreightRateStatus.APPROVED:
            rate = self._issueNewVersion(instance, validated_data, teams_data, comment)
        else:
            rate = self._editInPlace(instance, validated_data, teams_data, comment)

        if fuel_data is not None:
            # เพิ่มแถวใหม่เสมอ ไม่ทับของเดิม ประวัติการแก้ราคาจึงอยู่ครบทุกครั้ง
            for fuel in fuel_data:
                InternationalFreightRateFuelPrice.objects.create(root=rate.root, **fuel)

        return rate

    def _issueNewVersion(self, instance, validated_data, teams_data, comment=None):
        """copy ใบเดิมทั้งใบแล้วทับด้วยค่าที่ส่งมา ทีมที่ไม่ได้ส่งมาก็ copy ตามไปด้วย"""
        root = instance.root or instance
        last_version = (InternationalFreightRate.objects
                        .filter(root=root)
                        .aggregate(models.Max('version'))['version__max'] or 0)

        rate = InternationalFreightRate(root=root, version=last_version + 1)
        # ยกค่าทุกช่องจากใบเดิมมาก่อน แล้วค่อยทับเฉพาะช่องที่ส่งมาแก้
        for field in ('origin', 'destination', 'base_fuel_price', 'distance', 'payload_weight',
                      'fuel_freight_adjustment', 'fuel_used_per_trip', 'note'):
            setattr(rate, field, getattr(instance, field))
        for attr, value in validated_data.items():
            setattr(rate, attr, value)

        # เฟสนี้ยังไม่มีระบบอนุมัติ ใบใหม่จึงใช้ได้ทันที
        # ไม่กรอกวันเริ่มใช้ = วันนี้ (ต่างจากตอนสร้างใหม่ที่ default เป็น "ตั้งแต่เริ่มระบบ"
        # เพราะอันนี้คือการเปลี่ยนราคา ไม่ควรย้อนไปทับเดือนที่ปิดไปแล้วโดยไม่ตั้งใจ)
        rate.status = InternationalFreightRateStatus.APPROVED
        rate.effective_date = validated_data.get('effective_date') or date.today()
        rate.user_created = self._currentUser()
        rate.save()

        source_teams = teams_data if teams_data is not None else [
            {'team': t.team, 'weight_carried': t.weight_carried, 'freight_rate': t.freight_rate,
             'discount_per_ton': t.discount_per_ton,
             'freight_rate_per_ton_km': t.freight_rate_per_ton_km, 'note': t.note}
            for t in instance.teams.all()
        ]
        for team_data in source_teams:
            InternationalFreightRateTeam.objects.create(international_freight_rate=rate, **team_data)

        self._autoApprove(rate, comment or 'แก้ไขอัตราค่าขนส่ง', self._currentUser())
        return rate

    def _editInPlace(self, instance, validated_data, teams_data, comment=None):
        """ใบที่ยังไม่เคยถูกใช้จริง แก้ทับได้ ไม่ต้องขึ้นเวอร์ชันใหม่"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if teams_data is not None:
            instance.teams.all().delete()
            for team_data in teams_data:
                InternationalFreightRateTeam.objects.create(
                    international_freight_rate=instance, **team_data)

        # ใบที่ยังไม่อนุมัติ แก้แล้วถือเป็นการส่งขออนุมัติใหม่อีกรอบ
        self._logApproval(instance, InternationalFreightRateApprovalAction.SUBMIT,
                          comment or 'แก้ไขแล้วส่งอีกครั้ง', self._currentUser())
        instance.submitted_at = timezone.now()
        instance.status = InternationalFreightRateStatus.PENDING
        instance.save(update_fields=['submitted_at', 'status'])
        return instance
