from django.urls import path
from .views import VendorRegisterView, CustomerRegisterView, CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView



urlpatterns = [
    path('register/vendor/', VendorRegisterView.as_view(), name='vendor-register'),
    path('register/customer/', CustomerRegisterView.as_view(), name='customer-register'),
  
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]