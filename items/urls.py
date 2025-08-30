from django.urls import path
from . import views

app_name = 'items'

urlpatterns = [
    # Function-based views
    path('', views.item_list, name='item_list'),
    path('create/', views.item_create, name='item_create'),
    path('<int:pk>/', views.item_detail, name='item_detail'),
    path('<int:pk>/update/', views.item_update, name='item_update'),
    path('<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('<int:pk>/quick-view/', views.item_quick_view, name='item_quick_view'),
    path('<int:pk>/toggle-status/', views.item_status_toggle, name='item_status_toggle'),
    path('export/', views.item_export, name='item_export'),
    
    # Class-based views (alternative)
    # path('', views.ItemListView.as_view(), name='item_list'),
    # path('create/', views.ItemCreateView.as_view(), name='item_create'),
    # path('<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    # path('<int:pk>/update/', views.ItemUpdateView.as_view(), name='item_update'),
    # path('<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
] 