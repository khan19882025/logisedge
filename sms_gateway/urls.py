from django.urls import path
from . import views

app_name = 'sms_gateway'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Gateway management
    path('gateways/', views.SMSGatewayListView.as_view(), name='gateway_list'),
    path('gateways/create/', views.SMSGatewayCreateView.as_view(), name='gateway_create'),
    path('gateways/<int:pk>/', views.SMSGatewayDetailView.as_view(), name='gateway_detail'),
    path('gateways/<int:pk>/edit/', views.SMSGatewayUpdateView.as_view(), name='gateway_update'),
    path('gateways/<int:pk>/delete/', views.SMSGatewayDeleteView.as_view(), name='gateway_delete'),
    
    # Gateway testing
    path('gateways/<int:pk>/test/', views.gateway_test, name='gateway_test'),
    
    # Test results
    path('test-results/', views.test_results_list, name='test_results_list'),
    path('test-results/<int:pk>/', views.test_result_detail, name='test_result_detail'),
    
    # Messages
    path('messages/', views.messages_list, name='messages_list'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/send/', views.send_message, name='send_message'),
    
    # Health monitoring
    path('health/', views.gateway_health, name='gateway_health'),
    
    # API endpoints
    path('api/health/', views.api_health_check, name='api_health_check'),
]
