from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import (
    NotificationTemplate, TemplateVersion, TemplateAuditLog,
    TemplateCategory, TemplatePlaceholder
)


@receiver(post_save, sender=NotificationTemplate)
def create_template_version(sender, instance, created, **kwargs):
    """Create a new version when template content changes"""
    if not created:  # Only for updates
        # Check if content has changed
        try:
            old_instance = NotificationTemplate.objects.get(pk=instance.pk)
            if (old_instance.content != instance.content or 
                old_instance.html_content != instance.html_content or
                old_instance.subject != instance.subject):
                
                # Create version record
                TemplateVersion.objects.create(
                    template=instance,
                    version_number=instance.version,
                    content=old_instance.content,
                    html_content=old_instance.html_content,
                    subject=old_instance.subject,
                    changed_by=instance.updated_by,
                    change_reason=getattr(instance, '_change_reason', '')
                )
        except NotificationTemplate.DoesNotExist:
            pass


@receiver(post_save, sender=NotificationTemplate)
def log_template_audit(sender, instance, created, **kwargs):
    """Log template creation and updates"""
    if created:
        action = 'created'
        old_values = {}
        new_values = {
            'name': instance.name,
            'template_type': instance.template_type,
            'category': instance.category.name if instance.category else None,
            'content': instance.content,
            'html_content': instance.html_content,
            'subject': instance.subject,
            'language': instance.language,
        }
    else:
        action = 'updated'
        # Get old values from the instance's _old_values attribute
        old_values = getattr(instance, '_old_values', {})
        new_values = {
            'name': instance.name,
            'template_type': instance.template_type,
            'category': instance.category.name if instance.category else None,
            'content': instance.content,
            'html_content': instance.html_content,
            'subject': instance.subject,
            'language': instance.language,
        }
    
    # Create audit log entry
    TemplateAuditLog.objects.create(
        template=instance,
        action=action,
        user=instance.updated_by if not created else instance.created_by,
        old_values=old_values,
        new_values=new_values,
        change_reason=getattr(instance, '_change_reason', ''),
        ip_address=getattr(instance, '_ip_address', ''),
        user_agent=getattr(instance, '_user_agent', '')
    )


@receiver(post_delete, sender=NotificationTemplate)
def log_template_deletion(sender, instance, **kwargs):
    """Log template deletion"""
    # Note: We can't access the user here directly, so we'll use a system user
    # In a real implementation, you might want to store the user in the instance
    # before deletion or use a different approach
    
    TemplateAuditLog.objects.create(
        template=instance,
        action='deleted',
        user=User.objects.filter(is_superuser=True).first(),  # Fallback to superuser
        old_values={
            'name': instance.name,
            'template_type': instance.template_type,
            'category': instance.category.name if instance.category else None,
            'content': instance.content,
            'html_content': instance.html_content,
            'subject': instance.subject,
            'language': instance.language,
        },
        new_values={},
        change_reason='Template deleted',
        ip_address='',
        user_agent=''
    )


@receiver(post_save, sender=TemplateCategory)
def log_category_changes(sender, instance, created, **kwargs):
    """Log category creation and updates"""
    if created:
        action = 'created'
        old_values = {}
        new_values = {
            'name': instance.name,
            'description': instance.description,
            'color': instance.color,
            'icon': instance.icon,
            'is_active': instance.is_active
        }
    else:
        action = 'updated'
        # Get old values from the instance's _old_values attribute
        old_values = getattr(instance, '_old_values', {})
        new_values = {
            'name': instance.name,
            'description': instance.description,
            'color': instance.color,
            'icon': instance.icon,
            'is_active': instance.is_active
        }
    
    # Create audit log entry for category changes
    # Note: This is a simplified version - you might want to create a separate
    # audit model for categories or handle this differently
    
    # For now, we'll just log it in the template audit log if there are templates
    if instance.templates.exists():
        for template in instance.templates.all():
            TemplateAuditLog.objects.create(
                template=template,
                action=f'category_{action}',
                user=User.objects.filter(is_superuser=True).first(),  # Fallback
                old_values=old_values,
                new_values=new_values,
                change_reason=f'Category {action}: {instance.name}',
                ip_address='',
                user_agent=''
            )


@receiver(post_save, sender=TemplatePlaceholder)
def log_placeholder_changes(sender, instance, created, **kwargs):
    """Log placeholder creation and updates"""
    if created:
        action = 'created'
        old_values = {}
        new_values = {
            'name': instance.name,
            'display_name': instance.display_name,
            'description': instance.description,
            'placeholder_type': instance.placeholder_type,
            'data_type': instance.data_type,
            'format_string': instance.format_string,
            'example_value': instance.example_value,
            'is_active': instance.is_active,
            'is_required': instance.is_required
        }
    else:
        action = 'updated'
        # Get old values from the instance's _old_values attribute
        old_values = getattr(instance, '_old_values', {})
        new_values = {
            'name': instance.name,
            'display_name': instance.display_name,
            'description': instance.description,
            'placeholder_type': instance.placeholder_type,
            'data_type': instance.data_type,
            'format_string': instance.format_string,
            'example_value': instance.example_value,
            'is_active': instance.is_active,
            'is_required': instance.is_required
        }
    
    # Log placeholder changes in template audit logs for affected templates
    # This is a simplified approach - you might want to handle this differently
    
    # Find templates that use this placeholder
    # Use a different approach for SQLite compatibility
    affected_templates = []
    try:
        # Try to use contains lookup if supported
        affected_templates = list(NotificationTemplate.objects.filter(
            placeholders__contains=[instance.name]
        ))
    except Exception:
        # Fallback: manually check templates
        for template in NotificationTemplate.objects.all():
            if template.placeholders and instance.name in template.placeholders:
                affected_templates.append(template)
    
    for template in affected_templates:
        TemplateAuditLog.objects.create(
            template=template,
            action=f'placeholder_{action}',
            user=User.objects.filter(is_superuser=True).first(),  # Fallback
            old_values=old_values,
            new_values=new_values,
            change_reason=f'Placeholder {action}: {instance.name}',
            ip_address='',
            user_agent=''
        )


