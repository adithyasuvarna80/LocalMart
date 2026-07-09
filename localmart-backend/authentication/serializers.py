from rest_framework import serializers
from .models import User, Vendor, Customer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class VendorRegistrationSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(write_only=True, required=False)
    category = serializers.CharField(write_only=True, required=False)
    locality = serializers.CharField(write_only=True, required=False)
    pincode = serializers.CharField(write_only=True, required=False)
    
    # 1. ADD THESE TWO MISSING FIELDS:
    delivery_fee = serializers.DecimalField(write_only=True, required=False, max_digits=6, decimal_places=2)
    free_delivery_threshold = serializers.DecimalField(write_only=True, required=False, max_digits=6, decimal_places=2)

    class Meta:
        model = User
        # 2. Add them to the fields array
        fields = ['email', 'password', 'shop_name', 'category', 'locality', 'pincode', 'delivery_fee', 'free_delivery_threshold']

    def create(self, validated_data):
        user = User(
            username=validated_data['email'], # Keeping our silver-bullet fix!
            email=validated_data['email'],
            role='VENDOR'
        )
        user.set_password(validated_data['password'])
        user.save()

        Vendor.objects.create(
            user=user,
            shop_name=validated_data.get('shop_name', ''),
            category=validated_data.get('category', 'VEGETABLES'),
            locality=validated_data.get('locality', ''),
            pincode=validated_data.get('pincode', ''),
            # 3. Use .get() to safely pull the numbers without ever throwing a KeyError
            delivery_fee=validated_data.get('delivery_fee', 0.00),
            free_delivery_threshold=validated_data.get('free_delivery_threshold', 0.00)
        )
        return user

class CustomerRegistrationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    pincode = serializers.CharField(write_only=True)
    area_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'name', 'pincode', 'area_name']

    def create(self, validated_data):
        user = User(
            username=validated_data['email'], # <-- THE MAGIC FIX: Satisfies the DB constraint!
            email=validated_data['email'],
            first_name=validated_data.get('name', ''), 
            role='CUSTOMER'
        )
        user.set_password(validated_data['password'])
        user.save()

        Customer.objects.create(
            user=user,
            pincode=validated_data['pincode'],
            area_name=validated_data['area_name']
        )
        return user
       

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
       
        data['role'] = self.user.role
        return data