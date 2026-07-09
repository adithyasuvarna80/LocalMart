from rest_framework import serializers
from .models import Product, DailyStock
from authentication.models import Vendor,Customer
from .models import Product, DailyStock, Order, OrderItem

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
        fields = ['shop_name', 'locality', 'pincode', 'platform_score', 'email','is_closed_today']


class DailyStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit = serializers.CharField(source='product.unit', read_only=True)
    base_price = serializers.DecimalField(source='product.base_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DailyStock
      
        fields = [
            'id', 
            'product', 
            'product_name', 
            'unit', 
            'base_price', 
            'date', 
            'quantity', 
            'is_sold_out'
        ]
        read_only_fields = ['date', 'is_sold_out']

class CustomerShopSerializer(serializers.ModelSerializer):
 
    today_stock = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            'id', 'shop_name', 'category', 'locality', 'delivery_fee', 
            'free_delivery_threshold', 'is_closed_today', 'platform_score', 'today_stock'
        ]

    def get_today_stock(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        
        stock = DailyStock.objects.filter(product__vendor=obj, date=today)
        return DailyStockSerializer(stock, many=True).data

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'vendor', 'vendor_name', 'status', 'order_type', 'subtotal', 'delivery_fee', 'total_amount', 'created_at', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        
        order = Order.objects.create(**validated_data)
        
        
        from django.utils import timezone
        today = timezone.now().date()
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            
            
            stock = DailyStock.objects.filter(product=item_data['product'], date=today).first()
            if stock:
                stock.quantity -= item_data['quantity']
                
               
                if stock.quantity <= 0:
                    stock.quantity = 0
                    stock.is_sold_out = True
                stock.save()
                
        return order
    
class CustomerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = Customer
        fields = ['name', 'email', 'pincode', 'area_name']