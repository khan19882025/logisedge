from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Set app name for namespace
app_name = 'payment_source'

# Create router for API endpoints
router = DefaultRouter()
router.register(r'payment-sources', views.PaymentSourceViewSet, basename='payment-source')

# URL patterns
urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Frontend views
    path('', views.payment_source_list, name='payment_source_list'),
    path('create/', views.payment_source_create, name='payment_source_create'),
    path('<int:pk>/', views.payment_source_detail, name='payment_source_detail'),
    path('<int:pk>/edit/', views.payment_source_update, name='payment_source_update'),
    path('<int:pk>/delete/', views.payment_source_delete, name='payment_source_delete'),
    path('<int:pk>/restore/', views.payment_source_restore, name='payment_source_restore'),
    
    # AJAX endpoints
    path('ajax/get-payment-sources/', views.get_payment_sources_ajax, name='get_payment_sources_ajax'),
    path('ajax/update-status/', views.update_payment_source_status_ajax, name='update_payment_source_status_ajax'),
]
