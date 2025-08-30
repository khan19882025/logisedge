import json
import os
import uuid
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from .models import (
    Document, DocumentType, PreviewSession, PreviewAction,
    DocumentAccessLog, PreviewSettings, SignatureStamp
)
from .forms import (
    DocumentForm, DocumentTypeForm, DocumentSearchForm,
    PreviewSettingsForm, DocumentUploadForm, PrintDocumentForm
)
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import SignatureStampSerializer, SignatureStampUploadSerializer


@login_required
def dashboard(request):
    """Main dashboard for PDF Preview Tool"""
    # Get user's preview settings
    preview_settings, created = PreviewSettings.objects.get_or_create(user=request.user)
    
    # Get recent documents
    recent_documents = Document.objects.filter(
        Q(is_public=True) | Q(allowed_users=request.user)
    ).order_by('-created_at')[:10]
    
    # Get user's recent preview sessions
    recent_sessions = PreviewSession.objects.filter(
        user=request.user
    ).order_by('-started_at')[:5]
    
    # Get document statistics
    total_documents = Document.objects.filter(
        Q(is_public=True) | Q(allowed_users=request.user)
    ).count()
    
    documents_by_type = DocumentType.objects.annotate(
        doc_count=Count('documents')
    ).filter(doc_count__gt=0)
    
    # Get recent activity
    recent_activity = DocumentAccessLog.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]
    
    context = {
        'preview_settings': preview_settings,
        'recent_documents': recent_documents,
        'recent_sessions': recent_sessions,
        'total_documents': total_documents,
        'documents_by_type': documents_by_type,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'pdf_preview_tool/dashboard.html', context)


@login_required
def document_list(request):
    """List all accessible documents"""
    # Get search parameters
    search_form = DocumentSearchForm(request.GET)
    
    # Start with accessible documents
    documents = Document.objects.filter(
        Q(is_public=True) | Q(allowed_users=request.user)
    )
    
    # Apply search filters
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        document_type = search_form.cleaned_data.get('document_type')
        status = search_form.cleaned_data.get('status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        if query:
            # Search in title and description
            documents = documents.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        
        if document_type:
            documents = documents.filter(document_type=document_type)
        
        if status:
            documents = documents.filter(status=status)
        
        if date_from:
            documents = documents.filter(created_at__gte=date_from)
        
        if date_to:
            documents = documents.filter(created_at__lte=date_to)
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_documents': documents.count(),
    }
    
    return render(request, 'pdf_preview_tool/document_list.html', context)


@login_required
def document_detail(request, document_id):
    """Show document details and preview options"""
    document = get_object_or_404(Document, id=document_id)
    
    # Check access permissions
    if not document.is_accessible_by_user(request.user):
        # Log access denial
        DocumentAccessLog.objects.create(
            document=document,
            user=request.user,
            access_type='denied',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            reason='Insufficient permissions'
        )
        messages.error(request, "You don't have permission to access this document.")
        return redirect('pdf_preview_tool:document_list')
    
    # Log successful access
    DocumentAccessLog.objects.create(
        document=document,
        user=request.user,
        access_type='preview',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    # Get user's preview settings
    preview_settings, created = PreviewSettings.objects.get_or_create(user=request.user)
    
    # Get recent preview sessions for this document
    recent_sessions = PreviewSession.objects.filter(
        document=document,
        user=request.user
    ).order_by('-started_at')[:5]
    
    context = {
        'document': document,
        'preview_settings': preview_settings,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'pdf_preview_tool/document_detail.html', context)


@login_required
def document_preview(request, document_id):
    """Main PDF preview interface"""
    document = get_object_or_404(Document, id=document_id)
    
    # Check access permissions
    if not document.is_accessible_by_user(request.user):
        messages.error(request, "You don't have permission to access this document.")
        return redirect('pdf_preview_tool:document_list')
    
    # Create or get preview session
    preview_session, created = PreviewSession.objects.get_or_create(
        document=document,
        user=request.user,
        defaults={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR'),
        }
    )
    
    # Update session if document changed
    if preview_session.document != document:
        preview_session.document = document
        preview_session.save()
    
    # Get user's preview settings
    preview_settings, created = PreviewSettings.objects.get_or_create(user=request.user)
    
    context = {
        'document': document,
        'preview_session': preview_session,
        'preview_settings': preview_settings,
    }
    
    return render(request, 'pdf_preview_tool/document_preview.html', context)


@login_required
def document_create(request):
    """Create a new document"""
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            document = form.save(commit=False)
            document.created_by = request.user
            document.updated_by = request.user
            document.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f"Document '{document.title}' created successfully.")
            return redirect('pdf_preview_tool:document_detail', document_id=document.id)
    else:
        form = DocumentForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'pdf_preview_tool/document_form.html', context)


