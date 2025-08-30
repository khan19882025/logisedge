# LogisEdge Backup Scheduler

## Overview
The LogisEdge Backup Scheduler is a comprehensive backup management system that provides automated database backups, scheduling, monitoring, and disaster recovery capabilities.

## Features
- **Automated Backups**: Schedule daily, weekly, monthly, or yearly backups
- **Multiple Backup Types**: Full, incremental, and differential backups
- **Flexible Scopes**: Backup entire database or specific data categories
- **Storage Management**: Support for local, network, and cloud storage
- **Retention Policies**: Automatic cleanup of old backups
- **Monitoring & Alerts**: Real-time backup status and notifications
- **Web Dashboard**: User-friendly interface for management
- **Comprehensive Logging**: Detailed audit trail of all operations

## Quick Start

### 1. Initial Setup
The backup scheduler has been automatically configured with:
- Basic backup types (full, incremental, differential)
- Common backup scopes (database, customers, items, transactions, etc.)
- Default storage locations (local and network)
- Retention policies
- Alert configurations
- A daily backup schedule (2:00 AM)

### 2. Access the Dashboard
Navigate to: `/utilities/backup-scheduler/`

### 3. Manual Backup
Run a manual backup immediately:
```bash
python manage.py run_scheduled_backups --force
```

## Configuration

### Backup Types
- **Full Backup**: Complete backup of all data
- **Incremental Backup**: Only changed data since last backup
- **Differential Backup**: All data changed since last full backup

### Backup Scopes
- **Full Database**: Complete database backup
- **Customers**: Customer-related data
- **Items**: Inventory and item data
- **Transactions**: Financial and business transactions
- **Financial Data**: Accounting records
- **Documents**: File and document backup
- **Custom**: User-defined selection

### Storage Locations
- **Local Storage**: `C:/backups/logisEdge`
- **Network Storage**: `//192.168.1.100/backups/logisEdge`
- **Cloud Storage**: AWS S3, Azure Blob, Google Cloud Storage
- **FTP Server**: Remote FTP storage

## Scheduling

### Frequency Options
- **Daily**: Run at specified time every day
- **Weekly**: Run on specific weekday at specified time
- **Monthly**: Run on specific day of month at specified time
- **Yearly**: Run on specific date and time annually
- **Custom**: Cron expression for advanced scheduling

### Default Schedule
- **Name**: Daily Database Backup
- **Frequency**: Daily at 2:00 AM
- **Type**: Full backup
- **Scope**: Full database
- **Storage**: Local backup storage
- **Retention**: 7 days

## Automation

### Windows Task Scheduler
1. Open Task Scheduler (taskschd.msc)
2. Create Basic Task
3. Set trigger (e.g., Daily at 2:00 AM)
4. Set action: Start a program
5. Program: `powershell.exe`
6. Arguments: `-ExecutionPolicy Bypass -File "C:\Users\Admin\OneDrive\Desktop\logisEdge\run_backup_scheduler.ps1"`

### Command Line
```bash
# Run scheduled backups
python manage.py run_scheduled_backups

# Force run all schedules
python manage.py run_scheduled_backups --force

# Setup initial configuration
python manage.py setup_backup_scheduler
```

### Scripts
- **`run_backup_scheduler.bat`**: Windows batch file
- **`run_backup_scheduler.ps1`**: PowerShell script with logging

## Monitoring

### Dashboard Metrics
- Active schedules count
- Successful/failed backups
- Storage usage percentage
- Recent backup executions
- Upcoming schedules
- Recent activity logs

### Logs
- Backup execution logs
- Error details
- User actions
- System events

### Alerts
- Success notifications
- Failure alerts
- Storage full warnings
- Retention cleanup notifications

## Storage Management

### Local Storage
- Path: `C:/backups/logisEdge`
- Max Capacity: 100 GB
- Automatic directory creation

### Network Storage
- Path: `//192.168.1.100/backups/logisEdge`
- Max Capacity: 500 GB
- Network authentication support

### Backup Organization
```
C:/backups/logisEdge/
├── 2025-08-10/
│   ├── backup_full_database_20250810_171944.sql
│   └── backup_full_database_20250810_172049.sql
├── 2025-08-11/
└── ...
```

## Retention Policies

### Default Policies
- **Daily Backups**: Keep for 7 days
- **Weekly Backups**: Keep for 4 weeks
- **Monthly Backups**: Keep for 12 months

### Automatic Cleanup
- Removes expired backups
- Maintains storage space
- Logs cleanup operations

## Disaster Recovery

### Recovery Plans
- Documented recovery procedures
- Test schedules
- Backup verification
- Restore procedures

### Backup Verification
- File integrity checks
- Size validation
- Checksum verification
- Restore testing

## Security

### Access Control
- User permission-based access
- Audit logging
- Secure credential storage
- Role-based permissions

### Data Protection
- Encrypted storage support
- Secure network transmission
- Access logging
- Backup encryption

## Troubleshooting

### Common Issues

#### Backup Fails
1. Check storage location permissions
2. Verify disk space
3. Check database connectivity
4. Review error logs

#### Schedule Not Running
1. Verify schedule is active
2. Check timezone settings
3. Verify user permissions
4. Check system time

#### Storage Full
1. Review retention policies
2. Clean up old backups
3. Increase storage capacity
4. Check backup frequency

### Log Locations
- Application logs: Dashboard
- System logs: `C:\backups\logisEdge\backup_scheduler.log`
- Database logs: Backup execution records

## Maintenance

### Regular Tasks
- Monitor backup success rates
- Review storage usage
- Update retention policies
- Test recovery procedures
- Review alert configurations

### Performance Optimization
- Adjust backup frequency
- Optimize storage locations
- Monitor backup duration
- Review parallel execution settings

## Support

### Documentation
- This README file
- Django admin interface
- Web dashboard help
- API documentation

### Logs and Monitoring
- Real-time dashboard
- Detailed execution logs
- Error reporting
- Performance metrics

## Future Enhancements

### Planned Features
- Cloud storage integration
- Backup compression
- Incremental backup optimization
- Real-time monitoring
- Mobile notifications
- Advanced scheduling options
- Backup encryption
- Cross-platform support

---

**Note**: This backup scheduler is designed for the LogisEdge ERP system. Ensure proper testing in your environment before deploying to production.
