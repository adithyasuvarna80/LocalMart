from django.utils import timezone
from datetime import timedelta
from authentication.models import Vendor
from .models import Order, DailyStock

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