from django.urls import path
from . import views

app_name = 'exit_management'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Exit Types
    path('exit-types/', views.ExitTypeListView.as_view(), name='exit_type_list'),
    path('exit-types/create/', views.ExitTypeCreateView.as_view(), name='exit_type_create'),
    path('exit-types/<int:pk>/update/', views.ExitTypeUpdateView.as_view(), name='exit_type_update'),
    path('exit-types/<int:pk>/delete/', views.ExitTypeDeleteView.as_view(), name='exit_type_delete'),
    
    # Clearance Departments
    path('clearance-departments/', views.ClearanceDepartmentListView.as_view(), name='clearance_department_list'),
    path('clearance-departments/create/', views.ClearanceDepartmentCreateView.as_view(), name='clearance_department_create'),
    path('clearance-departments/<int:pk>/update/', views.ClearanceDepartmentUpdateView.as_view(), name='clearance_department_update'),
    path('clearance-departments/<int:pk>/delete/', views.ClearanceDepartmentDeleteView.as_view(), name='clearance_department_delete'),
    
    # Clearance Items
    path('clearance-items/', views.ClearanceItemListView.as_view(), name='clearance_item_list'),
    path('clearance-items/create/', views.ClearanceItemCreateView.as_view(), name='clearance_item_create'),
    path('clearance-items/<int:pk>/update/', views.ClearanceItemUpdateView.as_view(), name='clearance_item_update'),
    path('clearance-items/<int:pk>/delete/', views.ClearanceItemDeleteView.as_view(), name='clearance_item_delete'),
    
    # Resignation Requests
    path('resignations/', views.ResignationRequestListView.as_view(), name='resignation_request_list'),
    path('resignations/create/', views.ResignationRequestCreateView.as_view(), name='resignation_request_create'),
    path('resignations/<int:pk>/', views.ResignationRequestDetailView.as_view(), name='resignation_request_detail'),
    path('resignations/<int:pk>/update/', views.ResignationRequestUpdateView.as_view(), name='resignation_request_update'),
    path('resignations/<int:pk>/delete/', views.ResignationRequestDeleteView.as_view(), name='resignation_request_delete'),
    
    # Approval Workflow
    path('resignations/<int:pk>/manager-approval/', views.manager_approval, name='manager_approval'),
    path('resignations/<int:pk>/hr-approval/', views.hr_approval, name='hr_approval'),
    
    # Clearance Process
    path('resignations/<int:pk>/start-clearance/', views.start_clearance_process, name='start_clearance_process'),
    path('clearance-process/<int:pk>/', views.clearance_process_detail, name='clearance_process_detail'),
    path('clearance-item/<int:pk>/update/', views.update_clearance_item, name='update_clearance_item'),
    path('clearance-process/<int:pk>/bulk-update/', views.bulk_update_clearance, name='bulk_update_clearance'),
    
    # Gratuity Calculation
    path('resignations/<int:pk>/calculate-gratuity/', views.calculate_gratuity, name='calculate_gratuity'),
    path('gratuity/<int:pk>/update/', views.update_gratuity_calculation, name='update_gratuity_calculation'),
    
    # Final Settlement
    path('resignations/<int:pk>/create-settlement/', views.create_final_settlement, name='create_final_settlement'),
    path('settlement/<int:pk>/update/', views.update_final_settlement, name='update_final_settlement'),
    
    # Reports
    path('reports/', views.exit_reports, name='exit_reports'),
    
    # AJAX endpoints
    path('ajax/calculate-notice-period/', views.calculate_notice_period, name='calculate_notice_period'),
    path('ajax/employee-details/', views.get_employee_details, name='get_employee_details'),
] 