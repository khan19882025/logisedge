from django.urls import path
from . import views

app_name = 'bulk_email_sender'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Email Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<uuid:pk>/', views.template_detail, name='template_detail'),
    path('templates/<uuid:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<uuid:pk>/delete/', views.template_delete, name='template_delete'),
    
    # Email Campaigns
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/create/', views.campaign_create, name='campaign_create'),
    path('campaigns/<uuid:pk>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/<uuid:pk>/edit/', views.campaign_edit, name='campaign_edit'),
    path('campaigns/<uuid:pk>/preview/', views.campaign_preview, name='campaign_preview'),
    path('campaigns/<uuid:pk>/start/', views.campaign_start, name='campaign_start'),
    path('campaigns/<uuid:pk>/pause/', views.campaign_pause, name='campaign_pause'),
    path('campaigns/<uuid:pk>/cancel/', views.campaign_cancel, name='campaign_cancel'),
    
    # Recipient Lists
    path('recipient-lists/', views.recipient_list_list, name='recipient_list_list'),
    path('recipient-lists/create/', views.recipient_list_create, name='recipient_list_create'),
    path('recipient-lists/<uuid:pk>/', views.recipient_list_detail, name='recipient_list_detail'),
    
    # Recipient Management
    path('recipients/upload/', views.recipient_upload, name='recipient_upload'),
    path('recipients/upload/confirm/', views.recipient_upload_confirm, name='recipient_upload_confirm'),
    
    # Email Settings
    path('settings/', views.settings_list, name='settings_list'),
    path('settings/create/', views.settings_create, name='settings_create'),
    path('settings/<uuid:pk>/', views.settings_detail, name='settings_detail'),
    
    # Tracking and Analytics
    path('tracking/', views.tracking_dashboard, name='tracking_dashboard'),
    path('webhook/tracking/', views.tracking_webhook, name='tracking_webhook'),
]
