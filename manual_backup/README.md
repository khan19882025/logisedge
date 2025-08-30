# Manual Backup System

A comprehensive Django application for managing manual backups of the LogisEdge system.

## Features

### Core Functionality
- **Backup Creation**: Create full system, database-only, files-only, or configuration-only backups
- **Backup Management**: Track backup sessions, progress, and status
- **Restore Operations**: Restore from backup files with component selection
- **Audit Logging**: Comprehensive logging of all backup operations
- **Storage Management**: Configure multiple storage locations (local, network, cloud)
- **Retention Policies**: Automated cleanup based on configurable retention rules

### Backup Types
- **Full System Backup**: Complete backup including database, files, and configuration
- **Database Backup**: SQLite database backup only
- **Files Backup**: Media and static files backup
- **Configuration Backup**: Settings, requirements, and manage.py files

### Security Features
- **Encryption**: AES-128 and AES-256 encryption support
- **Checksum Verification**: SHA-256 integrity checking
- **Access Control**: Login-required views and user tracking
- **Audit Trail**: Complete history of all backup operations

## Installation

1. The app is already included in `INSTALLED_APPS` in `settings.py`
2. Run migrations: `python manage.py migrate manual_backup`
3. Access via `/utilities/manual-backup/` URL

## Usage

### Web Interface

#### Dashboard
- View backup statistics and recent backups
- Monitor storage usage and backup status
- Quick access to backup operations

#### Backup Operations
1. **Initiate Backup**: Create new backup sessions
2. **Backup History**: View and search through backup history
3. **Backup Details**: Detailed view of individual backup sessions
4. **Configuration Management**: Create and manage backup configurations

#### Storage Management
- Configure storage locations (local, network, cloud)
- Set primary and secondary storage paths
- Monitor storage capacity and usage

#### Audit Log
- View comprehensive logs of all backup operations
- Filter by log level, date, and user
- Track changes and system events

### Command Line Interface

#### Create Backup
```bash
# Full system backup
python manage.py create_backup --type full --reason "scheduled" --priority normal

# Database only backup
python manage.py create_backup --type database --reason "before_update" --priority high

# Dry run to see what would be backed up
python manage.py create_backup --dry-run --type full

# Custom notification emails
python manage.py create_backup --type full --notify "admin@example.com,ops@example.com"
```

#### Restore Backup
```bash
# Restore all components
python manage.py restore_backup backup_file.zip

# Restore specific components only
python manage.py restore_backup --components database config backup_file.zip

# Dry run to see what would be restored
python manage.py restore_backup --dry-run backup_file.zip

# Force restore even with warnings
python manage.py restore_backup --force backup_file.zip
```

## Models

### BackupConfiguration
- Backup type and settings
- Compression and encryption options
- Retention policies
- Include/exclude patterns

### BackupSession
- Individual backup sessions
- Progress tracking and status
- File information and checksums
- User and timing details

### BackupStep
- Step-by-step backup process
- Progress tracking for each step
- Error handling and logging

### BackupAuditLog
- Comprehensive audit trail
- Log levels (info, warning, error, critical)
- User context and IP tracking

### BackupStorageLocation
- Storage configuration
- Capacity and usage monitoring
- Connection details for remote storage

### BackupRetentionPolicy
- Automated cleanup rules
- Time-based retention policies
- Cleanup scheduling

## API Endpoints

### Backup Operations
- `POST /utilities/manual-backup/api/start-backup/` - Start new backup
- `GET /utilities/manual-backup/api/backup-progress/<backup_id>/` - Get backup progress
- `POST /utilities/manual-backup/api/update-step-progress/<backup_id>/<step_id>/` - Update step progress
- `POST /utilities/manual-backup/api/complete-backup/<backup_id>/` - Complete backup

### Configuration Management
- `POST /utilities/manual-backup/api/test-configuration/<config_id>/` - Test configuration
- `POST /utilities/manual-backup/api/activate-configuration/<config_id>/` - Activate configuration
- `POST /utilities/manual-backup/api/deactivate-configuration/<config_id>/` - Deactivate configuration

### Restore Operations
- `GET /utilities/manual-backup/api/restore-details/<backup_id>/` - Get restore details
- `POST /utilities/manual-backup/api/start-restore/<backup_id>/` - Start restore operation

## Configuration

### Settings
The app uses Django's standard settings. Key configuration options:

- `MEDIA_ROOT`: Media files directory for backup
- `STATIC_ROOT`: Static files directory for backup
- `DATABASES`: Database configuration for backup
- `EMAIL_*`: Email settings for notifications

### Storage Locations
Default storage location is created at `{BASE_DIR}/backups/` when first backup is created.

## Security Considerations

1. **Access Control**: All views require authentication
2. **File Permissions**: Backup files should have restricted access
3. **Encryption**: Sensitive data is encrypted using AES
4. **Audit Logging**: All operations are logged for security review
5. **Input Validation**: All user inputs are validated and sanitized

## Monitoring and Maintenance

### Regular Tasks
- Monitor backup success rates
- Check storage capacity and usage
- Review audit logs for anomalies
- Test restore procedures periodically

### Performance Optimization
- Use appropriate compression levels
- Schedule backups during low-usage periods
- Monitor backup duration and optimize if needed
- Clean up old backups based on retention policies

## Troubleshooting

### Common Issues

1. **Backup Fails**: Check file permissions and disk space
2. **Restore Fails**: Verify backup file integrity and permissions
3. **Slow Backups**: Adjust compression levels and exclude unnecessary files
4. **Storage Full**: Review retention policies and clean up old backups

### Logs
- Check Django logs for application errors
- Review audit logs for operation details
- Monitor system logs for file system issues

## Development

### Adding New Features
1. Extend models as needed
2. Add corresponding views and forms
3. Update templates and static files
4. Add tests for new functionality

### Testing
```bash
# Run tests
python manage.py test manual_backup

# Test backup creation
python manage.py create_backup --dry-run --type full

# Test restore
python manage.py restore_backup --dry-run test_backup.zip
```

## Support

For issues or questions:
1. Check the audit logs for error details
2. Review the Django application logs
3. Verify file permissions and disk space
4. Test with dry-run commands first

## License

This application is part of the LogisEdge system and follows the same licensing terms.
