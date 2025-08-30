from django.urls import path
from . import views

app_name = 'master_data_import'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # File Upload and Processing
    path('upload/', views.upload_file, name='upload_file'),
    path('column-mapping/', views.column_mapping, name='column_mapping'),
    path('preview/', views.preview_data, name='preview_data'),
    
    # Import Jobs
    path('jobs/', views.ImportJobListView.as_view(), name='job_list'),
    path('jobs/<uuid:pk>/', views.ImportJobDetailView.as_view(), name='job_detail'),
    path('jobs/<uuid:job_id>/progress/', views.job_progress, name='job_progress'),
    path('jobs/<uuid:job_id>/cancel/', views.cancel_job, name='cancel_job'),
    path('jobs/<uuid:job_id>/export-errors/', views.export_errors, name='export_errors'),
    
    # Import Templates
    path('templates/', views.ImportTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ImportTemplateCreateView.as_view(), name='template_create'),
    path('templates/<uuid:pk>/', views.ImportTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<uuid:pk>/edit/', views.ImportTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<uuid:pk>/delete/', views.ImportTemplateDeleteView.as_view(), name='template_delete'),
    path('templates/<uuid:template_id>/download/', views.download_template, name='download_template'),
]
