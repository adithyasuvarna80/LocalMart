from django.urls import path
from .views import VendorRegisterView, CustomerRegisterView, CustomTokenObtainPairView

urlpatterns = [
    path('register/vendor/', VendorRegisterView.as_view(), name='vendor-register'),
    path('register/customer/', CustomerRegisterView.as_view(), name='customer-register'),
  
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]