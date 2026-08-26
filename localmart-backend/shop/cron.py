from django.utils import timezone
from datetime import timedelta
from authentication.models import Vendor
from .models import Order, DailyStock
import random
from django.utils import timezone
from authentication.models import Customer
from .models import UserVote, TokenWallet, TokenTransaction

def calculate_platform_scores():
    """Recalculates the platform score out of 10 for every vendor daily."""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    for vendor in Vendor.objects.all():
        
        stock_days = DailyStock.objects.filter(
            product__vendor=vendor, 
            date__gte=thirty_days_ago
        ).values('date').distinct().count()
        stock_score = (stock_days / 30.0) * 3.0 if stock_days else 0.0

       
        total_orders = Order.objects.filter(vendor=vendor).count()
        accepted_orders = Order.objects.filter(
            vendor=vendor, 
            status__in=['ACCEPTED', 'READY', 'COMPLETED']
        ).count()
        acceptance_score = (accepted_orders / total_orders) * 2.5 if total_orders > 0 else 2.5

        
        total_deliveries = Order.objects.filter(
            vendor=vendor, 
            order_type='DELIVERY', 
            status__in=['ACCEPTED', 'READY', 'COMPLETED']
        ).count()
        completed_deliveries = Order.objects.filter(
            vendor=vendor, 
            order_type='DELIVERY', 
            status='COMPLETED'
        ).count()
        delivery_score = (completed_deliveries / total_deliveries) * 2.5 if total_deliveries > 0 else 2.5

    
        demerit_penalty = max(0, 10 - vendor.demerit_points)
        demerit_score = demerit_penalty * 0.20

       
        final_score = round(stock_score + acceptance_score + delivery_score + demerit_score, 1)
        
        
        vendor.platform_score = str(final_score)
        vendor.save()
        
    print(f"[{timezone.now()}] Successfully updated platform scores for all vendors.")

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
            updated_count += 1
            
    print(f"[{timezone.now()}] Assigned demerit points to {updated_count} vendors.")


def run_lottery_draw():
    """
    Module 6: Daily 11 PM Token Lottery Draw.
    Gathers all unique registered customer voters from today,
    runs a weighted random reward, increments winners' wallet balances,
    and logs the transactions.
    """
    today = timezone.now().date()
    
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