from django.urls import path
from user.user_views import (
    user_list, user_create, user_update, user_delete, user_detail,
    role_list, role_create, role_update, permission_list, permission_create, permission_update,
    get_role_permissions, update_role_permissions, change_password, reset_password,
    permissions_management
)

app_name = 'user'

urlpatterns = [
    # User management
    path('', user_list, name='user_list'),
    path('create/', user_create, name='user_create'),
    path('<int:pk>/', user_detail, name='user_detail'),
    path('<int:pk>/edit/', user_update, name='user_edit'),
    path('<int:pk>/delete/', user_delete, name='user_delete'),
    
    # Password management
    path('<int:pk>/change-password/', change_password, name='change_password'),
    path('<int:pk>/reset-password/', reset_password, name='reset_password'),
    
    # Role management
    path('roles/', role_list, name='role_list'),
    path('roles/create/', role_create, name='role_create'),
    path('roles/<int:pk>/edit/', role_update, name='role_edit'),
    
    # Permission management
    path('permissions/', permission_list, name='permission_list'),
    path('permissions/create/', permission_create, name='permission_create'),
    path('permissions/<int:pk>/edit/', permission_update, name='permission_edit'),
    
    # AJAX endpoints
    path('api/role/<int:role_id>/permissions/', get_role_permissions, name='get_role_permissions'),
    path('api/role/<int:role_id>/permissions/update/', update_role_permissions, name='update_role_permissions'),
    path('api/save-permissions/', permissions_management, name='save_permissions'),
    
    # Permissions Management
    path('permissions/manage/', permissions_management, name='permissions_management'),
]