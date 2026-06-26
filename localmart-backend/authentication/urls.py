from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import VendorRegisterView, CustomerRegisterView

urlpatterns = [
    # Registration Endpoints
    path('register/vendor/', VendorRegisterView.as_view(), name='vendor-register'),
    path('register/customer/', CustomerRegisterView.as_view(), name='customer-register'),
    
    # Login Endpoints (JWT Tokens)
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
