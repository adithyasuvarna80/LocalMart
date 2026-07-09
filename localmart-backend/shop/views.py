from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from authentication.models import Vendor 
from .models import Product, DailyStock, Order, OrderItem
from .serializers import ProductSerializer, VendorProfileSerializer, DailyStockSerializer, CustomerShopSerializer, OrderSerializer

from .models import Product, DailyStock
from .serializers import ProductSerializer, VendorProfileSerializer, DailyStockSerializer
from .serializers import CustomerShopSerializer,CustomerProfileSerializer


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile)

class ProductDetailView(generics.DestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile)

class VendorProfileView(generics.RetrieveAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.vendor_profile

# NEW: The Automated Daily Stock View
class DailyStockManageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vendor = request.user.vendor_profile
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        products = Product.objects.filter(vendor=vendor)
        today_stock = []

        for product in products:
            
            stock_entry, created = DailyStock.objects.get_or_create(
                product=product,
                date=today,
                defaults={'quantity': 0.00}
            )
            
            
            if created:
                yesterday_stock = DailyStock.objects.filter(product=product, date=yesterday).first()
                if yesterday_stock:
                    stock_entry.quantity = yesterday_stock.quantity
                    stock_entry.save()
                    
            today_stock.append(stock_entry)

        serializer = DailyStockSerializer(today_stock, many=True)
        return Response(serializer.data)

    def post(self, request):
        
        stock_data = request.data
        for item in stock_data:
            try:
               
                stock_entry = DailyStock.objects.get(
                    id=item['id'], 
                    product__vendor=request.user.vendor_profile
                )
                stock_entry.quantity = item['quantity']
                stock_entry.save() 
            except DailyStock.DoesNotExist:
                continue
                
        return Response({"message": "Daily stock updated successfully!"})
    

class ToggleShopClosedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        vendor = request.user.vendor_profile
        
        vendor.is_closed_today = not vendor.is_closed_today
        vendor.save()
        return Response({"is_closed_today": vendor.is_closed_today, "message": "Shop status updated!"})


class LocalShopsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
       
        if not hasattr(request.user, 'customer_profile'):
            return Response({"error": "Only customers can browse shops."}, status=403)
        
        customer = request.user.customer_profile
        
       
        shops = Vendor.objects.filter(pincode=customer.pincode)
        
        
        serializer = CustomerShopSerializer(shops, many=True)
        return Response(serializer.data)

class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'customer_profile'):
            return Response({"error": "Only customers can place orders."}, status=403)
        
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            
            serializer.save(customer=request.user.customer_profile)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
       
        if hasattr(request.user, 'vendor_profile'):
            orders = Order.objects.filter(vendor=request.user.vendor_profile).order_by('-created_at')
        elif hasattr(request.user, 'customer_profile'):
            orders = Order.objects.filter(customer=request.user.customer_profile).order_by('-created_at')
        else:
            return Response([], status=200)
            
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if hasattr(request.user, 'customer_profile'):
            serializer = CustomerProfileSerializer(request.user.customer_profile)
            return Response(serializer.data)
        return Response({"error": "Not a customer"}, status=400)