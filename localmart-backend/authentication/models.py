from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. UNIFIED AUTHENTICATION MODEL
class User(AbstractUser):
    ROLE_CHOICES = (
        ('VENDOR', 'Vendor'),
        ('CUSTOMER', 'Customer'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    # Use email for login instead of a username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']

    def __str__(self):
        return self.email


# 2. VENDOR PROFILE MODEL
class Vendor(models.Model):
    CATEGORY_CHOICES = (
        ('VEGETABLES', 'Vegetables'),
        ('BAKERY', 'Bakery'),
        ('DAIRY', 'Dairy'),
        ('GROCERY', 'Grocery'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    
    # Shop Setup Wizard Fields
    shop_name = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    locality = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    free_delivery_threshold = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    # Automated Business Logic Fields
    is_closed_today = models.BooleanField(default=False)
    stock_last_updated = models.DateTimeField(null=True, blank=True)
    demerit_points = models.IntegerField(default=0)
    needs_stock_nudge = models.BooleanField(default=False)
    platform_score = models.FloatField(default=0.0)

    def __str__(self):
        return self.shop_name or self.user.email


# 3. CUSTOMER PROFILE MODEL
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    
    # Registration Fields
    pincode = models.CharField(max_length=10)
    area_name = models.CharField(max_length=255)
    
    # Gamification Fields
    wallet_balance = models.IntegerField(default=0)

    def __str__(self):
        return self.user.email