# Signature/Stamp Uploader Feature

A comprehensive solution for uploading, managing, and integrating user signatures and company stamps into PDF documents within your ERP system.

## 🚀 Features

- **Secure File Upload**: PNG, JPG, JPEG support with 2MB size limit
- **User Isolation**: Each user can only access their own signature/stamp
- **PDF Integration**: Automatic signature embedding in generated documents
- **Modern UI**: Responsive design with drag-and-drop support
- **Real-time Preview**: Live image preview before upload
- **Admin Management**: Administrative interface for oversight

## 📁 File Structure

```
pdf_preview_tool/
├── models.py              # SignatureStamp model
├── serializers.py         # DRF serializers
├── views.py               # API views and template views
├── urls.py                # URL routing
├── admin.py               # Admin interface
├── forms.py               # Django forms
├── pdf_utils.py           # PDF generation utilities
├── templates/
│   └── pdf_preview_tool/
│       └── signature_uploader.html
└── static/
    ├── css/
    │   └── signature_uploader.css
    └── js/
        └── signature_uploader.js
```

## 🛠️ Installation

### 1. Install Dependencies

```bash
pip install -r requirements_signature_uploader.txt
```

### 2. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ... existing apps
    'rest_framework',
    'pdf_preview_tool',
]
```

### 3. Configure Media Settings

```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Ensure media files are served in development
if DEBUG:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
```

### 4. Run Migrations

```bash
python manage.py makemigrations pdf_preview_tool
python manage.py migrate
```

### 5. Create Superuser (for admin access)

```bash
python manage.py createsuperuser
```

## 🔧 Configuration

### File Upload Settings

```python
# settings.py
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB
ALLOWED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg']

# Media storage configuration
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
```

### PDF Generation Settings

```python
# settings.py
PDF_SIGNATURE_DIMENSIONS = {
    'width': 150,  # pixels
    'height': 60,  # pixels
}

PDF_SIGNATURE_POSITION = 'bottom-right'
```

## 📱 Usage

### 1. Access the Uploader

Navigate to: `/pdf_preview_tool/signature-uploader/`

### 2. Upload Signature/Stamp

- Click the upload area or drag and drop an image
- Supported formats: PNG, JPG, JPEG
- Maximum size: 2MB
- Preview before upload

### 3. Manage Existing Signature

- View current signature details
- Delete existing signature
- Update with new image

## 🔌 API Endpoints

### Base URL: `/pdf_preview_tool/api/signature-stamp/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List user's signature (filtered to current user) |
| POST | `/` | Create new signature |
| GET | `/my-signature/` | Get current user's signature |
| POST | `/upload/` | Upload/update signature file |
| DELETE | `/delete/` | Delete current signature |
| PUT | `/{id}/` | Update signature (admin only) |
| DELETE | `/{id}/` | Delete signature (admin only) |

### API Authentication

All endpoints require authentication. Include in headers:
```
Authorization: Token <your_token>
X-CSRFToken: <csrf_token>
```

### Example API Usage

```javascript
// Upload signature
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/pdf_preview_tool/api/signature-stamp/upload/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken,
    },
    body: formData,
})
.then(response => response.json())
.then(data => console.log('Success:', data));
```

## 📄 PDF Integration

### Basic Usage

```python
from pdf_preview_tool.pdf_utils import (
    generate_invoice_with_signature,
    generate_delivery_note_with_signature,
    generate_purchase_order_with_signature
)

# Generate invoice with signature
invoice_data = {
    'company_name': 'Your Company',
    'invoice_number': 'INV-001',
    'customer_name': 'Customer Name',
    'items': [
        {'description': 'Product 1', 'quantity': 2, 'unit_price': 100, 'total': 200}
    ],
    'subtotal': 200,
    'tax': 20,
    'total': 220
}

pdf_output = generate_invoice_with_signature(request.user, invoice_data)
```

### Custom PDF Generation

```python
from pdf_preview_tool.pdf_utils import PDFGenerator

class CustomPDFGenerator(PDFGenerator):
    def generate_custom_pdf(self, data):
        # Your custom PDF generation logic
        story = []
        # ... add content to story
        
        # Add signature automatically
        story = self.add_signature_to_pdf(story, page_width, page_height)
        
        # Build PDF
        doc.build(story)
        return output_path
```

## 🎨 Customization

### CSS Styling

Modify `static/css/signature_uploader.css` to customize:
- Colors and themes
- Layout and spacing
- Responsive breakpoints
- Animation effects

### JavaScript Functionality

Extend `static/js/signature_uploader.js` to add:
- Additional validation rules
- Custom upload handlers
- Integration with other systems
- Enhanced user experience features

### PDF Templates

Customize PDF generation in `pdf_utils.py`:
- Document layouts
- Signature positioning
- Company branding
- Multi-language support

## 🔒 Security Features

- **File Type Validation**: Only image files allowed
- **Size Limits**: 2MB maximum file size
- **User Isolation**: Users can only access their own files
- **CSRF Protection**: Built-in Django CSRF protection
- **Authentication Required**: All endpoints require login
- **Admin Controls**: Superuser oversight capabilities

## 🧪 Testing

### Run Tests

```bash
python manage.py test pdf_preview_tool.tests.test_signature_uploader
```

### Test Coverage

```bash
coverage run --source='.' manage.py test pdf_preview_tool
coverage report
coverage html
```

## 🚀 Deployment

### Production Considerations

1. **File Storage**: Consider using cloud storage (AWS S3, Google Cloud Storage)
2. **CDN**: Serve static files through CDN for better performance
3. **Caching**: Implement Redis/Memcached for API responses
4. **Monitoring**: Add logging and monitoring for file operations
5. **Backup**: Regular backup of uploaded signatures

### Environment Variables

```bash
# .env
MEDIA_STORAGE_BACKEND=storages.backends.s3boto3.S3Boto3Storage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=your_region
```

## 🔧 Troubleshooting

### Common Issues

1. **File Upload Fails**
   - Check file size and format
   - Verify media directory permissions
   - Check Django settings configuration

2. **PDF Generation Errors**
   - Ensure reportlab is installed
   - Check image file paths
   - Verify user permissions

3. **API Authentication Issues**
   - Check CSRF token configuration
   - Verify user authentication
   - Check API endpoint URLs

### Debug Mode

```python
# settings.py
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'pdf_preview_tool': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📚 API Documentation

### SignatureStamp Model

```python
class SignatureStamp(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='signatures/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Serializer Fields

- `id`: Unique identifier
- `user`: Associated user (read-only)
- `file`: Image file
- `file_url`: Public URL to file
- `file_size_mb`: File size in MB
- `file_extension`: File extension
- `uploaded_at`: Upload timestamp
- `updated_at`: Last update timestamp

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting section

---

**Note**: This feature requires Django REST Framework and reportlab for full functionality. Ensure all dependencies are properly installed and configured.
