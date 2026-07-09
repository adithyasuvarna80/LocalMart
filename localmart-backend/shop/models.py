from django.db import models
from django.utils import timezone
from authentication.models import Vendor, Customer 

class Product(models.Model):
    UNIT_CHOICES = (
        ('KG', 'Kilogram'),
        ('LITRE', 'Litre'),
        ('PIECE', 'Piece'),
        ('DOZEN', 'Dozen'),
        ('GRAM', 'Gram'),
    )
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KG')
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.vendor.user.email}"


class DailyStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='daily_stock')
    date = models.DateField(default=timezone.now)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_sold_out = models.BooleanField(default=False)

    class Meta:
      
        unique_together = ('product', 'date')

    def save(self, *args, **kwargs):
     
        if self.quantity <= 0:
            self.is_sold_out = True
        else:
            self.is_sold_out = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} | {self.date} | Qty: {self.quantity}"
    

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('READY', 'Ready / Out for Delivery'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    )
    ORDER_TYPE_CHOICES = (
        ('PICKUP', 'Pickup'),
        ('DELIVERY', 'Home Delivery'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)