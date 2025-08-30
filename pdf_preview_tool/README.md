# PDF Preview Tool

A comprehensive PDF preview and document management module for ERP systems, built with Django and modern web technologies.

## 🚀 Features

### Core Functionality
- **Dynamic PDF Rendering**: Render PDFs generated from ERP data with full browser support
- **Advanced Preview Interface**: Zoom, page navigation, search, and responsive design
- **Multi-Format Support**: PDF, HTML, and HTM document formats
- **Real-time Search**: Full-text search across document content with highlighting

### Document Management
- **Document Types**: Categorized document management (Invoice, Delivery Note, Purchase Order, etc.)
- **Access Control**: Role-based permissions and user-specific access
- **ERP Integration**: Seamless integration with ERP systems via reference fields
- **Metadata Management**: Tags, descriptions, and custom metadata fields

### User Experience
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5
- **Customizable Settings**: User preferences for zoom, layout, and theme
- **Keyboard Shortcuts**: Power user features for efficient navigation
- **Multi-language Support**: Internationalization ready

### Security & Compliance
- **Audit Trail**: Complete logging of all document access and actions
- **Session Tracking**: Monitor user preview sessions and interactions
- **Access Logging**: IP address, user agent, and timestamp tracking
- **Permission System**: Granular access control for sensitive documents

## 🏗️ Architecture

### Models
- `Document`: Core document entity with ERP integration
- `DocumentType`: Categorized document types
- `PreviewSession`: User session tracking
- `PreviewAction`: Detailed action logging
- `DocumentAccessLog`: Access audit trail
- `PreviewSettings`: User preferences

### Views
- **Dashboard**: Overview with statistics and recent activity
- **Document Management**: CRUD operations for documents
- **Preview Interface**: Full-featured PDF viewer
- **Type Management**: Document type administration
- **API Endpoints**: RESTful API for React integration

### Frontend
- **Bootstrap 5**: Modern, responsive UI framework
- **Custom CSS**: Professional styling with CSS variables
- **JavaScript**: Interactive features and PDF handling
- **FontAwesome**: Rich icon library

## 📁 File Structure

```
pdf_preview_tool/
├── models.py              # Database models
├── views.py               # View logic and API endpoints
├── forms.py               # Form definitions
├── urls.py                # URL routing
├── admin.py               # Django admin configuration
├── signals.py             # Automated actions and logging
├── apps.py                # App configuration
├── templates/             # HTML templates
│   └── pdf_preview_tool/
│       ├── dashboard.html
│       ├── document_list.html
│       ├── document_upload.html
│       └── document_type_form.html
├── static/                # Static files
│   ├── css/
│   │   └── pdf_preview_tool.css
│   └── js/
│       └── pdf_preview_tool.js
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Installation
The PDF Preview Tool is already integrated into your Django project. Ensure it's in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'pdf_preview_tool',
]
```

### 2. Database Setup
Run migrations to create the necessary database tables:

```bash
python manage.py makemigrations pdf_preview_tool
python manage.py migrate pdf_preview_tool
```

### 3. Access the Tool
Navigate to the PDF Preview Tool dashboard:

```
http://127.0.0.1:8000/utilities/pdf-preview-tool/
```

## 📖 Usage Guide

### Creating Document Types
1. Navigate to **Document Types** → **New Document Type**
2. Choose a category (Invoice, Delivery Note, etc.)
3. Set approval requirements and access permissions
4. Save and activate the document type

### Uploading Documents
1. Go to **Documents** → **Upload Document**
2. Fill in document information and metadata
3. Select the appropriate document type
4. Upload your PDF or HTML file
5. Set access permissions and tags

### Previewing Documents
1. Click the **Preview** button on any document
2. Use zoom controls and page navigation
3. Search within document content
4. Download, print, or email as needed

### Managing Access
- **Public Documents**: Accessible to all users
- **Private Documents**: Require explicit user permissions
- **Role-based Access**: Control via user roles and groups
- **Approval Workflow**: Optional approval process for sensitive documents

