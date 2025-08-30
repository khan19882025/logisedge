from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backup_scheduler.models import (
    BackupType, BackupScope, StorageLocation, BackupSchedule,
    BackupRetentionPolicy, BackupAlert
)
from django.utils import timezone
from datetime import time, timedelta


class Command(BaseCommand):
    help = 'Set up initial backup scheduler configuration'

    def handle(self, *args, **options):
        self.stdout.write('Setting up backup scheduler...')
        
        # Create backup types
        backup_types = [
            {
                'name': 'full',
                'description': 'Complete backup of all data including database, files, and configurations'
            },
            {
                'name': 'incremental',
                'description': 'Backup of only changed data since the last backup'
            },
            {
                'name': 'differential',
                'description': 'Backup of all data changed since the last full backup'
            }
        ]
        
        for bt_data in backup_types:
            backup_type, created = BackupType.objects.get_or_create(
                name=bt_data['name'],
                defaults={'description': bt_data['description']}
            )
            if created:
                self.stdout.write(f'Created backup type: {backup_type.name}')
            else:
                self.stdout.write(f'Backup type already exists: {backup_type.name}')
        
        # Create backup scopes
        backup_scopes = [
            {
                'name': 'full_database',
                'description': 'Complete database backup including all tables and data'
            },
            {
                'name': 'customers',
                'description': 'Customer-related data backup'
            },
            {
                'name': 'items',
                'description': 'Inventory and item data backup'
            },
            {
                'name': 'transactions',
                'description': 'Financial and business transaction data backup'
            },
            {
                'name': 'financial_data',
                'description': 'Accounting and financial records backup'
            },
            {
                'name': 'documents',
                'description': 'Document and file backup'
            },
            {
                'name': 'custom',
                'description': 'Custom selection of data for backup'
            }
        ]
        
        for bs_data in backup_scopes:
            backup_scope, created = BackupScope.objects.get_or_create(
                name=bs_data['name'],
                defaults={'description': bs_data['description']}
            )
            if created:
                self.stdout.write(f'Created backup scope: {backup_scope.name}')
            else:
                self.stdout.write(f'Backup scope already exists: {backup_scope.name}')
        
        # Create storage locations
        storage_locations = [
            {
                'name': 'Local Backup Storage',
                'storage_type': 'local',
                'path': 'C:/backups/logisEdge',
                'max_capacity_gb': 100,
                'used_capacity_gb': 0
            },
            {
                'name': 'Network Backup Storage',
                'storage_type': 'network',
                'path': '//192.168.1.100/backups/logisEdge',
                'max_capacity_gb': 500,
                'used_capacity_gb': 0
            }
        ]
        
        for sl_data in storage_locations:
            storage_location, created = StorageLocation.objects.get_or_create(
                name=sl_data['name'],
                defaults={
                    'storage_type': sl_data['storage_type'],
                    'path': sl_data['path'],
                    'max_capacity_gb': sl_data['max_capacity_gb'],
                    'used_capacity_gb': sl_data['used_capacity_gb']
                }
            )
            if created:
                self.stdout.write(f'Created storage location: {storage_location.name}')
            else:
                self.stdout.write(f'Storage location already exists: {storage_location.name}')
        
        # Create retention policies
        retention_policies = [
            {
                'name': 'Daily Backups - 7 days',
                'backup_type': BackupType.objects.get(name='full'),
                'retention_days': 7,
                'retention_count': 7
            },
            {
                'name': 'Weekly Backups - 4 weeks',
                'backup_type': BackupType.objects.get(name='full'),
                'retention_days': 28,
                'retention_count': 4
            },
            {
                'name': 'Monthly Backups - 12 months',
                'backup_type': BackupType.objects.get(name='full'),
                'retention_days': 365,
                'retention_count': 12
            }
        ]
        
        for rp_data in retention_policies:
            retention_policy, created = BackupRetentionPolicy.objects.get_or_create(
                name=rp_data['name'],
                defaults={
                    'backup_type': rp_data['backup_type'],
                    'retention_days': rp_data['retention_days'],
                    'retention_count': rp_data['retention_count']
                }
            )
            if created:
                self.stdout.write(f'Created retention policy: {retention_policy.name}')
            else:
                self.stdout.write(f'Retention policy already exists: {retention_policy.name}')
        
        # Create backup alerts
        backup_alerts = [
            {
                'name': 'Backup Success Notification',
                'alert_type': 'success',
                'channel': 'email',
                'recipients': ['admin@logisEdge.com']
            },
            {
                'name': 'Backup Failure Alert',
                'alert_type': 'failure',
                'channel': 'email',
                'recipients': ['admin@logisEdge.com', 'tech@logisEdge.com']
            },
            {
                'name': 'Storage Full Warning',
                'alert_type': 'storage_full',
                'channel': 'dashboard',
                'recipients': []
            }
        ]
        
        for ba_data in backup_alerts:
            backup_alert, created = BackupAlert.objects.get_or_create(
                name=ba_data['name'],
                defaults={
                    'alert_type': ba_data['alert_type'],
                    'channel': ba_data['channel'],
                    'recipients': ba_data['recipients']
                }
            )
            if created:
                self.stdout.write(f'Created backup alert: {backup_alert.name}')
            else:
                self.stdout.write(f'Backup alert already exists: {backup_alert.name}')
        
        # Create a default daily backup schedule
        try:
            # Get the first admin user or create one
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.first()
            
            if admin_user:
                default_schedule, created = BackupSchedule.objects.get_or_create(
                    name='Daily Database Backup',
                    defaults={
                        'backup_type': BackupType.objects.get(name='full'),
                        'backup_scope': BackupScope.objects.get(name='full_database'),
                        'storage_location': StorageLocation.objects.get(name='Local Backup Storage'),
                        'frequency': 'daily',
                        'start_time': time(2, 0),  # 2:00 AM
                        'start_date': timezone.now().date(),
                        'retention_days': 7,
                        'max_backups': 7,
                        'created_by': admin_user
                    }
                )
                if created:
                    self.stdout.write(f'Created default backup schedule: {default_schedule.name}')
                else:
                    self.stdout.write(f'Default backup schedule already exists: {default_schedule.name}')
        except Exception as e:
            self.stdout.write(f'Could not create default schedule: {e}')
        
        self.stdout.write(
            self.style.SUCCESS('Backup scheduler setup completed successfully!')
        )
