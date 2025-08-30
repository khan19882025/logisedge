from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import os
import zipfile
import hashlib
import shutil
from datetime import datetime

from manual_backup.models import (
    BackupSession, BackupAuditLog, BackupStorageLocation
)


class Command(BaseCommand):
    help = 'Restore a backup from a backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_path',
            help='Path to the backup file to restore'
        )
        parser.add_argument(
            '--user',
            type=int,
            help='User ID who initiated the restore'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without actually restoring'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore even if there are warnings'
        )
        parser.add_argument(
            '--components',
            nargs='+',
            choices=['database', 'files', 'config'],
            default=['database', 'files', 'config'],
            help='Which components to restore'
        )

    def handle(self, *args, **options):
        backup_path = options['backup_path']
        user_id = options['user']
        dry_run = options['dry_run']
        force = options['force']
        components = options['components']

        # Validate backup file
        if not os.path.exists(backup_path):
            raise CommandError(f'Backup file not found: {backup_path}')

        if not backup_path.endswith('.zip'):
            raise CommandError('Backup file must be a ZIP archive')

        # Get user
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f'User with ID {user_id} does not exist')
        else:
            user = User.objects.filter(is_superuser=True).first() or User.objects.first()

        if not user:
            raise CommandError('No users found in the system')

        # Validate backup file integrity
        if not self._validate_backup_file(backup_path):
            if not force:
                raise CommandError('Backup file integrity check failed. Use --force to override.')
            else:
                self.stdout.write(
                    self.style.WARNING('Backup file integrity check failed, but proceeding due to --force flag')
                )

        # Analyze backup contents
        backup_contents = self._analyze_backup(backup_path)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No restore will be performed')
            )
            self.stdout.write(f'Backup File: {backup_path}')
            self.stdout.write(f'File Size: {os.path.getsize(backup_path)} bytes')
            self.stdout.write(f'Components to Restore: {", ".join(components)}')
            self.stdout.write(f'User: {user.username}')
            
            self.stdout.write('\nBackup Contents:')
            for component, files in backup_contents.items():
                if component in components:
                    self.stdout.write(f'  ✓ {component.title()}: {len(files)} files')
                else:
                    self.stdout.write(f'  - {component.title()}: {len(files)} files (skipped)')
            
            self.stdout.write('\nRestore Summary:')
            if 'database' in components:
                self.stdout.write('  ✓ Database will be restored')
            if 'files' in components:
                self.stdout.write('  ✓ Media and static files will be restored')
            if 'config' in components:
                self.stdout.write('  ✓ Configuration files will be restored')
            
            return

        # Create restore session
        restore_session = BackupSession.objects.create(
            name=f"Restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            reason='restore',
            description=f'Restore from {os.path.basename(backup_path)}',
            priority='high',
            status='in_progress',
            created_by=user,
            started_at=timezone.now()
        )

        try:
            self.stdout.write(
                self.style.SUCCESS(f'Created restore session: {restore_session.backup_id}')
            )

            # Perform restore
            self._perform_restore(restore_session, backup_path, backup_contents, components)

            # Mark restore as completed
            restore_session.status = 'completed'
            restore_session.progress_percentage = 100
            restore_session.current_step = 'Completed'
            restore_session.completed_at = timezone.now()
            
            if restore_session.started_at:
                duration = (restore_session.completed_at - restore_session.started_at).total_seconds()
                restore_session.duration_seconds = int(duration)
            
            restore_session.save()

            self.stdout.write(
                self.style.SUCCESS('Restore completed successfully!')
            )

        except Exception as e:
            restore_session.status = 'failed'
            restore_session.current_step = f'Failed: {str(e)}'
            restore_session.save()
            
            BackupAuditLog.objects.create(
                backup_session=restore_session,
                level='error',
                message=f'Restore failed: {str(e)}',
                details={'error': str(e)}
            )
            
            raise CommandError(f'Restore failed: {str(e)}')

    def _validate_backup_file(self, backup_path):
        """Validate the integrity of the backup file"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Test if the ZIP file is valid
                zipf.testzip()
                return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup file validation failed: {str(e)}')
            )
            return False

    def _analyze_backup(self, backup_path):
        """Analyze the contents of the backup file"""
        backup_contents = {
            'database': [],
            'files': [],
            'config': []
        }
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                for file_info in zipf.filelist:
                    filename = file_info.filename
                    
                    if filename.startswith('database/'):
                        backup_contents['database'].append(filename)
                    elif filename.startswith('media/') or filename.startswith('static/'):
                        backup_contents['files'].append(filename)
                    elif filename.startswith('config/'):
                        backup_contents['config'].append(filename)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to analyze backup contents: {str(e)}')
            )
        
        return backup_contents

    def _perform_restore(self, restore_session, backup_path, backup_contents, components):
        """Perform the actual restore operation"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Restore database
                if 'database' in components and backup_contents['database']:
                    self.stdout.write('Restoring database...')
                    self._restore_database(zipf, restore_session)
                
                # Restore files
                if 'files' in components and backup_contents['files']:
                    self.stdout.write('Restoring files...')
                    self._restore_files(zipf, restore_session)
                
                # Restore config
                if 'config' in components and backup_contents['config']:
                    self.stdout.write('Restoring configuration...')
                    self._restore_config(zipf, restore_session)
                
        except Exception as e:
            raise Exception(f'Restore operation failed: {str(e)}')

    def _restore_database(self, zipf, restore_session):
        """Restore the database"""
        try:
            # Find database file in backup
            db_files = [f for f in zipf.namelist() if f.startswith('database/')]
            
            if not db_files:
                self.stdout.write(self.style.WARNING('No database files found in backup'))
                return
            
            # Extract database file
            for db_file in db_files:
                if db_file.endswith('.sqlite3'):
                    # Create backup of current database
                    current_db = settings.DATABASES['default']['NAME']
                    if os.path.exists(current_db):
                        backup_name = f"{current_db}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copy2(current_db, backup_name)
                        self.stdout.write(f'Current database backed up to: {backup_name}')
                    
                    # Extract and restore database
                    zipf.extract(db_file, '/tmp')
                    temp_db = f'/tmp/{db_file}'
                    
                    if os.path.exists(temp_db):
                        shutil.copy2(temp_db, current_db)
                        os.remove(temp_db)
                        self.stdout.write(self.style.SUCCESS('Database restored successfully'))
                        
                        # Log the restore
                        BackupAuditLog.objects.create(
                            backup_session=restore_session,
                            level='info',
                            message='Database restored successfully',
                            details={'database_file': db_file}
                        )
                    else:
                        raise Exception(f'Failed to extract database file: {db_file}')
                    
                    break
            
        except Exception as e:
            raise Exception(f'Database restore failed: {str(e)}')

    def _restore_files(self, zipf, restore_session):
        """Restore media and static files"""
        try:
            # Restore media files
            media_files = [f for f in zipf.namelist() if f.startswith('media/')]
            if media_files:
                self.stdout.write(f'Restoring {len(media_files)} media files...')
                
                # Create backup of current media directory
                if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
                    if os.path.exists(settings.MEDIA_ROOT):
                        backup_dir = f"{settings.MEDIA_ROOT}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copytree(settings.MEDIA_ROOT, backup_dir)
                        self.stdout.write(f'Current media directory backed up to: {backup_dir}')
                    
                    # Extract media files
                    for file_path in media_files:
                        zipf.extract(file_path, settings.MEDIA_ROOT)
                    
                    self.stdout.write(self.style.SUCCESS('Media files restored successfully'))
            
            # Restore static files
            static_files = [f for f in zipf.namelist() if f.startswith('static/')]
            if static_files:
                self.stdout.write(f'Restoring {len(static_files)} static files...')
                
                # Create backup of current static directory
                if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                    if os.path.exists(settings.STATIC_ROOT):
                        backup_dir = f"{settings.STATIC_ROOT}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copytree(settings.STATIC_ROOT, backup_dir)
                        self.stdout.write(f'Current static directory backed up to: {backup_dir}')
                    
                    # Extract static files
                    for file_path in static_files:
                        zipf.extract(file_path, settings.STATIC_ROOT)
                    
                    self.stdout.write(self.style.SUCCESS('Static files restored successfully'))
            
            # Log the restore
            BackupAuditLog.objects.create(
                backup_session=restore_session,
                level='info',
                message='Files restored successfully',
                details={
                    'media_files': len(media_files),
                    'static_files': len(static_files)
                }
            )
            
        except Exception as e:
            raise Exception(f'Files restore failed: {str(e)}')

    def _restore_config(self, zipf, restore_session):
        """Restore configuration files"""
        try:
            config_files = [f for f in zipf.namelist() if f.startswith('config/')]
            
            if not config_files:
                self.stdout.write(self.style.WARNING('No configuration files found in backup'))
                return
            
            self.stdout.write(f'Restoring {len(config_files)} configuration files...')
            
            # Create backup of current config files
            for config_file in config_files:
                filename = os.path.basename(config_file)
                
                if filename == 'settings.py':
                    current_path = os.path.join(settings.BASE_DIR, 'logisEdge', 'settings.py')
                elif filename == 'requirements.txt':
                    current_path = os.path.join(settings.BASE_DIR, 'requirements.txt')
                elif filename == 'manage.py':
                    current_path = os.path.join(settings.BASE_DIR, 'manage.py')
                else:
                    continue
                
                if os.path.exists(current_path):
                    backup_name = f"{current_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(current_path, backup_name)
                    self.stdout.write(f'Current {filename} backed up to: {backup_name}')
            
            # Extract config files
            for config_file in config_files:
                filename = os.path.basename(config_file)
                
                if filename == 'settings.py':
                    target_path = os.path.join(settings.BASE_DIR, 'logisEdge', 'settings.py')
                elif filename == 'requirements.txt':
                    target_path = os.path.join(settings.BASE_DIR, 'requirements.txt')
                elif filename == 'manage.py':
                    target_path = os.path.join(settings.BASE_DIR, 'manage.py')
                else:
                    continue
                
                # Extract to temporary location first
                zipf.extract(config_file, '/tmp')
                temp_file = f'/tmp/{config_file}'
                
                if os.path.exists(temp_file):
                    shutil.copy2(temp_file, target_path)
                    os.remove(temp_file)
            
            self.stdout.write(self.style.SUCCESS('Configuration files restored successfully'))
            
            # Log the restore
            BackupAuditLog.objects.create(
                backup_session=restore_session,
                level='info',
                message='Configuration files restored successfully',
                details={'config_files': len(config_files)}
            )
            
        except Exception as e:
            raise Exception(f'Configuration restore failed: {str(e)}')
