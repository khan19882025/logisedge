from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CronJob, CronJobLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class CronJobLogSerializer(serializers.ModelSerializer):
    """Serializer for cron job execution logs"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_formatted = serializers.CharField(source='duration_formatted', read_only=True)
    status_badge_class = serializers.CharField(source='status_badge_class', read_only=True)
    
    class Meta:
        model = CronJobLog
        fields = [
            'id', 'status', 'status_display', 'run_started_at', 'run_ended_at',
            'execution_time', 'duration_formatted', 'output_message', 
            'celery_task_id', 'worker_name', 'status_badge_class'
        ]
        read_only_fields = ['id', 'run_started_at', 'run_ended_at', 'execution_time', 
                           'duration_formatted', 'status_badge_class']


class CronJobSerializer(serializers.ModelSerializer):
    """Main serializer for cron jobs"""
    
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='owner',
        write_only=True
    )
    
    # Nested serializers
    execution_logs = CronJobLogSerializer(many=True, read_only=True)
    
    # Computed fields
    schedule_display = serializers.CharField(source='schedule_display', read_only=True)
    next_run_formatted = serializers.CharField(source='next_run_formatted', read_only=True)
    last_run_formatted = serializers.CharField(source='last_run_formatted', read_only=True)
    
    # Status badge for frontend
    status_badge_class = serializers.SerializerMethodField()
    
    class Meta:
        model = CronJob
        fields = [
            'id', 'name', 'description', 'task', 'schedule', 'schedule_display',
            'next_run_at', 'next_run_formatted', 'last_run_at', 'last_run_formatted',
            'last_status', 'status_badge_class', 'is_active', 'owner', 'owner_id',
            'created_at', 'updated_at', 'execution_logs'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'next_run_at', 'last_run_at']
    
    def get_status_badge_class(self, obj):
        """Return CSS class for status badge"""
        status_classes = {
            'success': 'bg-green-100 text-green-800',
            'failed': 'bg-red-100 text-red-800',
            'pending': 'bg-gray-100 text-gray-800',
            'running': 'bg-blue-100 text-blue-800',
        }
        return status_classes.get(obj.last_status, 'bg-gray-100 text-gray-800')
    
    def validate_schedule(self, value):
        """Validate schedule format"""
        if not value:
            raise serializers.ValidationError("Schedule is required")
        
        try:
            # Test if it's a valid schedule
            if value.startswith('every'):
                # Validate interval format
                parts = value.lower().split()
                if len(parts) != 3 or parts[0] != 'every':
                    raise serializers.ValidationError(
                        "Interval format must be 'every <number> <unit>'"
                    )
                
                number = int(parts[1])
                unit = parts[2]
                
                if unit.endswith('s'):
                    unit = unit[:-1]
                
                valid_units = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']
                if unit not in valid_units:
                    raise serializers.ValidationError(f"Invalid time unit: {unit}")
                
                if number <= 0:
                    raise serializers.ValidationError("Number must be positive")
                    
            else:
                # Validate cron expression
                import croniter
                croniter.croniter(value, '2023-01-01 00:00:00')
                
        except (ValueError, IndexError) as e:
            raise serializers.ValidationError(f"Invalid schedule format: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Invalid schedule: {str(e)}")
        
        return value
    
    def validate_task(self, value):
        """Validate task name format"""
        if not value:
            raise serializers.ValidationError("Task name is required")
        
        # Basic validation for Celery task format
        if '.' not in value or len(value.split('.')) < 2:
            raise serializers.ValidationError(
                "Task must be in format 'app.tasks.function_name'"
            )
        
        return value
    
    def create(self, validated_data):
        """Override create to set owner automatically and calculate next run"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['owner'] = request.user
        
        # Create the job
        job = super().create(validated_data)
        
        # Calculate next run time
        job.calculate_next_run()
        
        return job
    
    def update(self, instance, validated_data):
        """Override update to recalculate next run if schedule changes"""
        # Check if schedule changed
        schedule_changed = 'schedule' in validated_data and validated_data['schedule'] != instance.schedule
        
        # Update the instance
        job = super().update(instance, validated_data)
        
        # Recalculate next run if schedule changed
        if schedule_changed:
            job.calculate_next_run()
        
        return job


class CronJobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new cron jobs"""
    
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='owner',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = CronJob
        fields = [
            'name', 'description', 'task', 'schedule', 'is_active', 'owner_id'
        ]
    
    def validate(self, data):
        """Custom validation for job creation"""
        # Set default owner if not provided
        request = self.context.get('request')
        if request and hasattr(request, 'user') and 'owner' not in data:
            data['owner'] = request.user
        
        return super().validate(data)


class CronJobUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing cron jobs"""
    
    class Meta:
        model = CronJob
        fields = [
            'name', 'description', 'task', 'schedule', 'is_active'
        ]
    
    def validate(self, data):
        """Custom validation for job updates"""
        # Ensure only the owner can update the job
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            instance = self.instance
            if instance and instance.owner != request.user:
                raise serializers.ValidationError(
                    "You can only update your own cron jobs"
                )
        
        return super().validate(data)


class CronJobStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating cron job status"""
    
    is_active = serializers.BooleanField()
    
    def validate_is_active(self, value):
        """Validate status change"""
        instance = self.instance
        if not instance:
            raise serializers.ValidationError("No cron job instance provided")
        
        return value


class CronJobLogFilterSerializer(serializers.Serializer):
    """Serializer for filtering cron job logs"""
    
    status = serializers.ChoiceField(
        choices=CronJobLog.STATUS_CHOICES,
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)
    
    def validate(self, data):
        """Validate date range"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "Date from cannot be after date to"
            )
        
        return data


class CronJobStatisticsSerializer(serializers.Serializer):
    """Serializer for cron job statistics"""
    
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    inactive_jobs = serializers.IntegerField()
    
    jobs_by_status = serializers.DictField()
    jobs_by_schedule_type = serializers.DictField()
    
    recent_executions = serializers.IntegerField()
    successful_executions = serializers.IntegerField()
    failed_executions = serializers.IntegerField()
    
    average_execution_time = serializers.FloatField()
    total_execution_time = serializers.FloatField()


class CronJobRefreshSerializer(serializers.Serializer):
    """Serializer for refreshing cron jobs from Celery Beat"""
    
    force_refresh = serializers.BooleanField(default=False)
    sync_schedules = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validate refresh parameters"""
        return data
