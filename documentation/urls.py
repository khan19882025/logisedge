from django.urls import path
from .views import (
    DocumentationListView, DocumentationDetailView, DocumentationCreateView,
    DocumentationUpdateView, DocumentationDeleteView, get_customer_cargo,
    print_invoice, print_packing_list, print_da, print_too_letter,
    email_invoice, email_packing_list, email_da, email_too_letter,
    bulk_print, bulk_email
)

app_name = 'documentation'

urlpatterns = [
    # CRUD operations
    path('', DocumentationListView.as_view(), name='documentation_list'),
    path('create/', DocumentationCreateView.as_view(), name='documentation_create'),
    path('<int:pk>/', DocumentationDetailView.as_view(), name='documentation_detail'),
    path('<int:pk>/edit/', DocumentationUpdateView.as_view(), name='documentation_update'),
    path('<int:pk>/delete/', DocumentationDeleteView.as_view(), name='documentation_delete'),
    
    # Print views
    path('<int:pk>/print/invoice/', print_invoice, name='print_invoice'),
    path('<int:pk>/print/packing-list/', print_packing_list, name='print_packing_list'),
    path('<int:pk>/print/da/', print_da, name='print_da'),
    path('<int:pk>/print/too-letter/', print_too_letter, name='print_too_letter'),
    
    # Email views
    path('<int:pk>/email/invoice/', email_invoice, name='email_invoice'),
    path('<int:pk>/email/packing-list/', email_packing_list, name='email_packing_list'),
    path('<int:pk>/email/da/', email_da, name='email_da'),
    path('<int:pk>/email/too-letter/', email_too_letter, name='email_too_letter'),
    
    # Bulk operations
    path('bulk-print/', bulk_print, name='bulk_print'),
    path('bulk-email/', bulk_email, name='bulk_email'),
    
    # AJAX endpoints
    path('get-customer-cargo/<int:customer_id>/', get_customer_cargo, name='get_customer_cargo'),
] 