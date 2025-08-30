from django.urls import path
from . import views

app_name = 'putaways'

urlpatterns = [
    path('', views.putaway_list, name='putaway_list'),
    path('create/', views.putaway_create, name='putaway_create'),
    path('<int:pk>/', views.putaway_detail, name='putaway_detail'),
    path('<int:pk>/edit/', views.putaway_edit, name='putaway_edit'),
    path('<int:pk>/delete/', views.putaway_delete, name='putaway_delete'),
    path('<int:pk>/status/', views.putaway_status_update, name='putaway_status_update'),
    path('get-grn-items/<int:grn_id>/', views.get_grn_items, name='get_grn_items'),
    path('get-grn-pallets/<int:grn_id>/', views.get_grn_pallets, name='get_grn_pallets'),
    path('get-pallet-details/<int:grn_id>/<str:pallet_id>/', views.get_pallet_details, name='get_pallet_details'),
] 