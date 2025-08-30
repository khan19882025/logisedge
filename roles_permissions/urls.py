from django.urls import path
from . import views

app_name = 'roles_permissions'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Roles
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('roles/<uuid:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('roles/<uuid:pk>/edit/', views.RoleUpdateView.as_view(), name='role_update'),
    path('roles/<uuid:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),
    path('roles/<uuid:pk>/permissions/', views.role_permissions, name='role_permissions'),
    
    # Permissions
    path('permissions/', views.PermissionListView.as_view(), name='permission_list'),
    path('permissions/create/', views.PermissionCreateView.as_view(), name='permission_create'),
    path('permissions/<uuid:pk>/edit/', views.PermissionUpdateView.as_view(), name='permission_update'),
    
    # User Roles
    path('user-roles/', views.UserRoleListView.as_view(), name='user_role_list'),
    path('user-roles/create/', views.UserRoleCreateView.as_view(), name='user_role_create'),
    path('user-roles/<uuid:pk>/edit/', views.UserRoleUpdateView.as_view(), name='user_role_update'),
    path('user-roles/<uuid:pk>/delete/', views.UserRoleDeleteView.as_view(), name='user_role_delete'),
    path('user-roles/bulk-assignment/', views.bulk_role_assignment, name='bulk_role_assignment'),
    
    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<uuid:pk>/', views.department_detail, name='department_detail'),
    path('departments/<uuid:pk>/edit/', views.department_update, name='department_update'),
    path('departments/<uuid:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Cost Centers
    path('cost-centers/', views.cost_center_list, name='cost_center_list'),
    path('cost-centers/create/', views.cost_center_create, name='cost_center_create'),
    path('cost-centers/<uuid:pk>/', views.cost_center_detail, name='cost_center_detail'),
    path('cost-centers/<uuid:pk>/edit/', views.cost_center_update, name='cost_center_update'),
    path('cost-centers/<uuid:pk>/delete/', views.cost_center_delete, name='cost_center_delete'),
    
    # User Permissions
    path('users/<int:user_id>/permissions/', views.user_permissions, name='user_permissions'),
    
    # Logs
    path('access-logs/', views.access_logs, name='access_logs'),
    path('access-logs/<uuid:log_id>/details/', views.access_log_details, name='access_log_details'),
    path('access-logs/clear-old/', views.clear_old_access_logs, name='clear_old_access_logs'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('audit-logs/<uuid:log_id>/details/', views.log_details, name='log_details'),
    
    # API endpoints
    path('api/users/<int:user_id>/permissions/', views.get_user_permissions, name='api_user_permissions'),
    path('api/check-permission/', views.check_permission, name='api_check_permission'),
]
