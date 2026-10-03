from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from rest_framework import generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import Vendor

from .cron import calculate_vendor_platform_score
from .models import (
    DailyStock,
    DailyVote,
    Order,
    OrderItem,
    PollItem,
    Product,
    Review,
    StockUpdateLog,
    TokenTransaction,
    TokenWallet,
    UserVote,
)
from .serializers import (
    CustomerProfileSerializer,
    CustomerShopSerializer,
    DailyStockSerializer,
    DailyVoteSerializer,
    OrderSerializer,
    PollItemSerializer,
    ProductSerializer,
    ReviewSerializer,
    TokenTransactionSerializer,
    VendorProfileSerializer,
)



class ProductListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = ProductSerializer

    permission_classes = [
        IsAuthenticated
    ]

    # Allows:
    # FormData with image
    # normal form data
    # existing JSON requests
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser
    ]


    def get_queryset(self):

        return Product.objects.filter(
            vendor=self.request.user.vendor_profile
        )

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
    today = timezone.localdate()

    # Get every product belonging to this vendor
    products = Product.objects.filter(vendor=vendor)

    # IMPORTANT:
    # Check today's DailyStock PER PRODUCT,
    # not once for the whole shop.
    for product in products:

        stock_exists = DailyStock.objects.filter(
            product=product,
            date=today
        ).exists()

        if not stock_exists:

            # Get the most recent stock BEFORE today.
            # This keeps your existing pre-fill feature.
            latest_stock = DailyStock.objects.filter(
                product=product,
                date__lt=today
            ).order_by('-date').first()

            qty = (
                latest_stock.quantity
                if latest_stock
                else 0.00
            )

            DailyStock.objects.create(
                product=product,
                date=today,
                quantity=qty
            )

    # Now every product is guaranteed to have
    # today's DailyStock record.
    stock_items = DailyStock.objects.filter(
        product__vendor=vendor,
        date=today
    ).order_by('product__name')

    serializer = DailyStockSerializer(
        stock_items,
        many=True
    )

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

    StockUpdateLog.objects.update_or_create(
    vendor=vendor,
    date=timezone.localdate()
)   
    calculate_vendor_platform_score(vendor)

    return Response({
    "message": "Stock quantities and daily rates successfully updated!",
    "platform_score": vendor.platform_score
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

        # -------------------------------------------------
        # 1. Only customers can place orders
        # -------------------------------------------------

        if not hasattr(request.user, 'customer_profile'):
            return Response(
                {"error": "Only customers can place orders."},
                status=403
            )

        customer = request.user.customer_profile
        data = request.data

        # -------------------------------------------------
        # 2. Validate vendor
        # -------------------------------------------------

        try:
            vendor_id = int(data.get('vendor'))
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid vendor."},
                status=400
            )

        vendor = Vendor.objects.filter(
            id=vendor_id
        ).first()

        if not vendor:
            return Response(
                {"error": "Vendor not found."},
                status=404
            )

        # LocalMart is locality-first
        if vendor.pincode != customer.pincode:
            return Response(
                {
                    "error":
                    "You can only order from shops in your registered pincode."
                },
                status=400
            )

        if vendor.is_closed_today:
            return Response(
                {"error": "This shop is closed today."},
                status=400
            )

        # -------------------------------------------------
        # 3. Validate order type and address
        # -------------------------------------------------

        order_type = str(
            data.get('order_type', '')
        ).upper()

        if order_type not in ['PICKUP', 'DELIVERY']:
            return Response(
                {"error": "Invalid order type."},
                status=400
            )

        delivery_address = str(
            data.get('delivery_address') or ''
        ).strip()

        if order_type == 'DELIVERY' and not delivery_address:
            return Response(
                {
                    "error":
                    "Delivery address is required for home delivery."
                },
                status=400
            )

        if order_type == 'PICKUP':
            delivery_address = ''

        # -------------------------------------------------
        # 4. Validate cart
        # -------------------------------------------------

        items = data.get('items', [])

        if not isinstance(items, list) or len(items) == 0:
            return Response(
                {"error": "Your cart is empty."},
                status=400
            )

        # Combine duplicate product IDs if somebody
        # manipulates the API request manually.
        requested_products = {}

        try:
            for item in items:

                product_id = int(
                    item.get('product')
                )

                quantity = Decimal(
                    str(item.get('quantity'))
                )

                if quantity <= 0:
                    return Response(
                        {
                            "error":
                            "Product quantity must be greater than zero."
                        },
                        status=400
                    )

                requested_products[product_id] = (
                    requested_products.get(
                        product_id,
                        Decimal('0')
                    ) + quantity
                )

        except (
            TypeError,
            ValueError,
            InvalidOperation
        ):
            return Response(
                {"error": "Invalid product or quantity."},
                status=400
            )

        # -------------------------------------------------
        # 5. Validate today's real stock
        # -------------------------------------------------

        today = timezone.localdate()

        validated_items = []

        subtotal = Decimal('0.00')

        for product_id, quantity in requested_products.items():

            product = Product.objects.filter(
                id=product_id,
                vendor=vendor
            ).first()

            if not product:
                return Response(
                    {
                        "error":
                        "One of the selected products does not belong to this shop."
                    },
                    status=400
                )

            # Lock stock row while this order is being created.
            # Prevents two simultaneous orders from overselling.
            stock = DailyStock.objects.select_for_update().filter(
                product=product,
                date=today
            ).first()

            if not stock:
                return Response(
                    {
                        "error":
                        f"{product.name} does not have stock available for today."
                    },
                    status=400
                )

            available_quantity = Decimal(
                str(stock.quantity)
            )

            if (
                stock.is_sold_out
                or quantity > available_quantity
            ):
                return Response(
                    {
                        "error":
                        f"Only {available_quantity} "
                        f"{product.unit} of {product.name} is available."
                    },
                    status=400
                )

            # IMPORTANT:
            # Price comes from PostgreSQL, NOT Angular.
            price = Decimal(
                str(product.base_price)
            )

            subtotal += (
                price * quantity
            )

            validated_items.append(
                (
                    product,
                    stock,
                    quantity,
                    price
                )
            )

        subtotal = subtotal.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # -------------------------------------------------
        # 6. Calculate delivery fee on backend
        # -------------------------------------------------

        if order_type == 'PICKUP':

            delivery_fee = Decimal('0.00')

        else:

            free_delivery_threshold = Decimal(
                str(
                    vendor.free_delivery_threshold
                    or 0
                )
            )

            vendor_delivery_fee = Decimal(
                str(
                    vendor.delivery_fee
                    or 0
                )
            )

            if free_delivery_threshold > 0 and subtotal >= free_delivery_threshold:
                delivery_fee = Decimal('0.00')
            else:
                delivery_fee = vendor_delivery_fee

        delivery_fee = delivery_fee.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # -------------------------------------------------
        # 7. Validate token redemption
        # -------------------------------------------------

        try:
            tokens_used = int(
                data.get('tokens_used', 0)
            )
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid token amount."},
                status=400
            )

        if tokens_used < 0:
            return Response(
                {
                    "error":
                    "Token amount cannot be negative."
                },
                status=400
            )

        gross_total = (
            subtotal + delivery_fee
        )

        discount_amount = (
            Decimal(tokens_used)
            * Decimal('0.10')
        )

        if discount_amount > gross_total:
            return Response(
                {
                    "error":
                    "Token discount cannot exceed the order amount."
                },
                status=400
            )

        wallet = None

        if tokens_used > 0:

            wallet = (
                TokenWallet.objects
                .select_for_update()
                .filter(customer=customer)
                .first()
            )

            if (
                not wallet
                or wallet.balance < tokens_used
            ):
                return Response(
                    {
                        "error":
                        "Insufficient token balance."
                    },
                    status=400
                )

        # -------------------------------------------------
        # 8. Final total calculated ONLY by backend
        # -------------------------------------------------

        total_amount = (
            gross_total - discount_amount
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # -------------------------------------------------
        # 9. Create order
        # -------------------------------------------------

        order = Order.objects.create(
            customer=customer,
            vendor=vendor,
            order_type=order_type,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            delivery_address=delivery_address,
            status='PENDING'
        )

        # -------------------------------------------------
        # 10. Create order items and deduct stock
        # -------------------------------------------------

        for (
            product,
            stock,
            quantity,
            price
        ) in validated_items:

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )

            stock.quantity = (
                Decimal(str(stock.quantity))
                - quantity
            )

            # DailyStock.save() already maintains
            # is_sold_out based on quantity.
            stock.save()

        # -------------------------------------------------
        # 11. Deduct wallet tokens
        # -------------------------------------------------

        if tokens_used > 0 and wallet:

            wallet.balance -= tokens_used
            wallet.save(
                update_fields=['balance']
            )

            TokenTransaction.objects.create(
                customer=customer,
                amount=-tokens_used,
                transaction_type='REDEMPTION',
                description=(
                    f"Redeemed {tokens_used} tokens "
                    f"for ₹{discount_amount:.2f} "
                    f"discount at checkout."
                )
            )

        # -------------------------------------------------
        # 12. Return final server-calculated order
        # -------------------------------------------------

        serializer = OrderSerializer(order)

        return Response(
            serializer.data,
            status=201
        )

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
}

        if new_status not in valid_transitions.get(current_status, []):
            return Response({"error": f"Invalid transition from {current_status} to {new_status}"}, status=400)

        order.status = new_status
        order.save()

        calculate_vendor_platform_score(order.vendor)

        return Response({
    "message": "Order status updated successfully",
    "status": order.status,
    "platform_score": order.vendor.platform_score
})
    
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
        calculate_vendor_platform_score(order.vendor)
        return Response({"message": "Delivery confirmed successfully", "status": order.status,"platform_score": order.vendor.platform_score
})
    
