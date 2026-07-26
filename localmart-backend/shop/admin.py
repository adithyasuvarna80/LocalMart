from django.contrib import admin
from .models import Product, DailyStock, Order, OrderItem,PollItem 

admin.site.register(Product)
admin.site.register(DailyStock)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(PollItem)