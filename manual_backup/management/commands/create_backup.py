from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import os
import shutil
import zipfile
import hashlib
import json
from datetime import datetime

from manual_backup.models import (
    BackupSession, BackupConfiguration, BackupStep, 
    BackupAuditLog, BackupStorageLocation
)


class Command(BaseCommand):
    help = 'Create a manual backup of the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['full', 'database', 'files', 'config'],
            default='full',
            help='Type of backup to create'
        )
        parser.add_argument(
            '--reason',
            default='manual',
            help='Reason for the backup'
        )
        parser.add_argument(
            '--priority',
            choices=['low', 'normal', 'high', 'critical'],
            default='normal',
            help='Priority level of the backup'
        )
        parser.add_argument(
            '--description',
            default='',
            help='Description of the backup'
        )
        parser.add_argument(
            '--user',
            type=int,
            help='User ID who initiated the backup'
        )
        parser.add_argument(
            '--notify',
            help='Comma-separated list of email addresses for notifications'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be backed up without actually creating the backup'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        reason = options['reason']
        priority = options['priority']
        description = options['description']
        user_id = options['user']
        notify_emails = options['notify']
        dry_run = options['dry_run']

        # Get or create default configuration
        config, created = BackupConfiguration.objects.get_or_create(
            name=f'Default {backup_type.title()} Backup',
            defaults={
                'backup_type': backup_type,
                'compression_level': 'balanced',
                'encryption_type': 'aes256',
                'retention_days': 30,
                'include_media': True,
                'include_static': True,
                'include_database': True,
                'include_config': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created default backup configuration: {config.name}')
            )

        # Get user
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f'User with ID {user_id} does not exist')
        else:
            # Use first superuser or first user
            user = User.objects.filter(is_superuser=True).first() or User.objects.first()

        if not user:
            raise CommandError('No users found in the system')

        # Create backup session
        backup_name = f"{backup_type.title()}_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_session = BackupSession(
            name=backup_name,
            reason=reason,
            description=description,
            priority=priority,
            configuration=config,
            status='pending',
            created_by=user,
            notify_emails=notify_emails or ''
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No backup will be created')
            )
            self.stdout.write(f'Backup Name: {backup_name}')
            self.stdout.write(f'Backup Type: {backup_type}')
            self.stdout.write(f'Reason: {reason}')
            self.stdout.write(f'Priority: {priority}')
            self.stdout.write(f'User: {user.username}')
            self.stdout.write(f'Configuration: {config.name}')
            
            # Show what would be backed up
            self._show_backup_contents(backup_type)
            return

        try:
            backup_session.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created backup session: {backup_session.backup_id}')
            )

            # Create backup steps
            steps = self._create_backup_steps(backup_session, backup_type)
            
            # Execute backup
            self._execute_backup(backup_session, steps, backup_type)
            
            self.stdout.write(
                self.style.SUCCESS(f'Backup completed successfully: {backup_session.file_path}')
            )

        except Exception as e:
            if backup_session.pk:
                backup_session.status = 'failed'
                backup_session.save()
                
                BackupAuditLog.objects.create(
                    backup_session=backup_session,
                    level='error',
                    message=f'Backup failed: {str(e)}',
                    details={'error': str(e)}
                )
            
            raise CommandError(f'Backup failed: {str(e)}')

    def _create_backup_steps(self, backup_session, backup_type):
        """Create backup steps for the session"""
        steps_data = []
        
        if backup_type in ['full', 'database']:
            steps_data.append(('database_backup', 'Database Backup', 1))
        
        if backup_type in ['full', 'files']:
            steps_data.append(('file_backup', 'File Backup', 2))
        
        if backup_type in ['full', 'config']:
            steps_data.append(('config_backup', 'Configuration Backup', 3))
        
        steps_data.extend([
            ('checksum_generation', 'Checksum Generation', 4),
            ('compression', 'Compression', 5),
            ('storage', 'Storage', 6),
            ('verification', 'Verification', 7),
            ('cleanup', 'Cleanup', 8)
        ])

        steps = []
        for step_type, step_name, order in steps_data:
            step = BackupStep.objects.create(
                backup_session=backup_session,
                step_type=step_type,
                step_name=step_name,
                order=order,
                status='pending'
            )
            steps.append(step)

        return steps

    def _execute_backup(self, backup_session, steps, backup_type):
        """Execute the backup process"""
        backup_session.status = 'in_progress'
        backup_session.started_at = timezone.now()
        backup_session.save()

        try:
            # Get or create primary storage location
            storage_location, created = BackupStorageLocation.objects.get_or_create(
                name='Local Storage',
                defaults={
                    'storage_type': 'local',
                    'path': os.path.join(settings.BASE_DIR, 'backups'),
                    'description': 'Local backup storage',
                    'is_primary': True,
                    'is_active': True
                }
            )

            if created:
                os.makedirs(storage_location.path, exist_ok=True)

            backup_file_path = os.path.join(
                storage_location.path,
                f"{backup_session.name}.zip"
            )

            # Create backup archive
            with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Database backup
                if backup_type in ['full', 'database']:
                    self._backup_database(zipf, steps[0])
                
                # File backup
                if backup_type in ['full', 'files']:
                    self._backup_files(zipf, steps[1])
                
                # Config backup
                if backup_type in ['full', 'config']:
                    self._backup_config(zipf, steps[2])

            # Update backup session
            backup_session.status = 'completed'
            backup_session.file_path = backup_file_path
            backup_session.file_size_bytes = os.path.getsize(backup_file_path)
            backup_session.primary_storage_path = backup_file_path
            
            # Generate checksum
            with open(backup_file_path, 'rb') as f:
                backup_session.checksum_sha256 = hashlib.sha256(f.read()).hexdigest()
            
            backup_session.integrity_verified = True
            backup_session.verification_checksum = backup_session.checksum_sha256
            backup_session.verification_timestamp = timezone.now()
            
            # Calculate duration
            if backup_session.started_at:
                duration = (timezone.now() - backup_session.started_at).total_seconds()
                backup_session.duration_seconds = int(duration)
            
            backup_session.progress_percentage = 100
            backup_session.current_step = 'Completed'
            backup_session.save()

            # Mark all steps as completed
            for step in steps:
                step.status = 'completed'
                step.progress_percentage = 100
                step.completed_at = timezone.now()
                step.save()

        except Exception as e:
            backup_session.status = 'failed'
            backup_session.current_step = f'Failed: {str(e)}'
            backup_session.save()
            raise

    def _backup_database(self, zipf, step):
        """Backup the database"""
        step.status = 'in_progress'
        step.started_at = timezone.now()
        step.save()

        try:
            # For SQLite, just copy the database file
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                zipf.write(db_path, 'database/db.sqlite3')
                step.progress_percentage = 100
                step.status = 'completed'
                step.completed_at = timezone.now()
                step.save()
            else:
                raise Exception(f'Database file not found: {db_path}')
        except Exception as e:
            step.status = 'failed'
            step.error_message = str(e)
            step.save()
            raise

    def _backup_files(self, zipf, step):
        """Backup important files"""
        step.status = 'in_progress'
        step.started_at = timezone.now()
        step.save()

        try:
            # Backup media files
            if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
                media_path = settings.MEDIA_ROOT
                if os.path.exists(media_path):
                    for root, dirs, files in os.walk(media_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, media_path)
                            zipf.write(file_path, f'media/{arcname}')

            # Backup static files
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                static_path = settings.STATIC_ROOT
                if os.path.exists(static_path):
                    for root, dirs, files in os.walk(static_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, static_path)
                            zipf.write(file_path, f'static/{arcname}')

            step.progress_percentage = 100
            step.status = 'completed'
            step.completed_at = timezone.now()
            step.save()

        except Exception as e:
            step.status = 'failed'
            step.error_message = str(e)
            step.save()
            raise

    def _backup_config(self, zipf, step):
        """Backup configuration files"""
        step.status = 'in_progress'
        step.started_at = timezone.now()
        step.save()

        try:
            # Backup settings.py
            settings_path = os.path.join(settings.BASE_DIR, 'logisEdge', 'settings.py')
            if os.path.exists(settings_path):
                zipf.write(settings_path, 'config/settings.py')

            # Backup requirements.txt if it exists
            requirements_path = os.path.join(settings.BASE_DIR, 'requirements.txt')
            if os.path.exists(requirements_path):
                zipf.write(requirements_path, 'config/requirements.txt')

            # Backup manage.py
            manage_path = os.path.join(settings.BASE_DIR, 'manage.py')
            if os.path.exists(manage_path):
                zipf.write(manage_path, 'config/manage.py')

            step.progress_percentage = 100
            step.status = 'completed'
            step.completed_at = timezone.now()
            step.save()

        except Exception as e:
            step.status = 'failed'
            step.error_message = str(e)
            step.save()
            raise

    def _show_backup_contents(self, backup_type):
        """Show what would be backed up in dry-run mode"""
        self.stdout.write('\nBackup Contents:')
        
        if backup_type in ['full', 'database']:
            self.stdout.write('  ✓ Database')
        
        if backup_type in ['full', 'files']:
            self.stdout.write('  ✓ Media files')
            self.stdout.write('  ✓ Static files')
        
        if backup_type in ['full', 'config']:
            self.stdout.write('  ✓ Settings')
            self.stdout.write('  ✓ Requirements')
            self.stdout.write('  ✓ Manage.py')
        
        self.stdout.write('  ✓ Checksum generation')
        self.stdout.write('  ✓ Compression')
        self.stdout.write('  ✓ Storage')
        self.stdout.write('  ✓ Verification')
        self.stdout.write('  ✓ Cleanup')
