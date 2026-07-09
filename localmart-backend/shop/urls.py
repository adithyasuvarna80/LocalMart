from django.urls import path
from .views import ProductListCreateView, ProductDetailView, VendorProfileView, DailyStockManageView,ToggleShopClosedView 

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('profile/', VendorProfileView.as_view(), name='vendor-profile'),
    
    # NEW: Endpoint for the Daily Stock Gate
    path('daily-stock/', DailyStockManageView.as_view(), name='daily-stock'),
    path('toggle-closed/', ToggleShopClosedView.as_view(), name='toggle-closed'),
]