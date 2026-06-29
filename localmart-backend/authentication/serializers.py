from rest_framework import serializers
from .models import User, Vendor, Customer
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class VendorRegistrationSerializer(serializers.ModelSerializer):
    # Vendor-specific fields mapped to the profile
    shop_name = serializers.CharField(source='vendor_profile.shop_name', required=False)
    category = serializers.CharField(source='vendor_profile.category', required=False)
    locality = serializers.CharField(source='vendor_profile.locality', required=False)
    pincode = serializers.CharField(source='vendor_profile.pincode', required=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'shop_name', 'category', 'locality', 'pincode']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Extract vendor profile data
        vendor_data = validated_data.pop('vendor_profile', {})
        # Create the unified user
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            role='VENDOR',
            password=make_password(validated_data['password'])
        )
        # Create the linked vendor profile
        Vendor.objects.create(user=user, **vendor_data)
        return user


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    # Customer-specific fields mapped to the profile
    pincode = serializers.CharField(source='customer_profile.pincode')
    area_name = serializers.CharField(source='customer_profile.area_name')

    class Meta:
        model = User
        fields = ['email', 'password', 'pincode', 'area_name']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Extract customer profile data
        customer_data = validated_data.pop('customer_profile')
        # Create the unified user
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            role='CUSTOMER',
            password=make_password(validated_data['password'])
        )
        # Create the linked customer profile
        Customer.objects.create(user=user, **customer_data)
        return user
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # This calls the default validation (which handles the email/password check automatically)
        data = super().validate(attrs)
        
        # Add the user's custom role to the JSON response
        data['role'] = self.user.role
        
        return data