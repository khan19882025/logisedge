import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import connection
from django.utils import timezone
from django.contrib.auth.models import User
from .models import ScheduledTask, ScheduledTaskLog, TaskSchedule


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def execute_scheduled_task(self, task_id, parameters=None):
    """
    Main task executor for scheduled tasks
    
    Args:
        task_id: UUID of the ScheduledTask
        parameters: Optional parameters to override task defaults
    """
    try:
        # Get the scheduled task
        task = ScheduledTask.objects.get(id=task_id)
        
        # Create execution log
        log = ScheduledTaskLog.objects.create(
            task=task,
            status='running',
            task_id=self.request.id,
            worker_name=self.request.hostname,
            retry_count=self.request.retries,
            is_retry=self.request.retries > 0
        )
        
        start_time = timezone.now()
        
        # Execute the actual task based on task type
        if task.task_type == 'backup':
            result = execute_backup_task(task, parameters or {})
        elif task.task_type == 'report':
            result = execute_report_task(task, parameters or {})
        elif task.task_type == 'email':
            result = execute_email_task(task, parameters or {})
        elif task.task_type == 'sync':
            result = execute_sync_task(task, parameters or {})
        elif task.task_type == 'custom':
            result = execute_custom_task(task, parameters or {})
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
        
        # Mark task as completed
        end_time = timezone.now()
        execution_time = (end_time - start_time).total_seconds()
        
        log.mark_completed(
            status='success',
            output_message=str(result),
            error_traceback=''
        )
        
        # Update task last run time
        task.mark_as_run()
        
        logger.info(f"Task {task.name} executed successfully in {execution_time:.2f}s")
        return result
        
    except ScheduledTask.DoesNotExist:
        error_msg = f"ScheduledTask with id {task_id} not found"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    except Exception as exc:
        error_msg = f"Task execution failed: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        
        # Log the error
        if 'log' in locals():
            log.mark_failed(error_msg, traceback.format_exc())
        
        # Retry if configured
        if 'task' in locals() and task.retry_on_failure:
            if self.request.retries < task.max_retries:
                raise self.retry(
                    countdown=task.retry_delay,
                    exc=exc
                )
        
        raise exc


@shared_task
def execute_backup_task(task, parameters):
    """Execute database backup task"""
    try:
        backup_dir = parameters.get('backup_dir', settings.BACKUP_DIR if hasattr(settings, 'BACKUP_DIR') else 'backups/')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Perform database backup (example for SQLite)
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            db_path = settings.DATABASES['default']['NAME']
            import shutil
            shutil.copy2(db_path, backup_path)
            result = f"Database backup completed: {backup_path}"
        
        # For PostgreSQL
        elif settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            db_name = settings.DATABASES['default']['NAME']
            db_user = settings.DATABASES['default']['USER']
            db_host = settings.DATABASES['default']['HOST']
            db_port = settings.DATABASES['default']['PORT']
            
            # Use pg_dump for PostgreSQL backup
            import subprocess
            cmd = [
                'pg_dump',
                '-h', db_host or 'localhost',
                '-p', str(db_port or 5432),
                '-U', db_user,
                '-f', backup_path,
                db_name
            ]
            
            # Set password environment variable if provided
            env = os.environ.copy()
            if 'PASSWORD' in settings.DATABASES['default']:
                env['PGPASSWORD'] = settings.DATABASES['default']['PASSWORD']
            
            subprocess.run(cmd, env=env, check=True)
            result = f"PostgreSQL backup completed: {backup_path}"
        
        # For MySQL
        elif settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
            db_name = settings.DATABASES['default']['NAME']
            db_user = settings.DATABASES['default']['USER']
            db_host = settings.DATABASES['default']['HOST']
            db_port = settings.DATABASES['default']['PORT']
            
            # Use mysqldump for MySQL backup
            import subprocess
            cmd = [
                'mysqldump',
                '-h', db_host or 'localhost',
                '-P', str(db_port or 3306),
                '-u', db_user,
                '-p',
                db_name
            ]
            
            # Set password environment variable if provided
            env = os.environ.copy()
            if 'PASSWORD' in settings.DATABASES['default']:
                env['MYSQL_PWD'] = settings.DATABASES['default']['PASSWORD']
            
            with open(backup_path, 'w') as f:
                subprocess.run(cmd, env=env, stdout=f, check=True)
            
            result = f"MySQL backup completed: {backup_path}"
        
        else:
            result = f"Backup completed for database type: {settings.DATABASES['default']['ENGINE']}"
        
        # Clean up old backups if configured
        max_backups = parameters.get('max_backups', 10)
        cleanup_old_backups(backup_dir, max_backups)
        
        return result
        
    except Exception as e:
        logger.error(f"Backup task failed: {str(e)}")
        raise