@login_required
def document_update(request, document_id):
    """Update an existing document"""
    document = get_object_or_404(Document, id=document_id)
    
    # Check if user can edit this document
    if not (request.user == document.created_by or request.user.is_staff):
        messages.error(request, "You don't have permission to edit this document.")
        return redirect('pdf_preview_tool:document_detail', document_id=document.id)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            document.updated_by = request.user
            document.save()
            form.save_m2m()
            
            messages.success(request, f"Document '{document.title}' updated successfully.")
            return redirect('pdf_preview_tool:document_detail', document_id=document.id)
    else:
        form = DocumentForm(instance=document)
    
    context = {
        'form': form,
        'document': document,
        'action': 'Update',
    }
    
    return render(request, 'pdf_preview_tool/document_form.html', context)


@login_required
def document_upload(request):
    """Upload a new document"""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle file upload
            uploaded_file = form.cleaned_data['file']
            
            # Create document record
            document = Document(
                title=form.cleaned_data['title'],
                document_type=form.cleaned_data['document_type'],
                description=form.cleaned_data['description'],
                is_public=form.cleaned_data['is_public'],
                created_by=request.user,
                updated_by=request.user,
            )
            
            # Process tags
            tags = form.cleaned_data.get('tags', '')
            if tags:
                document.tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Set file information
            document.file_path = f"uploads/{uploaded_file.name}"
            document.file_size = uploaded_file.size
            
            # Determine page count (for PDFs)
            if uploaded_file.name.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    document.page_count = len(pdf_reader.pages)
                except:
                    document.page_count = 1
            else:
                document.page_count = 1
            
            document.save()
            
            # Add user to allowed users
            document.allowed_users.add(request.user)
            
            messages.success(request, f"Document '{document.title}' uploaded successfully.")
            return redirect('pdf_preview_tool:document_detail', document_id=document.id)
    else:
        form = DocumentUploadForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'pdf_preview_tool/document_upload.html', context)


@login_required
def document_type_list(request):
    """List all document types"""
    document_types = DocumentType.objects.all()
    
    context = {
        'document_types': document_types,
    }
    
    return render(request, 'pdf_preview_tool/document_type_list.html', context)


@login_required
def document_type_create(request):
    """Create a new document type"""
    if request.method == 'POST':
        form = DocumentTypeForm(request.POST)
        if form.is_valid():
            document_type = form.save()
            messages.success(request, f"Document type '{document_type.name}' created successfully.")
            return redirect('pdf_preview_tool:document_type_list')
    else:
        form = DocumentTypeForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'pdf_preview_tool/document_type_form.html', context)


