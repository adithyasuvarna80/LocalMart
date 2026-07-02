from rest_framework import serializers
from .models import User, Vendor, Customer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class VendorRegistrationSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(write_only=True, required=False)
    category = serializers.CharField(write_only=True, required=False)
    locality = serializers.CharField(write_only=True, required=False)
    pincode = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'shop_name', 'category', 'locality', 'pincode']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
      
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            role='VENDOR'
        )
        user.set_password(validated_data['password'])
        user.save()

        Vendor.objects.create(
            user=user,
            shop_name=validated_data.get('shop_name', ''),
            category=validated_data.get('category', 'VEGETABLES'),
        )
        return user

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    pincode = serializers.CharField(write_only=True, required=False)
    area_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'pincode', 'area_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
       
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            role='CUSTOMER'
        )
        user.set_password(validated_data['password'])
        user.save()

        Customer.objects.create(user=user)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
       
        data['role'] = self.user.role
        return data