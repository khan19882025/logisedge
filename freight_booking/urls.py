from django.urls import path
from . import views

app_name = 'freight_booking'

urlpatterns = [
    # Main Booking URLs
    path('', views.FreightBookingListView.as_view(), name='booking_list'),
    path('create/', views.FreightBookingCreateView.as_view(), name='booking_create'),
    path('<int:pk>/', views.FreightBookingDetailView.as_view(), name='booking_detail'),
    path('<int:pk>/edit/', views.FreightBookingUpdateView.as_view(), name='booking_update'),
    path('<int:pk>/delete/', views.FreightBookingDeleteView.as_view(), name='booking_delete'),
    path('<int:booking_id>/summary/', views.booking_summary, name='booking_summary'),
    
    # Carrier URLs
    path('carriers/', views.CarrierListView.as_view(), name='carrier_list'),
    path('carriers/create/', views.CarrierCreateView.as_view(), name='carrier_create'),
    path('carriers/<int:pk>/edit/', views.CarrierUpdateView.as_view(), name='carrier_update'),
    path('carriers/<int:pk>/delete/', views.CarrierDeleteView.as_view(), name='carrier_delete'),
    
    # Booking Coordinator URLs
    path('coordinators/', views.BookingCoordinatorListView.as_view(), name='coordinator_list'),
    path('coordinators/create/', views.BookingCoordinatorCreateView.as_view(), name='coordinator_create'),
    path('coordinators/<int:pk>/edit/', views.BookingCoordinatorUpdateView.as_view(), name='coordinator_update'),
    path('coordinators/<int:pk>/delete/', views.BookingCoordinatorDeleteView.as_view(), name='coordinator_delete'),
    
    # Document Management
    path('<int:booking_id>/documents/add/', views.add_document, name='add_document'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    
    # Charge Management
    path('<int:booking_id>/charges/add/', views.add_charge, name='add_charge'),
    path('charges/<int:charge_id>/edit/', views.edit_charge, name='edit_charge'),
    path('charges/<int:charge_id>/delete/', views.delete_charge, name='delete_charge'),
    
    # Status Management
    path('<int:booking_id>/status/', views.change_status, name='change_status'),
    
    # AJAX URLs
    path('ajax/quotation/<int:quotation_id>/', views.get_quotation_details, name='get_quotation_details'),
    path('ajax/search-quotations/', views.search_quotations, name='search_quotations'),
    
    # Statistics
    path('statistics/', views.booking_statistics, name='statistics'),
]
