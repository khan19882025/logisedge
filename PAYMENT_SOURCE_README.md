# Payment Source Master Module

## Overview

The Payment Source module is a comprehensive master data management system for tracking and categorizing payment sources in the logisEdge ERP system. It provides a complete CRUD interface for managing payment sources and integrates seamlessly with invoices and ledger entries.

## Features

### Core Functionality
- **Payment Source Management**: Create, read, update, and delete payment sources
- **Soft Delete**: Payment sources are deactivated rather than permanently removed
- **Audit Trail**: Track creation and modification with user timestamps
- **Status Management**: Active/Inactive status control
- **Search & Filter**: Advanced search and filtering capabilities

### Integration Points
- **Invoice Integration**: Payment sources can be assigned to invoices
- **Ledger Integration**: Payment source information is automatically copied to ledger entries
- **API Support**: Full REST API for frontend integration

## Technical Architecture

### Models

#### PaymentSource
```python
class PaymentSource(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, ...)
    updated_by = models.ForeignKey(User, ...)
```

### API Endpoints

#### REST API
- `GET /api/payment-sources/` - List all payment sources
- `POST /api/payment-sources/` - Create new payment source
- `GET /api/payment-sources/{id}/` - Retrieve specific payment source
- `PUT /api/payment-sources/{id}/` - Update payment source
- `DELETE /api/payment-sources/{id}/` - Soft delete payment source

#### Additional Endpoints
- `GET /api/payment-sources/active/` - Get only active payment sources
- `GET /api/payment-sources/dropdown/` - Get payment sources for dropdown (active only)

### Frontend Views

#### List View (`/payment-source/`)
- Search functionality with real-time filtering
- Status-based filtering (All/Active/Inactive)
- Responsive table with actions (Edit/Delete/Restore)
- Bootstrap-based UI with modern design

#### Create/Edit View (`/payment-source/create/`, `/payment-source/{id}/edit/`)
- Form validation with client-side and server-side checks
- Auto-save functionality
- Help text and guidance for users

#### Detail View (`/payment-source/{id}/`)
- Comprehensive payment source information
- Quick action buttons
- Usage statistics (placeholder for future enhancement)

## Installation & Setup

### 1. Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ... existing apps
    'payment_source',
    'rest_framework',  # Required for API
]
```

### 2. Run Migrations
```bash
python manage.py makemigrations payment_source
python manage.py migrate
```

### 3. Add URLs
```python
# In main urls.py
path('payment-source/', include('payment_source.urls', namespace='payment_source')),
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

## Usage Examples

### Creating Payment Sources

#### Via Admin Interface
1. Navigate to `/admin/payment_source/paymentsource/`
2. Click "Add Payment Source"
3. Fill in name, description, and status
4. Save

#### Via API
```bash
curl -X POST /payment-source/api/payment-sources/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Cash", "description": "Cash payments", "is_active": true}'
```

#### Via Frontend
1. Navigate to `/payment-source/`
2. Click "Add Payment Source"
3. Fill in the form
4. Click "Save"

### Managing Payment Sources

#### Search & Filter
- Use the search box to find payment sources by name or description
- Use status filters to show only active, inactive, or all sources
- Real-time search with debounced input

#### Edit & Delete
- Click the edit button (pencil icon) to modify payment sources
- Click the delete button (trash icon) to deactivate
- Deactivated sources can be restored using the restore button

## Integration with Other Modules

### Invoice Integration

#### Adding Payment Source to Invoice
```python
# In invoice form
payment_source = models.ForeignKey('payment_source.PaymentSource', ...)

# In invoice form fields
fields = [..., 'payment_source', ...]
```

#### Invoice Posting to Ledger
When an invoice is posted to the ledger, the payment source is automatically copied:

```python
# In post_invoice_to_ledger function
ar_entry = Ledger.objects.create(
    # ... other fields
    payment_source=invoice.payment_source,  # Copy from invoice
    # ... other fields
)
```

### Ledger Integration