## 🔧 Configuration

### User Settings
Users can customize their preview experience:
- Default zoom level
- Page layout preferences
- Theme selection (Light/Dark/Auto)
- Sidebar position
- Notification preferences

### Document Type Categories
Pre-configured categories include:
- **Invoice**: Customer billing documents
- **Delivery Note**: Shipping confirmations
- **Purchase Order**: Supplier orders
- **Sales Order**: Customer orders
- **Receipt**: Payment confirmations
- **Report**: Analytics and summaries
- **Contract**: Legal agreements
- **Other**: Custom document types

### File Size Limits
- **Maximum file size**: 50MB
- **Supported formats**: PDF, HTML, HTM
- **Recommended format**: PDF for best compatibility

## 🔌 API Integration

### REST Endpoints
The tool provides RESTful API endpoints for integration:

```python
# Start preview session
POST /api/documents/{id}/start-session/

# Log user actions
POST /api/sessions/{session_id}/log-action/

# End preview session
POST /api/sessions/{session_id}/end/

# Get document info
GET /api/documents/{id}/info/

# User settings
GET /api/user/settings/
POST /api/user/settings/update/
```

### React Integration
The JavaScript module is designed for React integration:
- Session management
- Real-time updates
- User preference handling
- Action logging

## 🎨 Customization

### Styling
Customize the appearance using CSS variables:

```css
:root {
    --primary-color: #4e73df;
    --secondary-color: #858796;
    --success-color: #1cc88a;
    --info-color: #36b9cc;
    --warning-color: #f6c23e;
    --danger-color: #e74a3b;
}
```

### Themes
Support for multiple themes:
- **Light**: Default professional appearance
- **Dark**: Modern dark mode
- **Auto**: System preference detection

### Layout Options
- **Single Page**: Traditional page-by-page view
- **Continuous**: Scrolling document view
- **Facing Pages**: Book-style layout

## 🔒 Security Features

### Access Control
- User authentication required
- Document-level permissions
- Role-based access control
- IP address logging

### Audit Trail
- Complete action logging
- User session tracking
- Document access history
- Change tracking

### Data Protection
- Secure file handling
- Input validation
- CSRF protection
- XSS prevention

## 📊 Performance Optimization

### Rendering
- Lazy loading for large documents
- Thumbnail generation
- Progressive page loading
- Memory management

### Caching
- Document metadata caching
- User preference caching
- Session data optimization
- Static asset optimization

## 🧪 Testing

### System Checks
Run Django system checks:

```bash
python manage.py check pdf_preview_tool
```

### Database Validation
Verify database integrity:

```bash
python manage.py validate
```

## 🚀 Deployment

### Production Considerations
- Configure static file serving
- Set up media file storage
- Configure database optimization
- Enable caching layers

### Scaling
- Multiple server support
- Load balancing ready
- Database connection pooling
- CDN integration support

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies
3. Run migrations
4. Start development server

### Code Standards
- Follow Django best practices
- Use consistent naming conventions
- Include comprehensive documentation
- Write unit tests for new features

## 📝 License

This module is part of the LogisEdge ERP system and follows the same licensing terms.

## 🆘 Support

### Common Issues
- **PDF not rendering**: Check file format and size
- **Permission denied**: Verify user access rights
- **Search not working**: Ensure document has text content

### Getting Help
- Check the Django admin interface
- Review system logs
- Consult the audit trail
- Contact system administrator

## 🔮 Future Enhancements

### Planned Features
- **Collaborative Annotations**: User comments and markups
- **Version Control**: Document versioning and history
- **Advanced Search**: AI-powered content analysis
- **Mobile App**: Native mobile application
- **Cloud Storage**: Integration with cloud providers
- **Workflow Automation**: Advanced approval processes

### Integration Opportunities
- **Email Systems**: Direct document sharing
- **Print Services**: Network printer integration
- **Document Management**: External DMS integration
- **Analytics**: Usage statistics and insights

---

**PDF Preview Tool** - Empowering ERP systems with professional document management and preview capabilities.