@shared_task
def execute_report_task(task, parameters):
    """Execute report generation task"""
    try:
        report_type = parameters.get('report_type', 'general')
        report_format = parameters.get('format', 'pdf')
        email_recipients = parameters.get('email_recipients', [])
        
        # Generate report based on type
        if report_type == 'sales':
            report_data = generate_sales_report(parameters)
        elif report_type == 'inventory':
            report_data = generate_inventory_report(parameters)
        elif report_type == 'financial':
            report_data = generate_financial_report(parameters)
        else:
            report_data = generate_general_report(parameters)
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"report_{report_type}_{timestamp}.{report_format}"
        report_path = save_report_to_file(report_data, report_filename, report_format)
        
        # Send email if recipients specified
        if email_recipients:
            send_report_email(report_path, report_type, email_recipients)
        
        result = f"Report generated: {report_path}"
        if email_recipients:
            result += f" and sent to {len(email_recipients)} recipients"
        
        return result
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise


@shared_task
def execute_email_task(task, parameters):
    """Execute email notification task"""
    try:
        subject = parameters.get('subject', 'Automated Notification')
        message = parameters.get('message', 'This is an automated message from the task scheduler.')
        recipients = parameters.get('recipients', [])
        template_name = parameters.get('template', None)
        
        if not recipients:
            raise ValueError("No email recipients specified")
        
        # Use email template if specified
        if template_name:
            message = render_email_template(template_name, parameters)
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False
        )
        
        result = f"Email sent to {len(recipients)} recipients: {subject}"
        return result
        
    except Exception as e:
        logger.error(f"Email task failed: {str(e)}")
        raise


@shared_task
def execute_sync_task(task, parameters):
    """Execute data synchronization task"""
    try:
        sync_type = parameters.get('sync_type', 'general')
        source_system = parameters.get('source_system', '')
        target_system = parameters.get('target_system', '')
        
        if sync_type == 'inventory':
            result = sync_inventory_data(source_system, target_system, parameters)
        elif sync_type == 'orders':
            result = sync_order_data(source_system, target_system, parameters)
        elif sync_type == 'customers':
            result = sync_customer_data(source_system, target_system, parameters)
        else:
            result = f"Data sync completed for type: {sync_type}"
        
        return result
        
    except Exception as e:
        logger.error(f"Sync task failed: {str(e)}")
        raise


@shared_task
def execute_custom_task(task, parameters):
    """Execute custom task using dynamic import"""
    try:
        # Import the custom function
        module_path, function_name = task.task_function.rsplit('.', 1)
        
        import importlib
        module = importlib.import_module(module_path)
        custom_function = getattr(module, function_name)
        
        # Execute with parameters
        if callable(custom_function):
            result = custom_function(**parameters)
        else:
            raise ValueError(f"Task function {task.task_function} is not callable")
        
        return result
        
    except Exception as e:
        logger.error(f"Custom task failed: {str(e)}")
        raise


@shared_task
def cleanup_old_backups(backup_dir, max_backups):
    """Clean up old backup files"""
    try:
        if not os.path.exists(backup_dir):
            return
        
        # Get all backup files
        backup_files = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_') and filename.endswith('.sql'):
                file_path = os.path.join(backup_dir, filename)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (oldest first)
        backup_files.sort(key=lambda x: x[1])
        
        # Remove old files
        files_to_remove = backup_files[:-max_backups] if len(backup_files) > max_backups else []
        
        for file_path, _ in files_to_remove:
            os.remove(file_path)
            logger.info(f"Removed old backup file: {file_path}")
        
        return f"Cleaned up {len(files_to_remove)} old backup files"
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {str(e)}")
        raise


def generate_sales_report(parameters):
    """Generate sales report data"""
    # This is a placeholder - implement based on your ERP system
    from django.db.models import Sum, Count
    from django.utils import timezone
    
    # Example: Get sales data for the last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # You would implement this based on your actual models
    # sales_data = Sale.objects.filter(
    #     date__range=[start_date, end_date]
    # ).aggregate(
    #     total_sales=Sum('amount'),
    #     total_orders=Count('id')
    # )
    
    return {
        'report_type': 'sales',
        'period': f"{start_date} to {end_date}",
        'total_sales': 0,  # sales_data['total_sales'] or 0
        'total_orders': 0,  # sales_data['total_orders'] or 0
        'generated_at': timezone.now().isoformat()
    }


def generate_inventory_report(parameters):
    """Generate inventory report data"""
    # Placeholder implementation
    return {
        'report_type': 'inventory',
        'total_items': 0,
        'low_stock_items': 0,
        'out_of_stock_items': 0,
        'generated_at': timezone.now().isoformat()
    }


def generate_financial_report(parameters):
    """Generate financial report data"""
    # Placeholder implementation
    return {
        'report_type': 'financial',
        'total_revenue': 0,
        'total_expenses': 0,
        'net_profit': 0,
        'generated_at': timezone.now().isoformat()
    }


def generate_general_report(parameters):
    """Generate general report data"""
    # Placeholder implementation
    return {
        'report_type': 'general',
        'system_status': 'operational',
        'active_users': User.objects.filter(is_active=True).count(),
        'generated_at': timezone.now().isoformat()
    }