#### Payment Source in Ledger Entries
```python
# In Ledger model
payment_source = models.ForeignKey('payment_source.PaymentSource', ...)

# In Ledger form
fields = [..., 'payment_source', ...]
```

## API Documentation

### Serializers

#### PaymentSourceSerializer
Full payment source data including audit information.

#### PaymentSourceCreateSerializer
For creating new payment sources with validation.

#### PaymentSourceUpdateSerializer
For updating existing payment sources with validation.

#### PaymentSourceListSerializer
Minimal fields for listing (optimized for performance).

#### PaymentSourceDropdownSerializer
Minimal fields for dropdown/select components.

### ViewSet Features

#### Filtering
- `?is_active=true/false` - Filter by active status
- `?search=term` - Search by name or description

#### Custom Actions
- `active/` - Get only active payment sources
- `dropdown/` - Get payment sources for dropdown components

## Frontend Implementation

### JavaScript Architecture

#### PaymentSourceManager Class
```javascript
class PaymentSourceManager {
    constructor() {
        this.currentPaymentSource = null;
        this.isEditMode = false;
        this.init();
    }
    
    // Methods for CRUD operations
    async loadPaymentSources() { ... }
    async savePaymentSource() { ... }
    async deletePaymentSource(id) { ... }
    async restorePaymentSource(id) { ... }
}
```

### UI Components

#### Search & Filter
- Real-time search with debouncing
- Status-based filtering
- Responsive design

#### Modal Forms
- Bootstrap modals for create/edit
- Form validation
- Loading states

#### Data Table
- Responsive table with hover effects
- Action buttons for each row
- Loading and empty states

## Database Schema

### Tables

#### payment_source
- `id` - Primary key
- `name` - Unique payment source name (max 50 chars)
- `description` - Optional description
- `is_active` - Status flag
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `created_by` - User who created
- `updated_by` - User who last updated

### Relationships

#### Foreign Keys
- `created_by` → `auth_user`
- `updated_by` → `auth_user`

#### Referenced By
- `invoice.invoice.payment_source` → `payment_source`
- `ledger.ledger.payment_source` → `payment_source`

## Security & Permissions

### Authentication
- All views require user authentication (`@login_required`)
- API endpoints require authentication (`IsAuthenticated`)

### CSRF Protection
- All forms include CSRF tokens
- API endpoints validate CSRF tokens

### Audit Trail
- Track who created and modified each payment source
- Timestamps for all changes
- Soft delete prevents data loss

## Performance Considerations

### Database Optimization
- Indexes on frequently queried fields
- Efficient filtering and search queries
- Pagination support for large datasets

### API Performance
- Optimized serializers for different use cases
- Efficient database queries
- Response caching where appropriate

## Testing

### Test Script
Run the included test script to verify functionality:

```bash
python test_payment_source.py
```

### Test Coverage
- Model creation and validation
- API endpoint functionality
- Integration with invoice and ledger modules
- Frontend form handling

## Troubleshooting

### Common Issues

#### Migration Errors
- Ensure Django REST Framework is installed
- Check that all dependencies are satisfied
- Verify database connection

#### API Errors
- Check authentication and permissions
- Verify CSRF token inclusion
- Check request format and validation

#### Frontend Issues
- Ensure Bootstrap and required CSS/JS are loaded
- Check browser console for JavaScript errors
- Verify CSRF token is available

### Debug Mode
Enable Django debug mode for detailed error messages:

```python
DEBUG = True
```

## Future Enhancements

### Planned Features
- Payment source usage analytics
- Bulk import/export functionality
- Advanced reporting and dashboards
- Integration with payment gateways
- Multi-currency support

### API Extensions
- GraphQL support
- Webhook notifications
- Rate limiting and throttling
- Advanced filtering and sorting

## Support & Maintenance

### Code Quality
- Follows Django best practices
- Comprehensive error handling
- Logging for debugging
- Clean, maintainable code

### Documentation
- Inline code documentation
- API documentation
- User guides and tutorials
- Change logs and version history

## License

This module is part of the logisEdge ERP system and follows the same licensing terms.

---

For technical support or questions, please refer to the project documentation or contact the development team.
