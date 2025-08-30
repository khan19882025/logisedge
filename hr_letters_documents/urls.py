from django.urls import path
from . import views

app_name = 'hr_letters_documents'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Letter Types
    path('letter-types/', views.LetterTypeListView.as_view(), name='letter_type_list'),
    path('letter-types/create/', views.LetterTypeCreateView.as_view(), name='letter_type_create'),
    path('letter-types/<int:pk>/update/', views.LetterTypeUpdateView.as_view(), name='letter_type_update'),
    path('letter-types/<int:pk>/delete/', views.LetterTypeDeleteView.as_view(), name='letter_type_delete'),
    
    # Letter Templates
    path('templates/', views.LetterTemplateListView.as_view(), name='letter_template_list'),
    path('templates/create/', views.LetterTemplateCreateView.as_view(), name='letter_template_create'),
    path('templates/<int:pk>/update/', views.LetterTemplateUpdateView.as_view(), name='letter_template_update'),
    path('templates/<int:pk>/delete/', views.LetterTemplateDeleteView.as_view(), name='letter_template_delete'),
    
    # Generated Letters
    path('letters/', views.GeneratedLetterListView.as_view(), name='letter_list'),
    path('letters/create/', views.letter_create, name='letter_create'),
    path('letters/<int:pk>/', views.GeneratedLetterDetailView.as_view(), name='letter_detail'),
    path('letters/<int:pk>/edit/', views.letter_edit, name='letter_edit'),
    path('letters/<int:pk>/finalize/', views.letter_finalize, name='letter_finalize'),
    path('letters/<int:pk>/sign/', views.letter_sign, name='letter_sign'),
    path('letters/<int:pk>/delete/', views.letter_delete, name='letter_delete'),
    
    # Bulk Letter Generation
    path('letters/bulk-generate/', views.bulk_letter_generation, name='bulk_letter_generation'),
    
    # Document Categories
    path('document-categories/', views.DocumentCategoryListView.as_view(), name='document_category_list'),
    path('document-categories/create/', views.DocumentCategoryCreateView.as_view(), name='document_category_create'),
    path('document-categories/<int:pk>/update/', views.DocumentCategoryUpdateView.as_view(), name='document_category_update'),
    path('document-categories/<int:pk>/delete/', views.DocumentCategoryDeleteView.as_view(), name='document_category_delete'),
    
    # HR Documents
    path('documents/', views.HRDocumentListView.as_view(), name='hr_document_list'),
    path('documents/create/', views.HRDocumentCreateView.as_view(), name='hr_document_create'),
    path('documents/<int:pk>/update/', views.HRDocumentUpdateView.as_view(), name='hr_document_update'),
    path('documents/<int:pk>/delete/', views.HRDocumentDeleteView.as_view(), name='hr_document_delete'),
    
    # AJAX endpoints
    path('ajax/templates/', views.get_templates_for_letter_type, name='get_templates_for_letter_type'),
    path('ajax/template-details/', views.get_template_details, name='get_template_details'),
    path('ajax/employee-details/', views.get_employee_details, name='get_employee_details'),
    path('ajax/preview-letter/', views.preview_letter, name='preview_letter'),
] 