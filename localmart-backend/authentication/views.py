from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import User
from .serializers import VendorRegistrationSerializer, CustomerRegistrationSerializer

class VendorRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = VendorRegistrationSerializer

class CustomerRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = CustomerRegistrationSerializer