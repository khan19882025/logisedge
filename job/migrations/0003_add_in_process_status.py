# Generated migration to add 'In Process' status

from django.db import migrations

def create_in_process_status(apps, schema_editor):
    JobStatus = apps.get_model('job', 'JobStatus')
    
    # Create 'In Process' status if it doesn't exist
    JobStatus.objects.get_or_create(
        name='In Process',
        defaults={
            'color': '#007bff',  # Blue color
            'description': 'Job is currently being processed',
            'is_active': True
        }
    )
    
    # Create other common statuses if they don't exist
    common_statuses = [
        {'name': 'Pending', 'color': '#ffc107', 'description': 'Job is waiting to be started'},
        {'name': 'Completed', 'color': '#28a745', 'description': 'Job has been completed'},
        {'name': 'On Hold', 'color': '#dc3545', 'description': 'Job is temporarily on hold'},
        {'name': 'Cancelled', 'color': '#6c757d', 'description': 'Job has been cancelled'},
    ]
    
    for status_data in common_statuses:
        JobStatus.objects.get_or_create(
            name=status_data['name'],
            defaults={
                'color': status_data['color'],
                'description': status_data['description'],
                'is_active': True
            }
        )

def reverse_in_process_status(apps, schema_editor):
    JobStatus = apps.get_model('job', 'JobStatus')
    # Only remove the 'In Process' status, keep others as they might be in use
    JobStatus.objects.filter(name='In Process').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('job', '0002_add_job_types'),
    ]
    
    operations = [
        migrations.RunPython(create_in_process_status, reverse_in_process_status),
    ]