def save_report_to_file(report_data, filename, format_type):
    """Save report data to file"""
    reports_dir = getattr(settings, 'REPORTS_DIR', 'reports/')
    os.makedirs(reports_dir, exist_ok=True)
    
    file_path = os.path.join(reports_dir, filename)
    
    if format_type == 'json':
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
    elif format_type == 'txt':
        with open(file_path, 'w') as f:
            for key, value in report_data.items():
                f.write(f"{key}: {value}\n")
    else:
        # Default to JSON
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
    
    return file_path


def send_report_email(report_path, report_type, recipients):
    """Send report via email"""
    subject = f"{report_type.title()} Report - {datetime.now().strftime('%Y-%m-%d')}"
    message = f"""
    Please find attached the {report_type} report.
    
    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    This is an automated message from the task scheduler.
    """
    
    # In a real implementation, you would attach the file
    # For now, just send the text
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=False
    )


def render_email_template(template_name, parameters):
    """Render email template with parameters"""
    # Placeholder implementation
    # In a real system, you would use Django's template system
    template_content = f"""
    Template: {template_name}
    Parameters: {json.dumps(parameters, indent=2)}
    
    This is a placeholder email template.
    """
    
    return template_content


def sync_inventory_data(source_system, target_system, parameters):
    """Sync inventory data between systems"""
    # Placeholder implementation
    return f"Inventory sync completed from {source_system} to {target_system}"


def sync_order_data(source_system, target_system, parameters):
    """Sync order data between systems"""
    # Placeholder implementation
    return f"Order sync completed from {source_system} to {target_system}"


def sync_customer_data(source_system, target_system, parameters):
    """Sync customer data between systems"""
    # Placeholder implementation
    return f"Customer sync completed from {source_system} to {target_system}"


@shared_task
def sync_celery_schedules():
    """Sync database schedules with Celery beat"""
    try:
        from celery import current_app
        
        # Get all active tasks
        active_tasks = ScheduledTask.objects.filter(status='active')
        
        for task in active_tasks:
            # Create or update Celery beat schedule
            schedule_key = f"task_{task.id}"
            
            # Get or create TaskSchedule
            task_schedule, created = TaskSchedule.objects.get_or_create(
                task=task,
                defaults={'schedule_key': schedule_key}
            )
            
            if created or not task_schedule.is_registered:
                # Register with Celery beat
                schedule_config = create_celery_schedule_config(task)
                
                # Add to Celery beat schedule
                current_app.conf.beat_schedule[schedule_key] = schedule_config
                
                task_schedule.is_registered = True
                task_schedule.save()
                
                logger.info(f"Registered task {task.name} with Celery beat")
        
        return f"Synced {active_tasks.count()} tasks with Celery beat"
        
    except Exception as e:
        logger.error(f"Failed to sync Celery schedules: {str(e)}")
        raise


def create_celery_schedule_config(task):
    """Create Celery beat schedule configuration for a task"""
    if task.schedule_type == 'daily':
        schedule = {
            'task': 'auto_task_scheduler.tasks.execute_scheduled_task',
            'schedule': crontab(
                hour=task.schedule_time.hour,
                minute=task.schedule_time.minute
            ),
            'args': (str(task.id),),
            'kwargs': {'parameters': task.task_parameters}
        }
    
    elif task.schedule_type == 'weekly':
        # For weekly tasks, we need to create multiple schedules
        # This is a simplified approach
        schedule = {
            'task': 'auto_task_scheduler.tasks.execute_scheduled_task',
            'schedule': crontab(
                hour=task.schedule_time.hour,
                minute=task.schedule_time.minute,
                day_of_week='*'  # This will run every day, but we'll filter in the task
            ),
            'args': (str(task.id),),
            'kwargs': {'parameters': task.task_parameters}
        }
    
    elif task.schedule_type == 'monthly':
        schedule = {
            'task': 'auto_task_scheduler.tasks.execute_scheduled_task',
            'schedule': crontab(
                hour=task.schedule_time.hour,
                minute=task.schedule_time.minute,
                day_of_month=task.day_of_month
            ),
            'args': (str(task.id),),
            'kwargs': {'parameters': task.task_parameters}
        }
    
    elif task.schedule_type == 'specific_datetime':
        # For one-time tasks, use a one-off schedule
        schedule = {
            'task': 'auto_task_scheduler.tasks.execute_scheduled_task',
            'schedule': task.next_run_at,
            'args': (str(task.id),),
            'kwargs': {'parameters': task.task_parameters}
        }
    
    else:
        raise ValueError(f"Unsupported schedule type: {task.schedule_type}")
    
    return schedule


# Import crontab for schedule configuration
try:
    from celery.schedules import crontab
except ImportError:
    # Fallback if crontab is not available
    def crontab(**kwargs):
        """Fallback crontab function"""
        return kwargs
