from django.urls import path
from . import views

app_name = 'notification_templates'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Template Management
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<uuid:pk>/', views.template_detail, name='template_detail'),
    path('templates/<uuid:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<uuid:pk>/delete/', views.template_delete, name='template_delete'),
    path('templates/<uuid:pk>/test/', views.template_test, name='template_test'),
    path('templates/<uuid:pk>/preview/', views.template_preview, name='template_preview'),
    
    # Category Management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<uuid:pk>/edit/', views.category_edit, name='category_edit'),
    
    # Import/Export
    path('import/', views.template_import, name='template_import'),
    path('export/', views.template_export, name='template_export'),
    
    # API Endpoints
    path('api/placeholders/', views.get_placeholders, name='api_placeholders'),
    path('api/validate/', views.validate_template, name='api_validate'),
]
