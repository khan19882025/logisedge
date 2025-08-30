from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'billing_payable_tracking'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'bills', views.BillViewSet, basename='bill')
router.register(r'vendors', views.VendorViewSet, basename='vendor')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Dashboard and frontend views
    path('', views.dashboard, name='dashboard'),
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/create/', views.bill_create, name='bill_create'),
    path('bills/<uuid:pk>/', views.bill_detail, name='bill_detail'),
    path('bills/<uuid:pk>/edit/', views.bill_edit, name='bill_edit'),
    path('bills/<uuid:pk>/delete/', views.bill_delete, name='bill_delete'),
    
    # AJAX endpoints for actions
    path('ajax/mark-paid/<uuid:bill_id>/', views.mark_bill_paid, name='mark_bill_paid'),
    path('ajax/confirm-bill/<uuid:bill_id>/', views.confirm_bill, name='confirm_bill'),
    path('ajax/dashboard-stats/', views.get_dashboard_stats, name='dashboard_stats'),
    path('ajax/filter-bills/', views.filter_bills, name='filter_bills'),
    path('ajax/dismiss-alert/<uuid:alert_id>/', views.dismiss_alert, name='dismiss_alert'),
    
    # Vendor management
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<uuid:pk>/', views.vendor_detail, name='vendor_detail'),
    path('vendors/<uuid:pk>/edit/', views.vendor_edit, name='vendor_edit'),
    path('vendors/<uuid:pk>/delete/', views.vendor_delete, name='vendor_delete'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
]