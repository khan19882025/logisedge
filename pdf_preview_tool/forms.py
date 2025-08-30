from django import forms
from django.contrib.auth.models import User
from .models import (
    Document, DocumentType, PreviewSession, PreviewAction,
    DocumentAccessLog, PreviewSettings, SignatureStamp
)


class DocumentTypeForm(forms.ModelForm):
    """Form for creating/editing document types"""
    
    class Meta:
        model = DocumentType
        fields = ['name', 'category', 'description', 'is_active', 'requires_approval']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DocumentForm(forms.ModelForm):
    """Form for creating/editing documents"""
    
    class Meta:
        model = Document
        fields = [
            'title', 'document_type', 'file_path', 'file_size', 'page_count',
            'status', 'erp_reference', 'erp_module', 'description', 'tags',
            'metadata', 'is_public', 'allowed_roles', 'allowed_users'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file_path': forms.TextInput(attrs={'class': 'form-control'}),
            'file_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'page_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'erp_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'erp_module': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'metadata': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allowed_roles': forms.TextInput(attrs={'class': 'form-control'}),
            'allowed_users': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class PreviewSettingsForm(forms.ModelForm):
    """Form for user preview settings"""
    
    class Meta:
        model = PreviewSettings
        fields = [
            'default_zoom', 'show_thumbnails', 'auto_fit_page',
            'enable_annotations', 'theme'
        ]
        widgets = {
            'default_zoom': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'show_thumbnails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_fit_page': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_annotations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'theme': forms.Select(attrs={'class': 'form-control'})
        }


class DocumentSearchForm(forms.Form):
    """Form for searching documents"""
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search documents...'
        })
    )
    
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.filter(is_active=True),
        required=False,
        empty_label="All Types",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Document.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class DocumentUploadForm(forms.Form):
    """Form for uploading new documents"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    is_public = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PrintDocumentForm(forms.Form):
    """Form for printing documents"""
    page_range = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 1-3, 5, 7-9'
        })
    )
    
    copies = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    orientation = forms.ChoiceField(
        choices=[
            ('portrait', 'Portrait'),
            ('landscape', 'Landscape')
        ],
        initial='portrait',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class SignatureStampForm(forms.ModelForm):
    """Form for uploading signature/stamp images"""
    
    class Meta:
        model = SignatureStamp
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400',
                'accept': 'image/png,image/jpg,image/jpeg',
                'id': 'signature-file-input'
            })
        }
    
    def clean_file(self):
        """Custom validation for the uploaded file"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (2MB limit)
            if file.size > 2 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 2MB.")
            
            # Check file extension
            allowed_extensions = ['png', 'jpg', 'jpeg']
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    f"Only {', '.join(allowed_extensions)} files are allowed."
                )
        
        return file
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].help_text = "Upload PNG, JPG, or JPEG image (max 2MB)"
