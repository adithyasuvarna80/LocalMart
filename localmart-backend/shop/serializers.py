from rest_framework import serializers
from .models import Product
from authentication.models import Vendor 

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'unit', 'base_price', 'image_url']

    def create(self, validated_data):
        vendor = self.context['request'].user.vendor_profile
        return Product.objects.create(vendor=vendor, **validated_data)


class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['shop_name', 'locality', 'pincode', 'platform_score']

class VendorProfileSerializer(serializers.ModelSerializer):
    
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Vendor
        fields = ['shop_name', 'locality', 'pincode', 'platform_score', 'email']