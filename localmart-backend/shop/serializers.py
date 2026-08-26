from django.utils import timezone
from rest_framework import serializers
from .models import Product, DailyStock
from authentication.models import Vendor,Customer
from .models import Product, DailyStock, Order, OrderItem, PollItem, DailyVote, UserVote,Review,TokenTransaction

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'unit', 'base_price', 'image_url']

    def create(self, validated_data):
        vendor = self.context['request'].user.vendor_profile
        return Product.objects.create(vendor=vendor, **validated_data)

class VendorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    demerit_points = serializers.IntegerField(read_only=True)
    needs_stock_nudge = serializers.BooleanField(read_only=True)
    stock_updated_today = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            'id',
            'user',
            'shop_name',
            'category',
            'locality',
            'pincode',
            'delivery_fee',
            'free_delivery_threshold',
            'is_closed_today',
            'platform_score',
            'email',
            'demerit_points',
            'needs_stock_nudge',
            'stock_updated_today'
        ]

    def get_stock_updated_today(self, obj):
        if not obj.stock_last_updated:
            return False

        return obj.stock_last_updated.date() == timezone.now().date()

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
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ['id', 'shop_name', 'category', 'locality', 'pincode', 'delivery_fee', 'free_delivery_threshold', 'is_closed_today', 'platform_score','stock_last_updated', 'today_stock','average_rating', 'review_count'] 


    def get_today_stock(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        
        stock = DailyStock.objects.filter(product__vendor=obj, date=today)
        stock_last_updated = serializers.DateTimeField(read_only=True) 
        return DailyStockSerializer(stock, many=True).data

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0.0

    # Counts total reviews
    def get_review_count(self, obj):
        return obj.reviews.count()

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    vendor_name = serializers.CharField(source='vendor.shop_name', read_only=True)
    customer_name = serializers.CharField(source='customer.user.first_name', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'vendor', 'vendor_name','customer_name', 'status', 'order_type', 'subtotal','delivery_address' ,'delivery_fee', 'total_amount', 'created_at', 'items']
        

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
    wallet_balance = serializers.SerializerMethodField()  

    class Meta:
        model = Customer
        fields = ['id', 'email', 'name', 'pincode', 'area_name', 'wallet_balance']

    def get_wallet_balance(self, obj):
        from .models import TokenWallet
        wallet, created = TokenWallet.objects.get_or_create(customer=obj)
        return wallet.balance

class PollItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollItem
        fields = ['id', 'name', 'category']

class DailyVoteSerializer(serializers.ModelSerializer):
    
    item_name = serializers.CharField(source='poll_item.name', read_only=True)

    class Meta:
        model = DailyVote
        fields = ['id', 'item_name', 'vote_count', 'pincode']

class ReviewSerializer(serializers.ModelSerializer):
   
    customer_name = serializers.CharField(source='customer.user.first_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'order', 'vendor', 'customer', 'customer_name', 'rating', 'text', 'created_at']
        read_only_fields = ['order', 'vendor', 'customer']

class TokenTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'date']