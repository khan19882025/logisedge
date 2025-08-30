from django.urls import path
from . import views

app_name = 'email_configuration'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Configuration management
    path('configurations/', views.EmailConfigurationListView.as_view(), name='configuration_list'),
    path('configurations/create/', views.EmailConfigurationCreateView.as_view(), name='configuration_create'),
    path('configurations/<int:pk>/', views.EmailConfigurationDetailView.as_view(), name='configuration_detail'),
    path('configurations/<int:pk>/edit/', views.EmailConfigurationUpdateView.as_view(), name='configuration_update'),
    path('configurations/<int:pk>/delete/', views.EmailConfigurationDeleteView.as_view(), name='configuration_delete'),
    
    # Testing
    path('configurations/<int:pk>/test/', views.test_email_configuration, name='test_configuration'),
    
    # Test results
    path('test-results/', views.test_results_list, name='test_results_list'),
    path('test-results/<int:pk>/', views.test_result_detail, name='test_result_detail'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notifications/<int:pk>/edit/', views.notification_update, name='notification_update'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    
    # API endpoints
    path('api/health/', views.configuration_health, name='configuration_health'),
    path('api/statistics/', views.configuration_statistics, name='configuration_statistics'),
]
