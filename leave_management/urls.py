from django.urls import path
from . import views

app_name = 'leave_management'

urlpatterns = [
    # Dashboard
    path('', views.leave_dashboard, name='dashboard'),
    
    # Leave Requests
    path('request/create/', views.leave_request_create, name='leave_request_create'),
    path('request/<str:request_id>/', views.leave_request_detail, name='leave_request_detail'),
    path('request/list/', views.leave_request_list, name='leave_request_list'),
    
    # Leave Approvals
    path('approval/<str:request_id>/', views.leave_approval, name='leave_approval'),
    
    # Leave Balances
    path('balance/', views.leave_balance, name='leave_balance'),
    path('balance/list/', views.leave_balance_list, name='leave_balance_list'),
    path('balance/<int:balance_id>/edit/', views.leave_balance_edit, name='leave_balance_edit'),
    path('balance/bulk/', views.bulk_leave_balance, name='bulk_leave_balance'),
    
    # Leave Calendar
    path('calendar/', views.leave_calendar, name='leave_calendar'),
    
    # Leave Encashment
    path('encashment/create/', views.leave_encashment_create, name='leave_encashment_create'),
    path('encashment/<int:encashment_id>/approval/', views.leave_encashment_approval, name='leave_encashment_approval'),
    path('encashment/list/', views.leave_encashment_list, name='leave_encashment_list'),
    
    # Notifications
    path('notifications/', views.leave_notifications, name='leave_notifications'),
    
    # Leave Types (Admin)
    path('types/', views.leave_type_list, name='leave_type_list'),
    path('types/create/', views.leave_type_create, name='leave_type_create'),
    path('types/<int:type_id>/edit/', views.leave_type_edit, name='leave_type_edit'),
    
    # Leave Policies (Admin)
    path('policy/', views.leave_policy, name='leave_policy'),
    path('policies/', views.leave_policy_list, name='leave_policy_list'),
    path('policies/create/', views.leave_policy_create, name='leave_policy_create'),
    path('policies/<int:policy_id>/edit/', views.leave_policy_edit, name='leave_policy_edit'),
    
    # Reports
    path('reports/', views.leave_reports, name='leave_reports'),
] 