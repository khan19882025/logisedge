"""
Celery integration for Cron Job Viewer
This module provides automatic logging and monitoring of Celery task executions
"""

import logging
from celery import shared_task, signals
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import transaction

from .models import CronJob, CronJobLog

logger = get_task_logger(__name__)


@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Handle task start - create log entry and mark job as running"""
    try:
        # Find the cron job by task name
        task_name = task.name if task else sender.name
        cron_job = CronJob.objects.filter(task=task_name, is_active=True).first()
        
        if cron_job:
            # Create log entry
            log = CronJobLog.objects.create(
                job=cron_job,
                celery_task_id=task_id,
                worker_name=getattr(sender, 'hostname', 'unknown')
            )
            
            # Mark job as running
            cron_job.mark_as_running()
            
            # Store log ID in task request for later use
            if hasattr(sender, 'request'):
                sender.request.cron_log_id = log.id
                
            logger.info(f"Started cron job: {cron_job.name} (Task ID: {task_id})")
            
    except Exception as e:
        logger.error(f"Error in task_prerun_handler: {str(e)}")


@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Handle successful task completion"""
    try:
        task_name = sender.name
        task_id = getattr(sender.request, 'id', None)
        
        # Find the cron job
        cron_job = CronJob.objects.filter(task=task_name, is_active=True).first()
        
        if cron_job:
            # Find the log entry
            log_id = getattr(sender.request, 'cron_log_id', None)
            if log_id:
                try:
                    log = CronJobLog.objects.get(id=log_id)
                    log.mark_completed(
                        status='success',
                        output_message=f"Task completed successfully. Result: {str(result)[:500]}"
                    )
                except CronJobLog.DoesNotExist:
                    # Create a new log entry if the original wasn't found
                    log = CronJobLog.objects.create(
                        job=cron_job,
                        celery_task_id=task_id,
                        worker_name=getattr(sender.request, 'hostname', 'unknown')
                    )
                    log.mark_completed(
                        status='success',
                        output_message=f"Task completed successfully. Result: {str(result)[:500]}"
                    )
            
            # Mark job as completed successfully
            cron_job.mark_as_completed(status='success')
            
            logger.info(f"Completed cron job: {cron_job.name} (Task ID: {task_id})")
            
    except Exception as e:
        logger.error(f"Error in task_success_handler: {str(e)}")


@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """Handle task failure"""
    try:
        task_name = sender.name
        
        # Find the cron job
        cron_job = CronJob.objects.filter(task=task_name, is_active=True).first()
        
        if cron_job:
            # Find the log entry
            log_id = getattr(sender.request, 'cron_log_id', None)
            if log_id:
                try:
                    log = CronJobLog.objects.get(id=log_id)
                    log.mark_completed(
                        status='failed',
                        output_message=f"Task failed: {str(exception)}"
                    )
                except CronJobLog.DoesNotExist:
                    # Create a new log entry if the original wasn't found
                    log = CronJobLog.objects.create(
                        job=cron_job,
                        celery_task_id=task_id,
                        worker_name=getattr(sender.request, 'hostname', 'unknown')
                    )
                    log.mark_completed(
                        status='failed',
                        output_message=f"Task failed: {str(exception)}"
                    )
            
            # Mark job as failed
            cron_job.mark_as_completed(status='failed')
            
            logger.error(f"Failed cron job: {cron_job.name} (Task ID: {task_id}): {str(exception)}")
            
    except Exception as e:
        logger.error(f"Error in task_failure_handler: {str(e)}")


