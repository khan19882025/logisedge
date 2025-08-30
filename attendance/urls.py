from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard
    path('', views.attendance_dashboard, name='dashboard'),
    
    # Attendance Management
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/create/', views.attendance_create, name='attendance_create'),
    path('attendance/<int:pk>/', views.attendance_detail, name='attendance_detail'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('attendance/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    path('attendance/bulk/', views.bulk_attendance, name='bulk_attendance'),
    
    # Time Tracking
    path('time-tracking/', views.time_tracking, name='time_tracking'),
    path('punch/', views.employee_punch, name='employee_punch'),
    
    # Break Management
    path('breaks/', views.break_list, name='break_list'),
    path('breaks/create/', views.break_create, name='break_create'),
    path('breaks/<int:pk>/edit/', views.break_edit, name='break_edit'),
    
    # Shift Management
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.shift_create, name='shift_create'),
    path('shifts/<int:pk>/edit/', views.shift_edit, name='shift_edit'),
    
    # Holiday Management
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/create/', views.holiday_create, name='holiday_create'),
    path('holidays/<int:pk>/edit/', views.holiday_edit, name='holiday_edit'),
    
    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/export/', views.export_attendance, name='export_attendance'),
    
    # Calendar
    path('calendar/', views.attendance_calendar, name='attendance_calendar'),
    
    # API Endpoints
    path('api/attendance-status/', views.api_attendance_status, name='api_attendance_status'),
    path('api/punch/', views.api_punch_in_out, name='api_punch_in_out'),
] 