from django.urls import path
from . import views

app_name = 'rf_scanner'

urlpatterns = [
    # Authentication
    path('login/', views.rf_login, name='login'),
    path('logout/', views.rf_logout, name='logout'),
    
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('start-session/', views.start_session, name='start_session'),
    path('end-session/<int:session_id>/', views.end_session, name='end_session'),
    path('scan/<int:session_id>/', views.scan, name='scan'),
    
    # API endpoints
    path('api/scan/', views.api_scan, name='api_scan'),
    
    # History and details
    path('history/', views.session_history, name='session_history'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('search/', views.search_items, name='search_items'),
] 