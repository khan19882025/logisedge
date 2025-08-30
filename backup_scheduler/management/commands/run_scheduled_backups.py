from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from backup_scheduler.models import (
    BackupSchedule, BackupExecution, BackupLog
)
from datetime import datetime, time, timedelta
import subprocess
import os
import shutil
import sqlite3
import json


class Command(BaseCommand):
    help = 'Run scheduled backups based on configured schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force run all active schedules regardless of timing',
        )

    def handle(self, *args, **options):
        self.stdout.write('Checking for scheduled backups...')
        
        now = timezone.now()
        current_time = now.time()
        current_date = now.date()
        
        # Get all active schedules
        active_schedules = BackupSchedule.objects.filter(is_active=True)
        
        if not active_schedules.exists():
            self.stdout.write('No active backup schedules found.')
            return
        
        for schedule in active_schedules:
            should_run = False
            
            if options['force']:
                should_run = True
            else:
                # Check if it's time to run this schedule
                if schedule.frequency == 'daily':
                    should_run = current_time >= schedule.start_time
                elif schedule.frequency == 'weekly' and schedule.weekday is not None:
                    should_run = (now.weekday() == schedule.weekday and 
                                current_time >= schedule.start_time)
                elif schedule.frequency == 'monthly' and schedule.day_of_month is not None:
                    should_run = (now.day == schedule.day_of_month and 
                                current_time >= schedule.start_time)
                elif schedule.frequency == 'yearly':
                    should_run = (now.month == schedule.start_date.month and 
                                now.day == schedule.start_date.day and 
                                current_time >= schedule.start_time)
            
            if should_run:
                self.stdout.write(f'Running scheduled backup: {schedule.name}')
                try:
                    self.run_backup(schedule)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to run backup {schedule.name}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Scheduled backup check completed!')
        )

    def run_backup(self, schedule):
        """Execute a backup based on the schedule"""
        # Create backup execution record
        execution = BackupExecution.objects.create(
            schedule=schedule,
            backup_type=schedule.backup_type,
            backup_scope=schedule.backup_scope,
            storage_location=schedule.storage_location,
            status='running',
            started_at=timezone.now(),
            is_manual=False,
            triggered_by=schedule.created_by
        )
        
        # Log the start
        BackupLog.objects.create(
            level='info',
            message=f'Started scheduled backup: {schedule.name}',
            execution=execution,
            user=schedule.created_by
        )
        
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(schedule.storage_location.path, 
                                    timezone.now().strftime('%Y-%m-%d'))
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{schedule.backup_scope.name}_{timestamp}.sql"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Perform database backup
            if schedule.backup_scope.name == 'full_database':
                self.backup_database(backup_path)
            else:
                self.backup_scope_data(schedule.backup_scope, backup_path)
            
            # Calculate file size
            file_size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            
            # Update execution record
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
            execution.file_path = backup_path
            execution.file_size_mb = round(file_size_mb, 2)
            execution.save()
            
            # Log success
            BackupLog.objects.create(
                level='info',
                message=f'Backup completed successfully: {backup_path}',
                execution=execution,
                user=schedule.created_by
            )
            
            self.stdout.write(f'Backup completed: {backup_path}')
            
        except Exception as e:
            # Update execution record with error
            execution.status = 'failed'
            execution.completed_at = timezone.now()
            execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
            execution.error_message = str(e)
            execution.save()
            
            # Log error
            BackupLog.objects.create(
                level='error',
                message=f'Backup failed: {str(e)}',
                execution=execution,
                user=schedule.created_by
            )
            
            raise e

    def backup_database(self, backup_path):
        """Create a full database backup"""
        # For SQLite, we can use the built-in backup functionality
        from django.conf import settings
        
        db_path = settings.DATABASES['default']['NAME']
        
        # Create a copy of the database file
        shutil.copy2(db_path, backup_path)
        
        # Verify the backup
        if not os.path.exists(backup_path):
            raise Exception("Backup file was not created")
        
        # Check file size
        if os.path.getsize(backup_path) == 0:
            raise Exception("Backup file is empty")

    def backup_scope_data(self, scope, backup_path):
        """Backup specific scope data"""
        # This is a simplified version - in production you'd want more sophisticated logic
        from django.conf import settings
        
        db_path = settings.DATABASES['default']['NAME']
        
        # For now, we'll create a full backup for any scope
        # In production, you might want to implement selective backup logic
        shutil.copy2(db_path, backup_path)
        
        if not os.path.exists(backup_path):
            raise Exception("Backup file was not created")
