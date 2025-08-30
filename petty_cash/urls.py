from django.urls import path
from . import views

app_name = 'petty_cash'

urlpatterns = [
    # Main views
    path('', views.petty_cash_register, name='register'),
    path('list/', views.petty_cash_list, name='list'),
    path('create/', views.petty_cash_create, name='create'),
    path('quick/', views.quick_entry, name='quick'),
    path('<int:pk>/', views.petty_cash_detail, name='detail'),
    path('<int:pk>/edit/', views.petty_cash_edit, name='edit'),
    
    # Action views
    path('<int:pk>/submit/', views.petty_cash_submit, name='submit'),
    path('<int:pk>/approve/', views.petty_cash_approve, name='approve'),
    path('<int:pk>/lock/', views.petty_cash_lock, name='lock'),
    
    # AJAX endpoints
    path('ajax/previous-balance/', views.get_previous_balance, name='previous_balance'),
    path('ajax/summary/', views.petty_cash_summary, name='summary'),
    
    # Export endpoints
    path('export/excel/', views.export_petty_cash_excel, name='export_excel'),
    path('export/pdf/', views.export_petty_cash_pdf, name='export_pdf'),
]