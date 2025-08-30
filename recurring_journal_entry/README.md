# Recurring Journal Entry Module

A comprehensive Django module for automating periodic journal entries in an ERP accounting system.

## Features

### Core Functionality
- **Template Management**: Create and manage recurring journal entry templates
- **Flexible Scheduling**: Support for daily, weekly, monthly, quarterly, and annual frequencies
- **Smart Posting**: Configurable posting days (1st, 15th, last day, or custom day)
- **Auto-Posting**: Optional automatic posting of generated entries
- **Balance Validation**: Real-time validation ensuring debit equals credit
- **Entry History**: Track all generated journal entries from templates

### User Interface
- **Modern Dashboard**: Overview with statistics and upcoming entries
- **Interactive Forms**: Dynamic form with real-time balance calculation
- **Account Search**: AJAX-powered account search with Select2 integration
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5
- **Professional Styling**: Clean, modern UI with intuitive navigation

### Advanced Features
- **Status Management**: Active, Paused, Completed, and Cancelled states
- **Manual Generation**: Generate entries on-demand for specific dates
- **Template Actions**: Pause, resume, and cancel recurring templates
- **Audit Trail**: Complete tracking of who created and modified templates
- **Multi-Currency Support**: Full integration with currency system

## Models

### RecurringEntry
Main template model containing:
- Basic information (name, type, narration)
- Scheduling details (frequency, posting day, date range)
- Financial information (totals, currency)
- Status and settings (auto-post, active/paused)

### RecurringEntryLine
Individual line items in a recurring entry:
- Account reference
- Description
- Debit/credit amounts
- Order tracking

### GeneratedEntry
Tracks generated journal entries:
- Links to original template
- Posting date
- Generated journal entry reference
- Audit information

## Usage

### Creating a Recurring Template

1. Navigate to `/accounting/recurring-journal-entry/`
2. Click "Create New Template"
3. Fill in basic information:
   - Template name (e.g., "Monthly Rent", "Depreciation")
   - Journal type (General, Adjustment, Opening)
   - Start date
   - End date or number of occurrences
4. Configure scheduling:
   - Frequency (Daily, Weekly, Monthly, Quarterly, Annually)
   - Posting day (1st, 15th, last day, or custom)
5. Add journal line items:
   - Select accounts from chart of accounts
   - Enter debit/credit amounts
   - Ensure total debit equals total credit
6. Set options:
   - Auto-post (optional)
   - Currency
   - Fiscal year
7. Save the template

### Managing Templates

- **View Details**: See template information and recent generated entries
- **Edit**: Modify template settings and line items
- **Generate Entry**: Manually create entries for specific dates
- **Pause/Resume**: Temporarily stop or restart automatic generation
- **Cancel**: Permanently stop the recurring entry
- **View History**: See all generated journal entries

### Automatic Generation

Use the management command to automatically generate due entries:

```bash
# Generate all due entries
python manage.py generate_recurring_entries

# Dry run to see what would be generated
python manage.py generate_recurring_entries --dry-run

# Generate for specific template
python manage.py generate_recurring_entries --template-id 1

# Generate with specific user
python manage.py generate_recurring_entries --user-id 1
```

## URL Structure

- `/accounting/recurring-journal-entry/` - List all templates
- `/accounting/recurring-journal-entry/dashboard/` - Dashboard view
- `/accounting/recurring-journal-entry/create/` - Create new template
- `/accounting/recurring-journal-entry/<id>/` - Template details
- `/accounting/recurring-journal-entry/<id>/edit/` - Edit template
- `/accounting/recurring-journal-entry/<id>/generate/` - Generate entry
- `/accounting/recurring-journal-entry/<id>/generated-entries/` - View history

## Dependencies

- Django 4.2+
- Select2 (for account search)
- Bootstrap 5 (for UI components)
- Chart.js (for dashboard charts)
- dateutil (for date calculations)

## Configuration

The module integrates with existing ERP components:
- Chart of Accounts (for account selection)
- Manual Journal Entry (for generated entries)
- Multi-Currency (for currency support)
- Fiscal Year (for period management)
- Company (for multi-company support)

## Security

- All views require login authentication
- User tracking for all operations
- Audit trail for template modifications
- Validation to prevent unbalanced entries

## Performance

- Optimized database queries with select_related
- Pagination for large datasets
- AJAX account search for better UX
- Efficient date calculations for scheduling

## Future Enhancements

- Email notifications for due entries
- Bulk operations for multiple templates
- Advanced scheduling (business days, holidays)
- Integration with approval workflows
- Export/import functionality
- Advanced reporting and analytics 