@signals.task_revoked.connect
def task_revoked_handler(sender=None, request=None, terminated=False, signum=None, expired=False, **kwargs):
    """Handle task revocation"""
    try:
        task_name = sender.name
        task_id = getattr(request, 'id', None)
        
        # Find the cron job
        cron_job = CronJob.objects.filter(task=task_name, is_active=True).first()
        
        if cron_job:
            # Find the log entry
            log_id = getattr(request, 'cron_log_id', None)
            if log_id:
                try:
                    log = CronJobLog.objects.get(id=log_id)
                    log.mark_completed(
                        status='failed',
                        output_message=f"Task revoked (terminated: {terminated}, expired: {expired})"
                    )
                except CronJobLog.DoesNotExist:
                    # Create a new log entry if the original wasn't found
                    log = CronJobLog.objects.create(
                        job=cron_job,
                        celery_task_id=task_id,
                        worker_name=getattr(request, 'hostname', 'unknown')
                    )
                    log.mark_completed(
                        status='failed',
                        output_message=f"Task revoked (terminated: {terminated}, expired: {expired})"
                    )
            
            # Mark job as failed
            cron_job.mark_as_completed(status='failed')
            
            logger.warning(f"Revoked cron job: {cron_job.name} (Task ID: {task_id})")
            
    except Exception as e:
        logger.error(f"Error in task_revoked_handler: {str(e)}")


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_celery_beat_schedules(self):
    """Sync cron jobs with Celery Beat schedules"""
    try:
        from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
        
        # Get all periodic tasks from Celery Beat
        periodic_tasks = PeriodicTask.objects.filter(enabled=True)
        
        synced_count = 0
        for pt in periodic_tasks:
            try:
                # Extract schedule information
                if hasattr(pt, 'crontab') and pt.crontab:
                    # Cron schedule
                    schedule = pt.crontab.hourly
                    if pt.crontab.minute != '*':
                        schedule = f"{pt.crontab.minute} {pt.crontab.hour} * * *"
                    elif pt.crontab.hour != '*':
                        schedule = f"0 {pt.crontab.hour} * * *"
                    else:
                        schedule = "0 0 * * *"
                elif hasattr(pt, 'interval') and pt.interval:
                    # Interval schedule
                    interval = pt.interval
                    if interval.period == 'seconds':
                        schedule = f"every {interval.every} second"
                    elif interval.period == 'minutes':
                        schedule = f"every {interval.every} minute"
                    elif interval.period == 'hours':
                        schedule = f"every {interval.every} hour"
                    elif interval.period == 'days':
                        schedule = f"every {interval.every} day"
                    else:
                        continue
                else:
                    continue
                
                # Try to find existing cron job
                cron_job, created = CronJob.objects.get_or_create(
                    task=pt.task,
                    defaults={
                        'name': pt.name or pt.task,
                        'schedule': schedule,
                        'is_active': pt.enabled,
                        'owner_id': 1,  # Default to first user, adjust as needed
                    }
                )
                
                if not created:
                    # Update existing job
                    cron_job.schedule = schedule
                    cron_job.is_active = pt.enabled
                    cron_job.save()
                
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Error syncing periodic task {pt.name}: {str(e)}")
                continue
        
        logger.info(f"Successfully synced {synced_count} cron jobs with Celery Beat")
        return f"Synced {synced_count} cron jobs"
        
    except Exception as e:
        logger.error(f"Error syncing Celery Beat schedules: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_old_cron_logs(self, days_to_keep=30):
    """Clean up old cron job logs to prevent database bloat"""
    try:
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        deleted_count, _ = CronJobLog.objects.filter(
            run_started_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old cron job logs (older than {days_to_keep} days)")
        return f"Cleaned up {deleted_count} old logs"
        
    except Exception as e:
        logger.error(f"Error cleaning up old cron logs: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def health_check_cron_jobs(self):
    """Health check for cron jobs - identify stuck or overdue jobs"""
    try:
        now = timezone.now()
        
        # Find stuck jobs (running for more than 1 hour)
        stuck_jobs = CronJob.objects.filter(
            last_status='running',
            last_run_at__lt=now - timedelta(hours=1)
        )
        
        stuck_count = 0
        for job in stuck_jobs:
            try:
                # Mark as failed
                job.mark_as_completed(status='failed')
                
                # Create a log entry for the stuck job
                CronJobLog.objects.create(
                    job=job,
                    celery_task_id='health_check',
                    worker_name='health_checker'
                ).mark_completed(
                    status='failed',
                    output_message='Job marked as stuck by health check (running for more than 1 hour)'
                )
                
                stuck_count += 1
                
            except Exception as e:
                logger.error(f"Error handling stuck job {job.name}: {str(e)}")
                continue
        
        # Find overdue jobs (next_run_at in the past)
        overdue_jobs = CronJob.objects.filter(
            is_active=True,
            next_run_at__lt=now
        )
        
        overdue_count = 0
        for job in overdue_jobs:
            try:
                # Recalculate next run time
                job.calculate_next_run()
                overdue_count += 1
                
            except Exception as e:
                logger.error(f"Error recalculating overdue job {job.name}: {str(e)}")
                continue
        
        logger.info(f"Health check completed: {stuck_count} stuck jobs, {overdue_count} overdue jobs")
        return f"Health check: {stuck_count} stuck, {overdue_count} overdue"
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def execute_cron_job(self, job_id):
    """Execute a specific cron job manually"""
    try:
        cron_job = CronJob.objects.get(id=job_id, is_active=True)
        
        # Create log entry
        log = CronJobLog.objects.create(
            job=cron_job,
            celery_task_id=self.request.id,
            worker_name=self.request.hostname
        )
        
        # Mark job as running
        cron_job.mark_as_running()
        
        # Here you would typically execute the actual task
        # For now, we'll simulate execution
        import time
        time.sleep(2)  # Simulate execution time
        
        # Mark as completed
        log.mark_completed(
            status='success',
            output_message='Job executed manually via Celery task'
        )
        
        cron_job.mark_as_completed(status='success')
        
        logger.info(f"Manually executed cron job: {cron_job.name}")
        return f"Successfully executed {cron_job.name}"
        
    except CronJob.DoesNotExist:
        logger.error(f"Cron job with ID {job_id} not found or inactive")
        raise
    except Exception as e:
        logger.error(f"Error executing cron job {job_id}: {str(e)}")
        raise self.retry(exc=e)
