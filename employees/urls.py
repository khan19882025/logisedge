from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # Dashboard
    path('', views.employee_dashboard, name='dashboard'),
    
    # Employee Management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('employees/export/', views.export_employees, name='export_employees'),
    
    # Department Management
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    
    # Designation Management
    path('designations/', views.designation_list, name='designation_list'),
    path('designations/create/', views.designation_create, name='designation_create'),
    path('designations/<int:pk>/edit/', views.designation_edit, name='designation_edit'),
    
    # Attendance Management
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/create/', views.attendance_create, name='attendance_create'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    
    # Leave Management
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/create/', views.leave_create, name='leave_create'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    
    # Reports
    path('reports/', views.employee_reports, name='reports'),
    path('reports/attendance/', views.attendance_report, name='attendance_report'),
    
    # AJAX endpoints
    path('ajax/designations/', views.get_designations, name='get_designations'),
    path('ajax/bulk-attendance/', views.bulk_attendance, name='bulk_attendance'),
] 