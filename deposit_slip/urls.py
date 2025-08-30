from django.urls import path
from . import views

app_name = 'deposit_slip'

urlpatterns = [
    # Main views
    path('', views.deposit_slip_list, name='list'),
    path('create/', views.deposit_slip_create, name='create'),
    path('<int:pk>/', views.deposit_slip_detail, name='detail'),
    path('<int:pk>/edit/', views.deposit_slip_edit, name='edit'),
    path('<int:pk>/delete/', views.deposit_slip_delete, name='delete'),
    
    # Action views
    path('<int:pk>/submit/', views.deposit_slip_submit, name='submit'),
    path('<int:pk>/confirm/', views.deposit_slip_confirm, name='confirm'),
    
    # AJAX endpoints
    path('ajax/available-vouchers/', views.get_available_vouchers, name='available_vouchers'),
    path('ajax/summary/', views.deposit_slip_summary, name='summary'),
] 