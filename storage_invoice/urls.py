from django.urls import path
from . import views

app_name = 'storage_invoice'

urlpatterns = [
    # Storage Invoice Management
    path('', views.storage_invoice_list, name='storage_invoice_list'),
    path('create/', views.generate_invoice, name='generate_invoice'),
    path('<int:pk>/', views.storage_invoice_detail, name='storage_invoice_detail'),
    path('<int:pk>/edit/', views.storage_invoice_edit, name='storage_invoice_edit'),
    path('<int:pk>/finalize/', views.storage_invoice_finalize, name='storage_invoice_finalize'),
    path('<int:pk>/cancel/', views.storage_invoice_cancel, name='storage_invoice_cancel'),
] 