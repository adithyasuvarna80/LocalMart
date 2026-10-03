from django.utils import timezone
from datetime import timedelta
from authentication.models import Vendor
from .models import Order, DailyStock
import random
import random
from datetime import timedelta

from django.utils import timezone

from authentication.models import Customer, Vendor

from .models import (
    Order,
    StockUpdateLog,
    TokenTransaction,
    TokenWallet,
    UserVote,
)

def calculate_vendor_platform_score(vendor):
    """
    Calculate one vendor's Platform Score out of 10.

    Components:
    Stock consistency  = 30%
    Acceptance rate    = 25%
    Delivery completion= 25%
    Demerit behaviour  = 20%
    """

    today =timezone.localdate()

    # INCLUDING today = exactly 30 calendar dates
    start_date = today - timedelta(days=29)

    # -------------------------------------------------
    # 1. STOCK UPDATE CONSISTENCY — 30%
    # -------------------------------------------------

    stock_days = StockUpdateLog.objects.filter(
        vendor=vendor,
        date__range=(start_date, today)
    ).values('date').distinct().count()

    stock_ratio = min(stock_days / 30.0, 1.0)

    stock_score = stock_ratio * 3.0


    # -------------------------------------------------
    # Orders belonging to the last 30 days only
    # -------------------------------------------------

    recent_orders = Order.objects.filter(
        vendor=vendor,
        created_at__date__range=(start_date, today)
    )


    # -------------------------------------------------
    # 2. ORDER ACCEPTANCE RATE — 25%
    # -------------------------------------------------

    accepted_orders = recent_orders.filter(
        status__in=['ACCEPTED', 'READY', 'COMPLETED']
    ).count()

    rejected_orders = recent_orders.filter(
        status='REJECTED'
    ).count()

    # PENDING orders are deliberately NOT counted.
    decided_orders = accepted_orders + rejected_orders

    if decided_orders > 0:
        acceptance_rate = accepted_orders / decided_orders
        acceptance_score = acceptance_rate * 2.5
    else:
        # Vendor should not be punished simply because
        # nobody has placed/decided an order yet.
        acceptance_score = 2.5


    # -------------------------------------------------
    # 3. DELIVERY COMPLETION RATE — 25%
    # -------------------------------------------------

    accepted_deliveries = recent_orders.filter(
        order_type='DELIVERY',
        status__in=['ACCEPTED', 'READY', 'COMPLETED']
    )

    total_accepted_deliveries = accepted_deliveries.count()

    completed_deliveries = accepted_deliveries.filter(
        status='COMPLETED'
    ).count()

    if total_accepted_deliveries > 0:
        delivery_rate = (
            completed_deliveries /
            total_accepted_deliveries
        )

        delivery_score = delivery_rate * 2.5
    else:
        # No delivery orders = no delivery penalty
        delivery_score = 2.5


    # -------------------------------------------------
    # 4. DEMERIT SCORE — 20%
    # -------------------------------------------------

    # 0 demerits  -> 2.0
    # 1 demerit   -> 1.8
    # 5 demerits  -> 1.0
    # 10+         -> 0.0

    demerit_score = max(
        0.0,
        10.0 - float(vendor.demerit_points)
    ) * 0.20


    # -------------------------------------------------
    # FINAL SCORE /10
    # -------------------------------------------------

    final_score = (
        stock_score +
        acceptance_score +
        delivery_score +
        demerit_score
    )

    final_score = round(
        min(max(final_score, 0.0), 10.0),
        1
    )

    vendor.platform_score = final_score

    vendor.save(
        update_fields=['platform_score']
    )

    return final_score


def calculate_platform_scores():
    """
    Recalculate Platform Score for every vendor.
    """

    for vendor in Vendor.objects.all():
        calculate_vendor_platform_score(vendor)

    print(
        f"[{timezone.now()}] "
        f"Successfully updated platform scores for all vendors."
    )

def apply_stock_nudges():
    """12-Hour Soft Nudge: Flags vendors who haven't updated stock recently."""
    twelve_hours_ago = timezone.now() - timedelta(hours=12)
    # Find open shops that haven't updated in 12 hours (or have never updated)
    vendors = Vendor.objects.filter(is_closed_today=False)
    
    updated_count = 0
    for vendor in vendors:
        if vendor.stock_last_updated is None or vendor.stock_last_updated < twelve_hours_ago:
            vendor.needs_stock_nudge = True
            vendor.save()
            updated_count += 1
            
    print(f"[{timezone.now()}] Applied stock nudge to {updated_count} vendors.")

def apply_demerits():
    """24-Hour Penalty: Adds 1 demerit to open vendors who haven't updated in 24 hours."""
    twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
    vendors = Vendor.objects.filter(is_closed_today=False)
    
    updated_count = 0
    for vendor in vendors:
        if vendor.stock_last_updated is None or vendor.stock_last_updated < twenty_four_hours_ago:
            vendor.demerit_points += 1
            vendor.save()

            calculate_vendor_platform_score(vendor)

            updated_count += 1
            
    print(f"[{timezone.now()}] Assigned demerit points to {updated_count} vendors.")


def run_lottery_draw():
    """
    Module 6: Daily 11 PM Token Lottery Draw.
    Gathers all unique registered customer voters from today,
    runs a weighted random reward, increments winners' wallet balances,
    and logs the transactions.
    """
    today = timezone.localdate()
    
    # 1. Query 'customer_id' instead of 'user_id'
    # 2. Exclude guest votes (where customer_id is null) using customer__isnull=False
    customer_ids = UserVote.objects.filter(
        date=today, 
        customer__isnull=False
    ).values_list('customer_id', flat=True).distinct()
    
    for customer_id in customer_ids:
        try:
            # Look up the customer record using their primary key ID
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            continue
            
        rand = random.random()
        reward = 0
        
     
        if rand < 0.05:
            reward = 100
            desc = "🎉 Rare Jackpot! Won 100 tokens in the daily poll lottery draw."
        elif rand < 0.25:  # 0.05 + 0.20
            reward = random.randint(1, 5)
            desc = f"🪙 Won {reward} tokens in the daily poll lottery draw."
        else:
            reward = 0
            
        if reward > 0:
        
            wallet, created = TokenWallet.objects.get_or_create(customer=customer)
            wallet.balance += reward
            wallet.save()
            
           
            TokenTransaction.objects.create(
                customer=customer,
                amount=reward,
                transaction_type='EARNING',
                description=desc
            )