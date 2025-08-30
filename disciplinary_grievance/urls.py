from django.urls import path
from . import views

app_name = 'disciplinary_grievance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Grievance URLs
    path('grievances/', views.grievance_list, name='grievance_list'),
    path('grievances/create/', views.grievance_create, name='grievance_create'),
    path('grievances/<int:pk>/', views.grievance_detail, name='grievance_detail'),
    path('grievances/<int:pk>/update/', views.grievance_update, name='grievance_update'),
    path('grievances/<int:pk>/delete/', views.grievance_delete, name='grievance_delete'),
    path('grievances/<int:pk>/status-update/', views.grievance_status_update, name='grievance_status_update'),
    path('grievances/<int:grievance_pk>/attachments/upload/', views.grievance_attachment_upload, name='grievance_attachment_upload'),
    path('grievances/<int:grievance_pk>/notes/add/', views.grievance_note_add, name='grievance_note_add'),
    
    # Disciplinary Case URLs
    path('disciplinary-cases/', views.disciplinary_case_list, name='disciplinary_case_list'),
    path('disciplinary-cases/create/', views.disciplinary_case_create, name='disciplinary_case_create'),
    path('disciplinary-cases/<int:pk>/', views.disciplinary_case_detail, name='disciplinary_case_detail'),
    path('disciplinary-cases/<int:pk>/update/', views.disciplinary_case_update, name='disciplinary_case_update'),
    path('disciplinary-cases/<int:pk>/status-update/', views.disciplinary_case_status_update, name='disciplinary_case_status_update'),
    
    # Disciplinary Action URLs
    path('disciplinary-cases/<int:case_pk>/actions/create/', views.disciplinary_action_create, name='disciplinary_action_create'),
    path('disciplinary-actions/<int:pk>/', views.disciplinary_action_detail, name='disciplinary_action_detail'),
    
    # Appeal URLs
    path('disciplinary-actions/<int:action_pk>/appeals/create/', views.appeal_create, name='appeal_create'),
    path('appeals/<int:pk>/review/', views.appeal_review, name='appeal_review'),
    
    # Configuration URLs
    path('categories/', views.grievance_category_list, name='grievance_category_list'),
    path('categories/create/', views.grievance_category_create, name='grievance_category_create'),
    path('action-types/', views.disciplinary_action_type_list, name='disciplinary_action_type_list'),
    path('action-types/create/', views.disciplinary_action_type_create, name='disciplinary_action_type_create'),
    
    # Report URLs
    path('reports/grievances/', views.grievance_report, name='grievance_report'),
    path('reports/disciplinary-cases/', views.disciplinary_case_report, name='disciplinary_case_report'),
    
    # API URLs for AJAX
    path('api/employee/<int:employee_id>/grievances/', views.get_employee_grievances, name='get_employee_grievances'),
    path('api/employee/<int:employee_id>/disciplinary-cases/', views.get_employee_disciplinary_cases, name='get_employee_disciplinary_cases'),
    path('api/grievances/<int:pk>/status/', views.update_grievance_status_ajax, name='update_grievance_status_ajax'),
] 