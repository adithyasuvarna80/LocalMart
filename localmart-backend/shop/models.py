from django.db import models
from django.utils import timezone
from authentication.models import Vendor

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

# NEW: The Daily Stock Tracker
class DailyStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='daily_stock')
    date = models.DateField(default=timezone.now)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_sold_out = models.BooleanField(default=False)

    class Meta:
        # Ensures a product can only have exactly ONE stock entry per day
        unique_together = ('product', 'date')

    def save(self, *args, **kwargs):
        # Automated Business Logic: If quantity drops to 0, mark as sold out automatically!
        if self.quantity <= 0:
            self.is_sold_out = True
        else:
            self.is_sold_out = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} | {self.date} | Qty: {self.quantity}"