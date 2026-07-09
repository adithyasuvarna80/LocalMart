from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('VENDOR', 'Vendor'),
        ('CUSTOMER', 'Customer'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']

    def __str__(self):
        return self.email



class Vendor(models.Model):
    CATEGORY_CHOICES = (
        ('VEGETABLES', 'Vegetables'),
        ('BAKERY', 'Bakery'),
        ('DAIRY', 'Dairy'),
        ('GROCERY', 'Grocery'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')

    
    

    shop_name = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    locality = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    free_delivery_threshold = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    
    is_closed_today = models.BooleanField(default=False)
    stock_last_updated = models.DateTimeField(null=True, blank=True)
    demerit_points = models.IntegerField(default=0)
    needs_stock_nudge = models.BooleanField(default=False)
    platform_score = models.FloatField(default=0.0)

    def __str__(self):
        return self.shop_name or self.user.email



class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    

    pincode = models.CharField(max_length=10)
    area_name = models.CharField(max_length=255)
    
    
    wallet_balance = models.IntegerField(default=0)

    def __str__(self):
        return self.user.email