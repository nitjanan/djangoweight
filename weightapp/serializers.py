from rest_framework import serializers
from weightapp.models import BaseScoop, BaseMill, Weight, BaseCustomer, BaseStoneType, BaseCarTeam, BaseDriver, BaseCarRegistration, BaseCar, BaseSite, BaseJobType, BaseCustomerSite, DeliveryOrder, WeightDelivery, AppRelease, ClientUpdateLog, UserScale, BaseCompanyMapBaseCustomer, InternationalFreightRate, InternationalFreightRateTeam
from django.contrib.auth.models import User
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
            'weight_carried': {'required': True, 'allow_null': False, 'allow_blank': False},
        }


class InternationalFreightRateSerializer(serializers.ModelSerializer):
    teams = InternationalFreightRateTeamSerializer(many=True, required=False)

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
            'average_fuel_price': {'required': True, 'allow_null': False},
            # ระบบเป็นคนใส่เวลาเอง ไม่ให้ client ส่งมาทับ
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def create(self, validated_data):
        # สร้างรายการหลัก + ทีมทั้งหมดในครั้งเดียว
        teams_data = validated_data.pop('teams', [])
        rate = InternationalFreightRate.objects.create(**validated_data)
        for team_data in teams_data:
            InternationalFreightRateTeam.objects.create(international_freight_rate=rate, **team_data)
        return rate

    def update(self, instance, validated_data):
        # teams : ถ้าส่งมา จะแทนที่ของเดิมทั้งชุด (ลบทิ้งแล้วสร้างใหม่ตามที่ส่งมา)
        # เพราะฟอร์มฝั่งหน้าเว็บส่งรายการทีมมาทั้งหมดทุกครั้งอยู่แล้ว
        # ถ้าไม่ส่งคีย์ teams มาเลย = ไม่แตะทีมเดิม (ใช้กับ PATCH ที่แก้เฉพาะข้อมูลหลัก)
        teams_data = validated_data.pop('teams', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if teams_data is not None:
            instance.teams.all().delete()
            for team_data in teams_data:
                InternationalFreightRateTeam.objects.create(international_freight_rate=instance, **team_data)

        return instance
