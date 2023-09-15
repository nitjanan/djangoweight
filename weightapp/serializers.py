from rest_framework import serializers
from weightapp.models import BaseScoop, BaseMill, Weight, BaseCustomer, BaseStoneType, BaseCarTeam, BaseDriver, BaseCarRegistration, BaseCar, BaseSite
from django.contrib.auth.models import User

class CustomField(serializers.CharField):
    def to_representation(self, obj):
        # Custom logic to represent the field
        return obj.custom_field_value
    
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

class BaseScoopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseScoop
        fields = ('รหัสผู้ตัก', 'ชื่อผู้ตัก')

    # Define custom field names
    รหัสผู้ตัก = serializers.CharField(source='scoop_id')
    ชื่อผู้ตัก = serializers.CharField(source='scoop_name')

class BaseCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCustomer
        fields = '__all__'
        extra_fields = ['customer_id']

class BaseMillSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseMill
        fields = ('รหัสโรงโม่', 'ชื่อโรงโม่')

    # Define custom field names
    รหัสโรงโม่ = serializers.CharField(source='mill_id')
    ชื่อโรงโม่ = serializers.CharField(source='mill_name')

class BaseStoneTypeSerializer(serializers.ModelSerializer):
    รหัสหิน = serializers.CharField(source='base_stone_type_id')
    ชื่อหิน = serializers.CharField(source='base_stone_type_name')

    class Meta:
        model = BaseStoneType
        fields = ('รหัสหิน', 'ชื่อหิน', 'cal_q',)

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
        fields = ('รหัสทีม', 'ชื่อทีม',)

    # Define custom field names
    รหัสทีม = serializers.CharField(source='car_team_id')
    ชื่อทีม = serializers.CharField(source='car_team_name')

class BaseDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDriver
        fields = ('รหัสผู้ขับ', 'ชื่อผู้ขับ',)

    # Define custom field names
    รหัสผู้ขับ = serializers.CharField(source='driver_id')
    ชื่อผู้ขับ = serializers.CharField(source='driver_name')

class BaseCarRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCarRegistration
        fields = ('รหัสทะเบียนรถ', 'ชื่อทะเบียนรถ','ประเภทรถ')

    # Define custom field names
    รหัสทะเบียนรถ = serializers.CharField(source='car_registration_id')
    ชื่อทะเบียนรถ = serializers.CharField(source='car_registration_name')
    ประเภทรถ = serializers.CharField(source='car_type')

class BaseCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseCar
        fields = ('รหัสรถร่วม', 'ชื่อรถร่วม','รหัสทีม')

    # Define custom field names
    รหัสรถร่วม = serializers.CharField(source='car_id')
    ชื่อรถร่วม = serializers.CharField(source='car_name')
    รหัสทีม = serializers.CharField(source='base_car_team.car_team_id')

class BaseSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseSite
        fields = ('รหัสหน้างาน', 'ชื่อหน้างาน','ลูกค้า')

    # Define custom field names
    รหัสหน้างาน = serializers.CharField(source='base_site_id')
    ชื่อหน้างาน = serializers.CharField(source='base_site_name')
    ลูกค้า = serializers.CharField(source='base_customer')
