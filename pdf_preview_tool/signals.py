from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Document, DocumentType, PreviewSession, PreviewAction,
    DocumentAccessLog, PreviewSettings
)


@receiver(post_save, sender=Document)
def log_document_changes(sender, instance, created, **kwargs):
    """Log document creation and updates"""
    if created:
        # Document was created
        DocumentAccessLog.objects.create(
            document=instance,
            user=instance.created_by,
            access_type='preview',
            ip_address='',  # Will be filled by view
            user_agent='',  # Will be filled by view
            reason='Document created'
        )
    else:
        # Document was updated
        DocumentAccessLog.objects.create(
            document=instance,
            user=instance.updated_by,
            access_type='preview',
            ip_address='',  # Will be filled by view
            user_agent='',  # Will be filled by view
            reason='Document updated'
        )


@receiver(post_save, sender=DocumentType)
def log_document_type_changes(sender, instance, created, **kwargs):
    """Log document type changes"""
    action = 'created' if created else 'updated'
    # You could add logging here if needed


@receiver(post_save, sender=PreviewSession)
def log_preview_session_start(sender, instance, created, **kwargs):
    """Log when a preview session starts"""
    if created:
        # Log the session start
        PreviewAction.objects.create(
            session=instance,
            action_type='view_page',
            details={'action': 'session_started'},
            page_number=1
        )


@receiver(post_save, sender=PreviewAction)
def update_session_statistics(sender, instance, created, **kwargs):
    """Update session statistics when actions are logged"""
    if created and instance.session:
        session = instance.session
        
        # Update page view tracking
        if instance.action_type == 'view_page' and instance.page_number:
            if not session.pages_viewed:
                session.pages_viewed = []
            if instance.page_number not in session.pages_viewed:
                session.pages_viewed.append(instance.page_number)
        
        # Update zoom level tracking
        elif instance.action_type in ['zoom_in', 'zoom_out']:
            if not session.zoom_levels_used:
                session.zoom_levels_used = []
            zoom_level = instance.details.get('zoom_level')
            if zoom_level and zoom_level not in session.zoom_levels_used:
                session.zoom_levels_used.append(zoom_level)
        
        # Update search query tracking
        elif instance.action_type == 'search':
            if not session.search_queries:
                session.search_queries = []
            query = instance.details.get('query')
            if query and query not in session.search_queries:
                session.search_queries.append(query)
        
        # Update action counts
        elif instance.action_type == 'download':
            session.downloads_count += 1
        elif instance.action_type == 'print':
            session.print_count += 1
        elif instance.action_type == 'email':
            session.email_count += 1
        
        session.save()


@receiver(post_save, sender=User)
def create_user_preview_settings(sender, instance, created, **kwargs):
    """Create default preview settings for new users"""
    if created:
        PreviewSettings.objects.create(
            user=instance,
            default_zoom=100.0,
            show_thumbnails=True,
            auto_fit_page=True,
            enable_annotations=False,
            theme='light',
        )


@receiver(pre_save, sender=Document)
def validate_document_permissions(sender, instance, **kwargs):
    """Validate document permissions before saving"""
    # Ensure public documents don't have restricted access
    if instance.is_public:
        instance.allowed_roles = []
        # Don't clear allowed_users as they might still need access


@receiver(post_delete, sender=Document)
def cleanup_document_files(sender, instance, **kwargs):
    """Clean up document files when document is deleted"""
    # Here you would implement file cleanup logic
    # For now, we'll just log the deletion
    try:
        # Log the deletion
        DocumentAccessLog.objects.create(
            document=instance,
            user=User.objects.filter(is_superuser=True).first(),
            access_type='denied',
            ip_address='',
            user_agent='',
            reason='Document deleted'
        )
    except:
        pass  # Handle gracefully if logging fails


@receiver(post_save, sender=PreviewSettings)
def apply_user_preferences(sender, instance, created, **kwargs):
    """Apply user preferences to active sessions"""
    if not created:
        # Update active sessions with new settings
        active_sessions = PreviewSession.objects.filter(
            user=instance.user,
            ended_at__isnull=True
        )
        
        for session in active_sessions:
            # You could implement real-time updates here
            # For now, we'll just log the preference change
            PreviewAction.objects.create(
                session=session,
                action_type='view_page',
                details={
                    'action': 'preferences_updated',
                    'new_zoom': instance.default_zoom,
                    'new_layout': instance.default_page_layout,
                    'new_theme': instance.theme,
                }
            )


# Custom signal for document access events
from django.dispatch import Signal

# Signal emitted when a document is accessed
document_accessed = Signal()

# Signal emitted when a document is previewed
document_previewed = Signal()

# Signal emitted when a document is downloaded
document_downloaded = Signal()

# Signal emitted when a document is printed
document_printed = Signal()

# Signal emitted when a document is emailed
document_emailed = Signal()


@receiver(document_accessed)
def handle_document_access(sender, document, user, access_type, **kwargs):
    """Handle document access events"""
    # Log the access
    DocumentAccessLog.objects.create(
        document=document,
        user=user,
        access_type=access_type,
        ip_address=kwargs.get('ip_address', ''),
        user_agent=kwargs.get('user_agent', ''),
        reason=kwargs.get('reason', '')
    )


@receiver(document_previewed)
def handle_document_preview(sender, document, user, **kwargs):
    """Handle document preview events"""
    # You could implement analytics, notifications, etc. here
    pass


@receiver(document_downloaded)
def handle_document_download(sender, document, user, **kwargs):
    """Handle document download events"""
    # Log the download
    handle_document_access(
        sender=sender,
        document=document,
        user=user,
        access_type='download',
        **kwargs
    )


@receiver(document_printed)
def handle_document_print(sender, document, user, **kwargs):
    """Handle document print events"""
    # Log the print action
    handle_document_access(
        sender=sender,
        document=document,
        user=user,
        access_type='print',
        **kwargs
    )


@receiver(document_emailed)
def handle_document_email(sender, document, user, **kwargs):
    """Handle document email events"""
    # Log the email action
    handle_document_access(
        sender=sender,
        document=document,
        user=user,
        access_type='email',
        **kwargs
    )
