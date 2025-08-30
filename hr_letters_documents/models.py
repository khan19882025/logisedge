from django.db import models
from django.contrib.auth.models import User
from employees.models import Employee
from django.utils import timezone
import uuid


class LetterType(models.Model):
    """Model for different types of HR letters"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Letter Type'
        verbose_name_plural = 'Letter Types'

    def __str__(self):
        return self.name


class LetterTemplate(models.Model):
    """Model for letter templates with placeholders"""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('both', 'English & Arabic'),
    ]
    
    letter_type = models.ForeignKey(LetterType, on_delete=models.CASCADE, related_name='templates')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    content = models.TextField(help_text="Use placeholders like {{employee_name}}, {{designation}}, {{salary}}, etc.")
    arabic_content = models.TextField(blank=True, help_text="Arabic version of the content")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Letter Template'
        verbose_name_plural = 'Letter Templates'

    def __str__(self):
        return f"{self.letter_type.name} - {self.get_language_display()}"


class GeneratedLetter(models.Model):
    """Model for generated letters"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('finalized', 'Finalized'),
        ('signed', 'Signed'),
        ('issued', 'Issued'),
    ]
    
    reference_number = models.CharField(max_length=50, unique=True)
    letter_type = models.ForeignKey(LetterType, on_delete=models.CASCADE)
    template = models.ForeignKey(LetterTemplate, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='hr_letters')
    
    # Letter content
    subject = models.CharField(max_length=200)
    content = models.TextField()
    arabic_content = models.TextField(blank=True)
    
    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateField(default=timezone.now)
    effective_date = models.DateField(null=True, blank=True)
    
    # File management
    pdf_file = models.FileField(upload_to='hr_letters/', null=True, blank=True)
    signed_pdf = models.FileField(upload_to='hr_letters/signed/', null=True, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_letters')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='finalized_letters')
    finalized_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='signed_letters')
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional fields
    notes = models.TextField(blank=True)
    is_confidential = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Generated Letter'
        verbose_name_plural = 'Generated Letters'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_number} - {self.employee.full_name} - {self.letter_type.name}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            # Generate unique reference number
            self.reference_number = f"HR-{self.letter_type.name.upper()[:3]}-{timezone.now().strftime('%Y%m')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class LetterPlaceholder(models.Model):
    """Model for managing letter placeholders and their values"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    default_value = models.CharField(max_length=200, blank=True)
    is_required = models.BooleanField(default=True)
    field_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('date', 'Date'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('phone', 'Phone'),
    ], default='text')
    
    class Meta:
        verbose_name = 'Letter Placeholder'
        verbose_name_plural = 'Letter Placeholders'

    def __str__(self):
        return self.name


class LetterApproval(models.Model):
    """Model for letter approval workflow"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    letter = models.ForeignKey(GeneratedLetter, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='letter_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Letter Approval'
        verbose_name_plural = 'Letter Approvals'
        unique_together = ['letter', 'approver']

    def __str__(self):
        return f"{self.letter.reference_number} - {self.approver.username}"


class LetterHistory(models.Model):
    """Model for tracking letter history and changes"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('finalized', 'Finalized'),
        ('signed', 'Signed'),
        ('issued', 'Issued'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    letter = models.ForeignKey(GeneratedLetter, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Letter History'
        verbose_name_plural = 'Letter History'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.letter.reference_number} - {self.action} - {self.timestamp}"


class DocumentCategory(models.Model):
    """Model for categorizing HR documents"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Document Category'
        verbose_name_plural = 'Document Categories'

    def __str__(self):
        return self.name


class HRDocument(models.Model):
    """Model for general HR documents"""
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='hr_documents/')
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.IntegerField(blank=True, null=True)  # in bytes
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    version = models.CharField(max_length=20, default='1.0')
    
    # Tracking
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'HR Document'
        verbose_name_plural = 'HR Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title
