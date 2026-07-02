from django.urls import path
from .views import ProductListCreateView, ProductDetailView, VendorProfileView

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    
    
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    
    
    path('profile/', VendorProfileView.as_view(), name='vendor-profile'),
]