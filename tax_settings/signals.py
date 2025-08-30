from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    TaxJurisdiction, TaxType, TaxRate, ProductTaxCategory,
    CustomerTaxProfile, SupplierTaxProfile, TaxSettingsAuditLog
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit_change(sender, instance, action, field_name=None, old_value=None, new_value=None, request=None):
    """Log changes to audit log"""
    if hasattr(instance, '_current_user') and instance._current_user:
        user = instance._current_user
    else:
        # Try to get user from request
        user = None
        if request and hasattr(request, 'user'):
            user = request.user
    
    ip_address = None
    if request:
        ip_address = get_client_ip(request)
    
    TaxSettingsAuditLog.objects.create(
        model_name=sender.__name__,
        object_id=str(instance.pk),
        action=action,
        field_name=field_name or '',
        old_value=str(old_value) if old_value is not None else '',
        new_value=str(new_value) if new_value is not None else '',
        user=user,
        ip_address=ip_address
    )


@receiver(pre_save, sender=TaxJurisdiction)
def tax_jurisdiction_pre_save(sender, instance, **kwargs):
    """Log changes to TaxJurisdiction"""
    if instance.pk:  # Update
        try:
            old_instance = TaxJurisdiction.objects.get(pk=instance.pk)
            for field in ['name', 'code', 'jurisdiction_type', 'is_active']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    log_audit_change(
                        sender, instance, 'update', 
                        field_name=field, 
                        old_value=old_value, 
                        new_value=new_value
                    )
        except TaxJurisdiction.DoesNotExist:
            pass
    else:  # Create
        log_audit_change(sender, instance, 'create')


@receiver(pre_save, sender=TaxType)
def tax_type_pre_save(sender, instance, **kwargs):
    """Log changes to TaxType"""
    if instance.pk:  # Update
        try:
            old_instance = TaxType.objects.get(pk=instance.pk)
            for field in ['name', 'code', 'tax_type', 'description', 'is_active']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    log_audit_change(
                        sender, instance, 'update', 
                        field_name=field, 
                        old_value=old_value, 
                        new_value=new_value
                    )
        except TaxType.DoesNotExist:
            pass
    else:  # Create
        log_audit_change(sender, instance, 'create')


@receiver(pre_save, sender=TaxRate)
def tax_rate_pre_save(sender, instance, **kwargs):
    """Log changes to TaxRate"""
    if instance.pk:  # Update
        try:
            old_instance = TaxRate.objects.get(pk=instance.pk)
            for field in ['name', 'rate_percentage', 'effective_from', 'effective_to', 'rounding_method', 'is_active']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    log_audit_change(
                        sender, instance, 'update', 
                        field_name=field, 
                        old_value=old_value, 
                        new_value=new_value
                    )
        except TaxRate.DoesNotExist:
            pass
    else:  # Create
        log_audit_change(sender, instance, 'create')


@receiver(pre_save, sender=ProductTaxCategory)
def product_tax_category_pre_save(sender, instance, **kwargs):
    """Log changes to ProductTaxCategory"""
    if instance.pk:  # Update
        try:
            old_instance = ProductTaxCategory.objects.get(pk=instance.pk)
            for field in ['name', 'code', 'description', 'is_active']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    log_audit_change(
                        sender, instance, 'update', 
                        field_name=field, 
                        old_value=old_value, 
                        new_value=new_value
                    )
        except ProductTaxCategory.DoesNotExist:
            pass
    else:  # Create
        log_audit_change(sender, instance, 'create')


@receiver(pre_save, sender=CustomerTaxProfile)
def customer_tax_profile_pre_save(sender, instance, **kwargs):
    """Log changes to CustomerTaxProfile"""
    if instance.pk:  # Update
        try:
            old_instance = CustomerTaxProfile.objects.get(pk=instance.pk)
            for field in ['tax_registration_number', 'tax_exemption_number', 'is_tax_exempt', 'tax_exemption_reason']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    log_audit_change(
                        sender, instance, 'update', 
                        field_name=field, 
                        old_value=old_value, 
                        new_value=new_value
                    )
        except CustomerTaxProfile.DoesNotExist:
            pass
    else:  # Create
        log_audit_change(sender, instance, 'create')


@receiver(pre_save, sender=SupplierTaxProfile)
def supplier_tax_profile_pre_save(sender, instance, **kwargs):
    """Log changes to SupplierTaxProfile"""
    if instance.pk:  # Update
        try:
            old_instance = SupplierTaxProfile.objects.get(pk=instance.pk)
            for field in ['tax_registration_number', 'tax_exemption_number', 'is_tax_exempt', 'tax_exemption_reason']:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    log_audit_change(
                        sender, instance, 'update', 
                        field_name=field, 
                        old_value=old_value, 
                        new_value=new_value
                    )
        except SupplierTaxProfile.DoesNotExist:
            pass
    else:  # Create
        log_audit_change(sender, instance, 'create')


@receiver(pre_delete, sender=TaxJurisdiction)
def tax_jurisdiction_pre_delete(sender, instance, **kwargs):
    """Log deletion of TaxJurisdiction"""
    log_audit_change(sender, instance, 'delete')


@receiver(pre_delete, sender=TaxType)
def tax_type_pre_delete(sender, instance, **kwargs):
    """Log deletion of TaxType"""
    log_audit_change(sender, instance, 'delete')


@receiver(pre_delete, sender=TaxRate)
def tax_rate_pre_delete(sender, instance, **kwargs):
    """Log deletion of TaxRate"""
    log_audit_change(sender, instance, 'delete')


@receiver(pre_delete, sender=ProductTaxCategory)
def product_tax_category_pre_delete(sender, instance, **kwargs):
    """Log deletion of ProductTaxCategory"""
    log_audit_change(sender, instance, 'delete')


@receiver(pre_delete, sender=CustomerTaxProfile)
def customer_tax_profile_pre_delete(sender, instance, **kwargs):
    """Log deletion of CustomerTaxProfile"""
    log_audit_change(sender, instance, 'delete')


@receiver(pre_delete, sender=SupplierTaxProfile)
def supplier_tax_profile_pre_delete(sender, instance, **kwargs):
    """Log deletion of SupplierTaxProfile"""
    log_audit_change(sender, instance, 'delete')
