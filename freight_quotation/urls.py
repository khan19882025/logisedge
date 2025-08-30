from django.urls import path
from . import views

app_name = 'freight_quotation'

urlpatterns = [
    # Customer URLs
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    
    # Cargo Type URLs
    path('cargo-types/', views.CargoTypeListView.as_view(), name='cargo_type_list'),
    path('cargo-types/create/', views.CargoTypeCreateView.as_view(), name='cargo_type_create'),
    path('cargo-types/<int:pk>/edit/', views.CargoTypeUpdateView.as_view(), name='cargo_type_edit'),
    path('cargo-types/<int:pk>/delete/', views.CargoTypeDeleteView.as_view(), name='cargo_type_delete'),
    
    # Incoterm URLs
    path('incoterms/', views.IncotermListView.as_view(), name='incoterm_list'),
    path('incoterms/create/', views.IncotermCreateView.as_view(), name='incoterm_create'),
    path('incoterms/<int:pk>/edit/', views.IncotermUpdateView.as_view(), name='incoterm_edit'),
    path('incoterms/<int:pk>/delete/', views.IncotermDeleteView.as_view(), name='incoterm_delete'),
    
    # Charge Type URLs
    path('charge-types/', views.ChargeTypeListView.as_view(), name='charge_type_list'),
    path('charge-types/create/', views.ChargeTypeCreateView.as_view(), name='charge_type_create'),
    path('charge-types/<int:pk>/edit/', views.ChargeTypeUpdateView.as_view(), name='charge_type_edit'),
    path('charge-types/<int:pk>/delete/', views.ChargeTypeDeleteView.as_view(), name='charge_type_delete'),
    
    # Freight Quotation URLs
    path('', views.FreightQuotationListView.as_view(), name='quotation_list'),
    path('create/', views.FreightQuotationCreateView.as_view(), name='quotation_create'),
    path('<int:pk>/', views.FreightQuotationDetailView.as_view(), name='quotation_detail'),
    path('<int:pk>/edit/', views.FreightQuotationUpdateView.as_view(), name='quotation_edit'),
    path('<int:pk>/delete/', views.FreightQuotationDeleteView.as_view(), name='quotation_delete'),
    path('<int:pk>/clone/', views.clone_quotation, name='quotation_clone'),
    
    # Quotation Charges URLs
    path('<int:quotation_id>/charges/add/', views.add_charge, name='add_charge'),
    path('charges/<int:charge_id>/edit/', views.edit_charge, name='edit_charge'),
    path('charges/<int:charge_id>/delete/', views.delete_charge, name='delete_charge'),
    
    # Quotation Attachments URLs
    path('<int:quotation_id>/attachments/add/', views.add_attachment, name='add_attachment'),
    path('attachments/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    
    # Quotation Status Management
    path('<int:quotation_id>/change-status/', views.change_status, name='change_status'),
    
    # AJAX URLs
    path('ajax/customer/<int:customer_id>/', views.get_customer_details, name='get_customer_details'),
    
    # Statistics
    path('statistics/', views.quotation_statistics, name='statistics'),
] 