class CustomerPollView(APIView):
    permission_classes = [AllowAny] 

    def get(self, request):
        # Auto-detect area if logged in, otherwise default to 000000
        pincode = '000000'
        if request.user.is_authenticated and hasattr(request.user, 'customer_profile'):
            pincode = request.user.customer_profile.pincode
            
        items = PollItem.objects.all()
        data = PollItemSerializer(items, many=True).data
        today = timezone.localdate()
        
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
        today = timezone.localdate()

        
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

        today = timezone.localdate()
        # Grab the vendor's specific area
        vendor_pincode = request.user.vendor_profile.pincode 
        
        # Filter strictly by the vendor's area
        votes = DailyVote.objects.filter(date=today, pincode=vendor_pincode).order_by('-vote_count')
        return Response(DailyVoteSerializer(votes, many=True).data)


class SubmitReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if not hasattr(request.user, 'customer_profile'):
            return Response(
                {"error": "Only customers can submit reviews."},
                status=403
            )

        order_id = request.data.get('order')

        order = Order.objects.filter(
            id=order_id,
            customer=request.user.customer_profile,
            status='COMPLETED'
        ).first()

        if not order:
            return Response(
                {"error": "Valid completed order not found."},
                status=404
            )

        if hasattr(order, 'review'):
            return Response(
                {"error": "You have already reviewed this order."},
                status=400
            )

        # ---------------------------------------------
        # Validate rating
        # ---------------------------------------------

        try:
            rating = int(request.data.get('rating', 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "Rating must be a number between 1 and 5."},
                status=400
            )

        if rating < 1 or rating > 5:
            return Response(
                {"error": "Rating must be between 1 and 5 stars."},
                status=400
            )

        review = Review.objects.create(
            order=order,
            vendor=order.vendor,
            customer=request.user.customer_profile,
            rating=rating,
            text=request.data.get('text', '')
        )

        return Response({
            "message": "Review submitted successfully!",
            "rating": review.rating
        }, status=201)
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