from rest_framework import serializers
from .models import Product, DailyStock
from authentication.models import Vendor

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'unit', 'base_price', 'image_url']

    def create(self, validated_data):
        vendor = self.context['request'].user.vendor_profile
        return Product.objects.create(vendor=vendor, **validated_data)

class VendorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Vendor
        fields = ['shop_name', 'locality', 'pincode', 'platform_score', 'email']

# NEW: Serializer for the Daily Stock Gate
class DailyStockSerializer(serializers.ModelSerializer):
    # Fetch details from the related Product model so Angular can display names easily
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit = serializers.CharField(source='product.unit', read_only=True)

    class Meta:
        model = DailyStock
        fields = ['id', 'product', 'product_name', 'unit', 'date', 'quantity', 'is_sold_out','is_closed_today']
        read_only_fields = ['date', 'is_sold_out']