from django.contrib import admin
from .models import Product, DailyStock, Order, OrderItem

admin.site.register(Product)
admin.site.register(DailyStock)
admin.site.register(Order)
admin.site.register(OrderItem)