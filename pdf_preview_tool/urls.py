from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'pdf_preview_tool'

# Create a router for API endpoints
router = DefaultRouter()
router.register(r'signature-stamp', views.SignatureStampViewSet, basename='signature-stamp')

urlpatterns = [
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<uuid:document_id>/edit/', views.document_update, name='document_update'),
    path('documents/<uuid:document_id>/preview/', views.document_preview, name='document_preview'),
    path('documents/<uuid:document_id>/print/', views.print_document, name='print_document'),
    
    # Document types
    path('document-types/', views.document_type_list, name='document_type_list'),
    path('document-types/create/', views.document_type_create, name='document_type_create'),
    
    # User settings
    path('settings/', views.preview_settings, name='preview_settings'),
    
    # Signature uploader template
    path('signature-uploader/', views.signature_uploader_view, name='signature_uploader'),
    path('utilities/signature-stamp/', views.signature_uploader_view, name='signature_uploader_utilities'),
    
    # API endpoints for React integration
    path('api/documents/<uuid:document_id>/start-session/', views.api_start_preview_session, name='api_start_preview_session'),
    path('api/sessions/<str:session_id>/log-action/', views.api_log_preview_action, name='api_log_preview_action'),
    path('api/sessions/<str:session_id>/end/', views.api_end_preview_session, name='api_end_preview_session'),
    path('api/documents/<uuid:document_id>/info/', views.api_document_info, name='api_document_info'),
    path('api/user/settings/', views.api_user_preview_settings, name='api_user_preview_settings'),
    path('api/user/settings/update/', views.api_update_preview_settings, name='api_update_preview_settings'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
