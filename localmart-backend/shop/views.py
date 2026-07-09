from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import Product, DailyStock
from .serializers import ProductSerializer, VendorProfileSerializer, DailyStockSerializer

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
            # Get or create a stock entry for today
            stock_entry, created = DailyStock.objects.get_or_create(
                product=product,
                date=today,
                defaults={'quantity': 0.00}
            )
            
            # Automated Pre-fill Logic: Copy yesterday's stock if today is a new entry
            if created:
                yesterday_stock = DailyStock.objects.filter(product=product, date=yesterday).first()
                if yesterday_stock:
                    stock_entry.quantity = yesterday_stock.quantity
                    stock_entry.save()
                    
            today_stock.append(stock_entry)

        serializer = DailyStockSerializer(today_stock, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Bulk update stock quantities sent from Angular
        stock_data = request.data
        for item in stock_data:
            try:
                # Securely ensure the vendor can only update their own products
                stock_entry = DailyStock.objects.get(
                    id=item['id'], 
                    product__vendor=request.user.vendor_profile
                )
                stock_entry.quantity = item['quantity']
                stock_entry.save() # This triggers the automatic "Sold Out" logic!
            except DailyStock.DoesNotExist:
                continue
                
        return Response({"message": "Daily stock updated successfully!"})
    

class ToggleShopClosedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        vendor = request.user.vendor_profile
        # Flip the status from True to False, or False to True
        vendor.is_closed_today = not vendor.is_closed_today
        vendor.save()
        return Response({"is_closed_today": vendor.is_closed_today, "message": "Shop status updated!"})