# Signal to capture old values before saving
@receiver(pre_save, sender=NotificationTemplate)
def capture_old_values(sender, instance, **kwargs):
    """Capture old values before saving for audit logging"""
    if instance.pk:  # Only for updates
        try:
            old_instance = NotificationTemplate.objects.get(pk=instance.pk)
            instance._old_values = {
                'name': old_instance.name,
                'template_type': old_instance.template_type,
                'category': old_instance.category.name if old_instance.category else None,
                'content': old_instance.content,
                'html_content': old_instance.html_content,
                'subject': old_instance.subject,
                'language': old_instance.language,
            }
        except NotificationTemplate.DoesNotExist:
            instance._old_values = {}


@receiver(pre_save, sender=TemplateCategory)
def capture_category_old_values(sender, instance, **kwargs):
    """Capture old category values before saving"""
    if instance.pk:  # Only for updates
        try:
            old_instance = TemplateCategory.objects.get(pk=instance.pk)
            instance._old_values = {
                'name': old_instance.name,
                'description': old_instance.description,
                'color': old_instance.color,
                'icon': old_instance.icon,
                'is_active': old_instance.is_active
            }
        except TemplateCategory.DoesNotExist:
            instance._old_values = {}


@receiver(pre_save, sender=TemplatePlaceholder)
def capture_placeholder_old_values(sender, instance, **kwargs):
    """Capture old placeholder values before saving"""
    if instance.pk:  # Only for updates
        try:
            old_instance = TemplatePlaceholder.objects.get(pk=instance.pk)
            instance._old_values = {
                'name': old_instance.name,
                'display_name': old_instance.display_name,
                'description': old_instance.description,
                'placeholder_type': old_instance.placeholder_type,
                'data_type': old_instance.data_type,
                'format_string': old_instance.format_string,
                'example_value': old_instance.example_value,
                'is_active': old_instance.is_active,
                'is_required': old_instance.is_required
            }
        except TemplatePlaceholder.DoesNotExist:
            instance._old_values = {}


# Signal to handle template approval
@receiver(post_save, sender=NotificationTemplate)
def handle_template_approval(sender, instance, **kwargs):
    """Handle template approval workflow"""
    if instance.requires_approval and instance.is_approved:
        # Log approval
        TemplateAuditLog.objects.create(
            template=instance,
            action='approved',
            user=instance.approved_by,
            old_values={'is_approved': False},
            new_values={'is_approved': True},
            change_reason='Template approved',
            ip_address='',
            user_agent=''
        )
        
        # You could add additional logic here, such as:
        # - Sending notifications to stakeholders
        # - Updating related systems
        # - Triggering workflows


# Signal to handle template activation/deactivation
@receiver(post_save, sender=NotificationTemplate)
def handle_template_status_change(sender, instance, **kwargs):
    """Handle template activation/deactivation"""
    if hasattr(instance, '_old_values'):
        old_is_active = instance._old_values.get('is_active', False)
        if old_is_active != instance.is_active:
            action = 'activated' if instance.is_active else 'deactivated'
            
            TemplateAuditLog.objects.create(
                template=instance,
                action=action,
                user=instance.updated_by,
                old_values={'is_active': old_is_active},
                new_values={'is_active': instance.is_active},
                change_reason=f'Template {action}',
                ip_address='',
                user_agent=''
            )


# Signal to handle placeholder updates in templates
@receiver(post_save, sender=TemplatePlaceholder)
def update_template_placeholders(sender, instance, **kwargs):
    """Update template placeholders when placeholder is modified"""
    if not instance.is_active:
        # If placeholder is deactivated, remove it from templates
        templates = NotificationTemplate.objects.filter(
            placeholders__contains=[instance.name]
        )
        
        for template in templates:
            if instance.name in template.placeholders:
                template.placeholders.remove(instance.name)
                template.save(update_fields=['placeholders'])
                
                # Log the change
                TemplateAuditLog.objects.create(
                    template=template,
                    action='placeholder_removed',
                    user=User.objects.filter(is_superuser=True).first(),
                    old_values={'placeholders': template.placeholders + [instance.name]},
                    new_values={'placeholders': template.placeholders},
                    change_reason=f'Placeholder "{instance.name}" deactivated and removed',
                    ip_address='',
                    user_agent=''
                )
