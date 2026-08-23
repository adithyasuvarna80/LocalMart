from django.urls import path
from .views import ProductListCreateView, ProductDetailView, VendorProfileView, DailyStockManageView,ToggleShopClosedView,LocalShopsView ,PlaceOrderView, OrderListView ,CustomerProfileView
from .views import UpdateOrderStatusView, CustomerConfirmDeliveryView,CustomerPollView, VendorPollChartDataView,SubmitReviewView, VendorReviewsListView,CustomerWalletHistoryView


urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('profile/', VendorProfileView.as_view(), name='vendor-profile'),
    
    
    path('daily-stock/', DailyStockManageView.as_view(), name='daily-stock'),
    path('toggle-closed/', ToggleShopClosedView.as_view(), name='toggle-closed'),

    
    path('local-shops/', LocalShopsView.as_view(), name='local-shops'),

     path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/place/', PlaceOrderView.as_view(), name='place-order'),

     path('customer-profile/', CustomerProfileView.as_view(), name='customer-profile'),

      path('orders/<int:pk>/status/', UpdateOrderStatusView.as_view(), name='update-order-status'),
    path('orders/<int:pk>/confirm/', CustomerConfirmDeliveryView.as_view(), name='confirm-delivery'),


     path('poll/', CustomerPollView.as_view(), name='customer-poll'),
    path('poll/chart/', VendorPollChartDataView.as_view(), name='vendor-poll-chart'),

    path('reviews/', SubmitReviewView.as_view(), name='submit-review'),
    path('vendors/<int:vendor_id>/reviews/', VendorReviewsListView.as_view(), name='vendor-reviews'),
    path('wallet/history/', CustomerWalletHistoryView.as_view(), name='wallet-history'),

]
