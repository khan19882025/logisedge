from django.urls import path
from . import views

app_name = 'supplier_bills'

urlpatterns = [
    path('', views.supplier_bill_list, name='list'),
    path('dashboard/', views.supplier_bill_dashboard, name='dashboard'),
    path('create/', views.supplier_bill_create, name='create'),
    path('<int:pk>/', views.supplier_bill_detail, name='detail'),
    path('<int:pk>/update/', views.supplier_bill_update, name='update'),
    path('<int:pk>/delete/', views.supplier_bill_delete, name='delete'),
    path('<int:pk>/print/', views.supplier_bill_print, name='print'),
    path('<int:pk>/email/', views.supplier_bill_email, name='email'),
    path('<int:pk>/update-status/', views.update_bill_status, name='update_status'),
] 