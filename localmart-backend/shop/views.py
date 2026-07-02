from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Product
from .serializers import ProductSerializer, VendorProfileSerializer

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user.vendor_profile)


class ProductDetailView(generics.DestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
       
        return Product.objects.filter(vendor=self.request.user.vendor_profile)


class VendorProfileView(generics.RetrieveAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Automatically pull the profile of the user making the request
        return self.request.user.vendor_profile