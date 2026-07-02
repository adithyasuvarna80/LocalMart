from django.db import models
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
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, null=True) # Will store the Cloudinary URL

    def __str__(self):
        return f"{self.name} - {self.vendor.shop_name}"