@login_required
def preview_settings(request):
    """User's preview settings"""
    preview_settings, created = PreviewSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PreviewSettingsForm(request.POST, instance=preview_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Preview settings updated successfully.")
            return redirect('pdf_preview_tool:preview_settings')
    else:
        form = PreviewSettingsForm(instance=preview_settings)
    
    context = {
        'form': form,
        'preview_settings': preview_settings,
    }
    
    return render(request, 'pdf_preview_tool/preview_settings.html', context)


@login_required
def print_document(request, document_id):
    """Print a document"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        form = PrintDocumentForm(request.POST)
        if form.is_valid():
            # Here you would implement the actual printing logic
            # For now, we'll just log the action
            page_range = form.cleaned_data['page_range']
            copies = form.cleaned_data['copies']
            
            # Log the print action
            PreviewAction.objects.create(
                session=PreviewSession.objects.filter(
                    user=request.user,
                    document=document
                ).first(),
                action_type='print',
                details={
                    'page_range': page_range,
                    'copies': copies,
                    'orientation': form.cleaned_data['orientation'],
                }
            )
            
            messages.success(request, f"Document '{document.title}' sent to print")
            return redirect('pdf_preview_tool:document_detail', document_id=document.id)
    else:
        form = PrintDocumentForm()
    
    context = {
        'form': form,
        'document': document,
    }
    
    return render(request, 'pdf_preview_tool/print_document.html', context)


# API Views for React integration
@csrf_exempt
@require_http_methods(["POST"])
def api_start_preview_session(request, document_id):
    """API endpoint to start a preview session"""
    try:
        data = json.loads(request.body)
        document = get_object_or_404(Document, id=document_id)
        
        # Check access permissions
        if not document.is_accessible_by_user(request.user):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Create preview session
        preview_session = PreviewSession.objects.create(
            document=document,
            user=request.user,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        
        return JsonResponse({
            'session_id': str(preview_session.id),
            'document_id': str(document.id),
            'status': 'started'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_log_preview_action(request, session_id):
    """API endpoint to log preview actions"""
    try:
        data = json.loads(request.body)
        action_type = data.get('action_type')
        details = data.get('details', {})
        
        # Find the preview session
        try:
            preview_session = PreviewSession.objects.get(id=session_id)
        except PreviewSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        # Create action log
        PreviewAction.objects.create(
            session=preview_session,
            action_type=action_type,
            details=details,
        )
        
        return JsonResponse({'status': 'logged'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_end_preview_session(request, session_id):
    """API endpoint to end a preview session"""
    try:
        # Find and end the preview session
        try:
            preview_session = PreviewSession.objects.get(id=session_id)
        except PreviewSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        
        preview_session.end_session()
        
        return JsonResponse({'status': 'ended'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_document_info(request, document_id):
    """API endpoint to get document information"""
    try:
        document = get_object_or_404(Document, id=document_id)
        
        # Check access permissions
        if not document.is_accessible_by_user(request.user):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Return document info
        return JsonResponse({
            'id': str(document.id),
            'title': document.title,
            'document_type': document.document_type.name,
            'file_path': document.file_path,
            'file_size': document.file_size,
            'page_count': document.page_count,
            'status': document.status,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_user_preview_settings(request):
    """API endpoint to get user's preview settings"""
    try:
        preview_settings, created = PreviewSettings.objects.get_or_create(user=request.user)
        
        return JsonResponse({
            'default_zoom': preview_settings.default_zoom,
            'show_thumbnails': preview_settings.show_thumbnails,
            'auto_fit_page': preview_settings.auto_fit_page,
            'enable_annotations': preview_settings.enable_annotations,
            'theme': preview_settings.theme,
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_update_preview_settings(request):
    """API endpoint to update user's preview settings"""
    try:
        data = json.loads(request.body)
        preview_settings, created = PreviewSettings.objects.get_or_create(user=request.user)
        
        # Update settings
        for field, value in data.items():
            if hasattr(preview_settings, field):
                setattr(preview_settings, field, value)
        
        preview_settings.save()
        
        return JsonResponse({'status': 'updated'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class SignatureStampViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user signatures and stamps.
    Users can only access their own signature/stamp.
    """
    serializer_class = SignatureStampSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Users can only see their own signature/stamp"""
        return SignatureStamp.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user when creating a signature/stamp"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='my-signature')
    def my_signature(self, request):
        """Get the current user's signature/stamp"""
        try:
            signature = SignatureStamp.objects.get(user=request.user)
            serializer = self.get_serializer(signature)
            return Response(serializer.data)
        except SignatureStamp.DoesNotExist:
            return Response(
                {'message': 'No signature/stamp found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_signature(self, request):
        """Upload a new signature/stamp file"""
        serializer = SignatureStampUploadSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Check if user already has a signature
                existing_signature = SignatureStamp.objects.filter(user=request.user).first()
                
                if existing_signature:
                    # Update existing signature
                    existing_signature.file = serializer.validated_data['file']
                    existing_signature.save()
                    response_serializer = SignatureStampSerializer(existing_signature, context={'request': request})
                    return Response(
                        {
                            'message': 'Signature/stamp updated successfully.',
                            'data': response_serializer.data
                        },
                        status=status.HTTP_200_OK
                    )
                else:
                    # Create new signature
                    signature = serializer.save(user=request.user)
                    response_serializer = SignatureStampSerializer(signature, context={'request': request})
                    return Response(
                        {
                            'message': 'Signature/stamp uploaded successfully.',
                            'data': response_serializer.data
                        },
                        status=status.HTTP_201_CREATED
                    )
            except Exception as e:
                return Response(
                    {'error': f'Failed to upload signature: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'], url_path='delete')
    def delete_signature(self, request):
        """Delete the current user's signature/stamp"""
        try:
            signature = SignatureStamp.objects.get(user=request.user)
            signature.delete()
            return Response(
                {'message': 'Signature/stamp deleted successfully.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except SignatureStamp.DoesNotExist:
            return Response(
                {'message': 'No signature/stamp found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )


@login_required
def signature_uploader_view(request):
    """View for the signature/stamp uploader interface"""
    return render(request, 'pdf_preview_tool/signature_uploader.html')
