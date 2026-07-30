from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from authentication.models import Vendor 

from .serializers import ProductSerializer, VendorProfileSerializer, DailyStockSerializer
from .serializers import CustomerShopSerializer,CustomerProfileSerializer

from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, DailyStock, Order, OrderItem, PollItem, DailyVote, UserVote,Review
from .serializers import (
    ProductSerializer, VendorProfileSerializer, DailyStockSerializer, 
    CustomerShopSerializer, CustomerProfileSerializer, OrderSerializer,
    PollItemSerializer, DailyVoteSerializer,ReviewSerializer
)


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

        vendor = request.user.vendor_profile
        vendor.stock_last_updated = timezone.now()
        vendor.save()
                
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
        
       
        shops = Vendor.objects.filter(pincode=customer.pincode).order_by('is_closed_today', 'shop_name')
        
        
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
    
class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not hasattr(request.user, 'vendor_profile'):
            return Response({"error": "Only vendors can update order status."}, status=403)

        try:
            order = Order.objects.get(pk=pk, vendor=request.user.vendor_profile)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=404)

        new_status = request.data.get('status')
        current_status = order.status

        
        valid_transitions = {
            'PENDING': ['ACCEPTED', 'REJECTED'],
            'ACCEPTED': ['READY'],
            'READY': ['COMPLETED']
        }

        if new_status not in valid_transitions.get(current_status, []):
            return Response({"error": f"Invalid transition from {current_status} to {new_status}"}, status=400)

        order.status = new_status
        order.save()
        return Response({"message": "Order status updated successfully", "status": order.status})
    
class CustomerConfirmDeliveryView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not hasattr(request.user, 'customer_profile'):
            return Response({"error": "Only customers can confirm delivery."}, status=403)

        try:
            order = Order.objects.get(pk=pk, customer=request.user.customer_profile)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=404)

        if order.status != 'READY':
            return Response({"error": "Order must be READY to be confirmed."}, status=400)

        order.status = 'COMPLETED'
        order.save()
        return Response({"message": "Delivery confirmed successfully", "status": order.status})
    
class CustomerPollView(APIView):
    permission_classes = [AllowAny] 

    def get(self, request):
        # Auto-detect area if logged in, otherwise default to 000000
        pincode = '000000'
        if request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            pincode = request.user.customer_profile.pincode
            
        items = PollItem.objects.all()
        data = PollItemSerializer(items, many=True).data
        today = timezone.now().date()
        
        # Attach live vote counts for this specific area
        for item in data:
            dv = DailyVote.objects.filter(poll_item_id=item['id'], pincode=pincode, date=today).first()
            item['vote_count'] = dv.vote_count if dv else 0
            
        return Response(data)

    def post(self, request):
        pincode = request.data.get('pincode', '000000')
        item_ids = request.data.get('item_ids', [])

       
        customer_profile = None
        if request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            customer_profile = request.user.customer_profile
            
        session_id = request.META.get('HTTP_X_SESSION_ID', 'guest_default_session')
        today = timezone.now().date()

        
        if customer_profile:
            old_votes = UserVote.objects.filter(customer=customer_profile, date=today)
        else:
            old_votes = UserVote.objects.filter(session_id=session_id, date=today)

        for uv in old_votes:
            for item in uv.voted_items.all():
                dv = DailyVote.objects.filter(pincode=pincode, poll_item=item, date=today).first()
                if dv and dv.vote_count > 0:
                    dv.vote_count -= 1
                    dv.save()
        old_votes.delete()

        
        new_vote = UserVote.objects.create(customer=customer_profile, session_id=session_id, date=today)
        for item_id in item_ids:
            try:
                item = PollItem.objects.get(id=item_id)
                new_vote.voted_items.add(item)
                dv, created = DailyVote.objects.get_or_create(pincode=pincode, poll_item=item, date=today)
                dv.vote_count += 1
                dv.save()
            except PollItem.DoesNotExist:
                pass

        return Response({"message": "Votes recorded successfully!"})


class VendorPollChartDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'vendor_profile'):
            return Response({"error": "Only vendors can view chart data."}, status=403)

        today = timezone.now().date()
        # Grab the vendor's specific area
        vendor_pincode = request.user.vendor_profile.pincode 
        
        # Filter strictly by the vendor's area
        votes = DailyVote.objects.filter(date=today, pincode=vendor_pincode).order_by('-vote_count')
        return Response(DailyVoteSerializer(votes, many=True).data)


class SubmitReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order')
        
        # Ensure the order exists, belongs to this customer, and is actually COMPLETED
        order = Order.objects.filter(id=order_id, customer=request.user.customer_profile, status='COMPLETED').first()
        
        if not order:
            return Response({"error": "Valid completed order not found."}, status=404)

        # Double check to prevent duplicate reviews (OneToOneField also backs this up)
        if hasattr(order, 'review'):
            return Response({"error": "You have already reviewed this order."}, status=400)

        # Create and save the review
        Review.objects.create(
            order=order,
            vendor=order.vendor,
            customer=request.user.customer_profile,
            rating=request.data.get('rating', 5),
            text=request.data.get('text', '')
        )
        return Response({"message": "Review submitted successfully!"})

class VendorReviewsListView(APIView):
    # Anyone can read reviews
    permission_classes = [AllowAny] 

    def get(self, request, vendor_id):
        # Fetch all reviews for this specific vendor, newest first
        reviews = Review.objects.filter(vendor_id=vendor_id).order_by('-created_at')
        return Response(ReviewSerializer(reviews, many=True).data)