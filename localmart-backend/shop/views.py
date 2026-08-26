from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from authentication.models import Vendor 
from django.db.models import Case, When, Value, IntegerField

from .serializers import ProductSerializer, VendorProfileSerializer, DailyStockSerializer
from .serializers import CustomerShopSerializer,CustomerProfileSerializer

from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, DailyStock, Order, OrderItem, PollItem, DailyVote, UserVote,Review,TokenWallet, TokenTransaction
from .serializers import (
    ProductSerializer, VendorProfileSerializer, DailyStockSerializer, 
    CustomerShopSerializer, CustomerProfileSerializer, OrderSerializer,
    PollItemSerializer, DailyVoteSerializer,ReviewSerializer,TokenTransactionSerializer
)
from decimal import Decimal
from django.db import transaction




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
        
        # Pre-fill yesterday's stock levels for today if missing [5]
        stock_exists = DailyStock.objects.filter(product__vendor=vendor, date=today).exists()
        if not stock_exists:
            products = Product.objects.filter(vendor=vendor)
            for product in products:
                latest_stock = DailyStock.objects.filter(product=product).order_by('-date').first()
                qty = latest_stock.quantity if latest_stock else 0.00
                DailyStock.objects.create(product=product, date=today, quantity=qty)
        
        stock_items = DailyStock.objects.filter(product__vendor=vendor, date=today)
        serializer = DailyStockSerializer(stock_items, many=True)
        return Response(serializer.data)

 def post(self, request):
    vendor = request.user.vendor_profile
    updated_any = False

    for item in request.data:
        try:
            stock_id = item.get('id')
            qty = item.get('quantity', 0.00)
            price = item.get('base_price')

            stock_record = DailyStock.objects.get(
                id=stock_id,
                product__vendor=vendor
            )

            stock_record.quantity = float(qty)
            stock_record.is_sold_out = (stock_record.quantity <= 0)
            stock_record.save()

            if price is not None:
                product = stock_record.product
                product.base_price = float(price)
                product.save()

            updated_any = True

        except (DailyStock.DoesNotExist, ValueError, TypeError):
            continue

    if not updated_any:
        return Response(
            {"error": "No stock records were successfully updated."},
            status=400
        )

    vendor.stock_last_updated = timezone.now()
    vendor.needs_stock_nudge = False
    vendor.save()

    return Response({
        "message": "Stock quantities and daily rates successfully updated!"
    })
    

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
        user = request.user
        
        # 1. Get the customer's pincode to filter shops hyperlocally
        try:
            customer_profile = user.customer_profile
            pincode = getattr(customer_profile, 'pincode', None)
        except AttributeError:
            return Response({"error": "User does not have an active customer profile"}, status=400)
            
        if not pincode:
            return Response({"error": "Pincode is missing for this customer profile"}, status=400)

        # 2. Query and dynamically annotate vendors based on demerit tiers & open status
        shops = Vendor.objects.filter(pincode=pincode).annotate(
            visibility_tier=Case(
                # Rule 1: Closed shops go to the absolute bottom (Tier 4)
                When(is_closed_today=True, then=Value(4)),
                # Rule 2: Open shops with 10+ demerit points (Tier 3)
                When(demerit_points__gte=10, then=Value(3)),
                # Rule 3: Open shops with 6 to 9 demerit points (Tier 2)
                When(demerit_points__range=(6, 9), then=Value(2)),
                # Rule 4: Open shops with 3 to 5 demerit points (Tier 1)
                When(demerit_points__range=(3, 5), then=Value(1)),
                # Rule 5: Open shops with 0 to 2 demerit points (Tier 0 - Normal / Top)
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by(
            'visibility_tier',          # Sort by visibility tiers (Tier 0 first, Tier 4 last)
            '-platform_score',          # Tie-breaker 1: prioritize higher platform scores
            'shop_name'                 # Tie-breaker 2: alphabetical sorting
        )

        serializer = CustomerShopSerializer(shops, many=True)
        return Response(serializer.data)


class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # 1. Verify user role first to prevent AttributeErrors
        if not hasattr(request.user, 'customer_profile'):
            return Response({"error": "Only customers can place orders."}, status=403)
            
        customer = request.user.customer_profile
        data = request.data
        
        vendor_id = data.get('vendor')
        order_type = data.get('order_type')
        subtotal = float(data.get('subtotal', 0.00))
        delivery_fee = float(data.get('delivery_fee', 0.00))
        tokens_used = int(data.get('tokens_used', 0))
        delivery_address = data.get('delivery_address', '')

        # 2. Process Token Wallet Deductions
        discount_amount = 0.00
        if tokens_used > 0:
            wallet, created = TokenWallet.objects.get_or_create(customer=customer)
            if wallet.balance < tokens_used:
                return Response({"error": "Insufficient token balance"}, status=400)
            
            # Redemption calculation: 50 tokens = ₹5 discount
            discount_amount = float(tokens_used) * 0.10
            
            # Deduct tokens and write the transaction ledger
            wallet.balance -= tokens_used
            wallet.save()
            
            TokenTransaction.objects.create(
                customer=customer,
                amount=-tokens_used,
                transaction_type='REDEMPTION',
                description=f"Redeemed {tokens_used} tokens for ₹{discount_amount:.2f} discount at checkout."
            )
            
        # 3. Calculate Final Checkout Total
        total_amount = max(0.00, subtotal + delivery_fee - discount_amount)
        
        # 4. Save the single order cleanly to your database
        order = Order.objects.create(
            customer=customer,
            vendor_id=vendor_id,
            order_type=order_type,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            delivery_address=delivery_address,
            status='PENDING'
        )
        
        # 5. Save items & deduct stock level quantities
        for item in data.get('items', []):
            product_id = item.get('product')
            quantity = float(item.get('quantity'))
            price = float(item.get('price'))
            
            OrderItem.objects.create(
                order=order, 
                product_id=product_id, 
                quantity=quantity, 
                price=price
            )
            
            # Real-time stock decrement
            today = timezone.now().date()
            try:
                stock = DailyStock.objects.get(product_id=product_id, date=today)
                stock.quantity = max(0.00, float(stock.quantity) - quantity)
                stock.is_sold_out = (stock.quantity <= 0)
                stock.save()
            except DailyStock.DoesNotExist:
                pass
                
        # 6. Serialize the successfully created order and return it!
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=201)

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
        
        
        order = Order.objects.filter(id=order_id, customer=request.user.customer_profile, status='COMPLETED').first()
        
        if not order:
            return Response({"error": "Valid completed order not found."}, status=404)

        
        if hasattr(order, 'review'):
            return Response({"error": "You have already reviewed this order."}, status=400)

        
        Review.objects.create(
            order=order,
            vendor=order.vendor,
            customer=request.user.customer_profile,
            rating=request.data.get('rating', 5),
            text=request.data.get('text', '')
        )
        return Response({"message": "Review submitted successfully!"})

class VendorReviewsListView(APIView):
   
    permission_classes = [AllowAny] 

    def get(self, request, vendor_id):
      
        reviews = Review.objects.filter(vendor_id=vendor_id).order_by('-created_at')
        return Response(ReviewSerializer(reviews, many=True).data)

class CustomerWalletHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = request.user.customer_profile
        wallet, created = TokenWallet.objects.get_or_create(customer=customer)
        transactions = TokenTransaction.objects.filter(customer=customer).order_by('-date')
        
        serializer = TokenTransactionSerializer(transactions, many=True)
        return Response({
            "wallet_balance": wallet.balance,
            "transactions": serializer.data
        })