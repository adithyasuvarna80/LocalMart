from django.utils import timezone
from rest_framework import serializers
from .models import Product, DailyStock
from authentication.models import Vendor,Customer
from .models import Product, DailyStock, Order, OrderItem, PollItem, DailyVote, UserVote,Review,TokenTransaction
import cloudinary.uploader

class ProductSerializer(serializers.ModelSerializer):

    # Actual uploaded file from Angular.
    # This is NOT stored directly in PostgreSQL.
    image = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True
    )

    # Cloudinary URL stored in Product.image_url
    image_url = serializers.URLField(
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Product

        fields = [
            'id',
            'name',
            'unit',
            'base_price',
            'image',
            'image_url'
        ]


    def validate_image(self, image):

        if not image:
            return image

        # Maximum LocalMart upload size = 5 MB
        max_size = 5 * 1024 * 1024

        if image.size > max_size:
            raise serializers.ValidationError(
                "Product image must be smaller than 5 MB."
            )

        allowed_types = [
            'image/jpeg',
            'image/png',
            'image/webp'
        ]

        content_type = getattr(
            image,
            'content_type',
            None
        )

        if content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only JPG, PNG and WEBP images are allowed."
            )

        return image


    def create(self, validated_data):

        vendor = (
            self.context['request']
            .user
            .vendor_profile
        )

        # Remove image because Product model
        # doesn't contain an actual image field.
        image = validated_data.pop(
            'image',
            None
        )

        image_url = None

        # ------------------------------------------
        # Upload product image to Cloudinary
        # ------------------------------------------

        if image:

            try:

                upload_result = cloudinary.uploader.upload(
                    image,

                    folder=(
                        f"localmart/products/"
                        f"vendor_{vendor.id}"
                    ),

                    resource_type="image"
                )

                image_url = upload_result.get(
                    'secure_url'
                )

            except Exception as exc:

                print(
                    "Cloudinary upload error:",
                    exc
                )

                raise serializers.ValidationError({
                    "image":
                    "Image upload failed. Please try again."
                })


        # ------------------------------------------
        # Create permanent Product
        # ------------------------------------------

        product = Product.objects.create(
            vendor=vendor,
            image_url=image_url,
            **validated_data
        )


        # ------------------------------------------
        # Create today's DailyStock immediately
        # Keeps the multiple-product fix intact
        # ------------------------------------------

        DailyStock.objects.get_or_create(
            product=product,
            date=timezone.now().date(),
            defaults={
                'quantity': 0.00
            }
        )


        return product

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

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    unit = serializers.CharField(
        source='product.unit',
        read_only=True
    )

    base_price = serializers.DecimalField(
        source='product.base_price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    # NEW — Cloudinary product image
    image_url = serializers.URLField(
        source='product.image_url',
        read_only=True,
        allow_null=True
    )


    class Meta:
        model = DailyStock

        fields = [
            'id',
            'product',
            'product_name',
            'unit',
            'base_price',

            # NEW
            'image_url',

            'date',
            'quantity',
            'is_sold_out'
        ]

        read_only_fields = [
            'date',
            'is_sold_out'
        ]

class CustomerShopSerializer(serializers.ModelSerializer):

    today_stock = serializers.SerializerMethodField()

    # Customer review rating /5
    average_rating = serializers.SerializerMethodField()

    # Number of customer reviews
    review_count = serializers.SerializerMethodField()

    # Combined Platform + Customer score /10
    overall_rating = serializers.SerializerMethodField()

    class Meta:
        model = Vendor

        fields = [
            'id',
            'shop_name',
            'category',
            'locality',
            'pincode',
            'delivery_fee',
            'free_delivery_threshold',
            'is_closed_today',

            # Rating information
            'platform_score',
            'average_rating',
            'review_count',
            'overall_rating',

            'stock_last_updated',
            'today_stock'
        ]

    def get_today_stock(self, obj):
        from django.utils import timezone

        today = timezone.now().date()

        stock = DailyStock.objects.filter(
            product__vendor=obj,
            date=today
        )

        return DailyStockSerializer(
            stock,
            many=True
        ).data


    def get_average_rating(self, obj):

        reviews = obj.reviews.all()

        if not reviews.exists():
            return 0.0

        total = sum(
            review.rating
            for review in reviews
        )

        average = total / reviews.count()

        return round(average, 1)


    def get_review_count(self, obj):

        return obj.reviews.count()


    def get_overall_rating(self, obj):
        """
        Overall Rating /10

        Platform Score = already /10
        Customer Rating = /5, therefore multiply by 2

        50% Platform Score
        50% Customer Rating
        """

        platform_score = float(
            obj.platform_score or 0
        )

        reviews = obj.reviews.all()

        # No customer reviews yet:
        # don't unfairly treat "no reviews" as zero stars.
        if not reviews.exists():
            return round(platform_score, 1)

        average_customer_rating = (
            sum(review.rating for review in reviews)
            / reviews.count()
        )

        customer_score_out_of_10 = (
            average_customer_rating * 2
        )

        overall = (
            platform_score +
            customer_score_out_of_10
        ) / 2

        return round(
            min(max(overall, 0.0), 10.0),
            1
        )

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