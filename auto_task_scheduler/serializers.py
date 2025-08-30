from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ScheduledTask, ScheduledTaskLog, TaskSchedule


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class ScheduledTaskLogSerializer(serializers.ModelSerializer):
    """Serializer for task execution logs"""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    
    class Meta:
        model = ScheduledTaskLog
        fields = [
            'id', 'status', 'status_display', 'started_at', 'completed_at',
            'execution_time', 'duration_formatted', 'output_message',
            'error_traceback', 'task_id', 'worker_name', 'retry_count', 'is_retry'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'execution_time', 
                           'duration_formatted', 'task_id', 'worker_name', 'retry_count', 'is_retry']


class TaskScheduleSerializer(serializers.ModelSerializer):
    """Serializer for Celery beat schedule configuration"""
    
    class Meta:
        model = TaskSchedule
        fields = ['id', 'schedule_key', 'is_registered', 'last_sync']
        read_only_fields = ['id', 'last_sync']


class ScheduledTaskSerializer(serializers.ModelSerializer):
    """Main serializer for scheduled tasks"""
    
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    schedule_type_display = serializers.CharField(source='get_schedule_type_display', read_only=True)
    
    # Nested serializers
    execution_logs = ScheduledTaskLogSerializer(many=True, read_only=True)
    celery_schedule = TaskScheduleSerializer(read_only=True)
    
    # Computed fields
    next_run_formatted = serializers.SerializerMethodField()
    last_run_formatted = serializers.SerializerMethodField()
    schedule_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledTask
        fields = [
            'id', 'name', 'description', 'task_type', 'task_type_display',
            'schedule_type', 'schedule_type_display', 'schedule_time', 'schedule_date',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'day_of_month', 'task_function', 'task_parameters', 'status', 'status_display',
            'last_run_at', 'last_run_formatted', 'next_run_at', 'next_run_formatted',
            'max_execution_time', 'retry_on_failure', 'max_retries', 'retry_delay',
            'user', 'user_id', 'is_public', 'created_at', 'updated_at',
            'execution_logs', 'celery_schedule', 'schedule_summary'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_run_at', 'next_run_at']
    
    def get_next_run_formatted(self, obj):
        """Format next run time for display"""
        if obj.next_run_at:
            return obj.next_run_at.strftime('%Y-%m-%d %H:%M:%S')
        return "Not scheduled"
    
    def get_last_run_formatted(self, obj):
        """Format last run time for display"""
        if obj.last_run_at:
            return obj.last_run_at.strftime('%Y-%m-%d %H:%M:%S')
        return "Never"
    
    def get_schedule_summary(self, obj):
        """Generate human-readable schedule summary"""
        if obj.schedule_type == 'daily':
            return f"Daily at {obj.schedule_time.strftime('%H:%M')}"
        
        elif obj.schedule_type == 'weekly':
            weekdays = []
            if obj.monday: weekdays.append('Mon')
            if obj.tuesday: weekdays.append('Tue')
            if obj.wednesday: weekdays.append('Wed')
            if obj.thursday: weekdays.append('Thu')
            if obj.friday: weekdays.append('Fri')
            if obj.saturday: weekdays.append('Sat')
            if obj.sunday: weekdays.append('Sun')
            
            if weekdays:
                return f"Weekly on {', '.join(weekdays)} at {obj.schedule_time.strftime('%H:%M')}"
            return "Weekly (no days selected)"
        
        elif obj.schedule_type == 'monthly':
            return f"Monthly on day {obj.day_of_month} at {obj.schedule_time.strftime('%H:%M')}"
        
        elif obj.schedule_type == 'specific_datetime':
            if obj.schedule_date:
                return f"Once on {obj.schedule_date} at {obj.schedule_time.strftime('%H:%M')}"
            return "Specific date/time (no date set)"
        
        return "Schedule not configured"
    
    def validate(self, data):
        """Custom validation for task configuration"""
        # Validate schedule configuration based on schedule type
        schedule_type = data.get('schedule_type')
        
        if schedule_type == 'specific_datetime':
            if not data.get('schedule_date'):
                raise serializers.ValidationError(
                    "Specific date is required for specific_datetime schedule type"
                )
        
        elif schedule_type == 'weekly':
            # At least one day must be selected for weekly tasks
            weekdays = [
                data.get('monday', False), data.get('tuesday', False),
                data.get('wednesday', False), data.get('thursday', False),
                data.get('friday', False), data.get('saturday', False),
                data.get('sunday', False)
            ]
            if not any(weekdays):
                raise serializers.ValidationError(
                    "At least one weekday must be selected for weekly tasks"
                )
        
        elif schedule_type == 'monthly':
            day_of_month = data.get('day_of_month')
            if not day_of_month or not (1 <= day_of_month <= 31):
                raise serializers.ValidationError(
                    "Day of month must be between 1 and 31 for monthly tasks"
                )
        
        # Validate task function
        if not data.get('task_function'):
            raise serializers.ValidationError("Task function is required")
        
        # Validate execution time limits
        max_execution_time = data.get('max_execution_time', 300)
        if max_execution_time < 60:
            raise serializers.ValidationError(
                "Maximum execution time must be at least 60 seconds"
            )
        if max_execution_time > 3600:
            raise serializers.ValidationError(
                "Maximum execution time cannot exceed 1 hour"
            )
        
        # Validate retry settings
        if data.get('retry_on_failure', True):
            max_retries = data.get('max_retries', 3)
            if max_retries > 10:
                raise serializers.ValidationError(
                    "Maximum retries cannot exceed 10"
                )
            
            retry_delay = data.get('retry_delay', 300)
            if retry_delay < 60:
                raise serializers.ValidationError(
                    "Retry delay must be at least 60 seconds"
                )
        
        return data
    
    def create(self, validated_data):
        """Override create to set user automatically"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        return super().create(validated_data)


class ScheduledTaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new scheduled tasks"""
    
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ScheduledTask
        fields = [
            'name', 'description', 'task_type', 'schedule_type', 'schedule_time',
            'schedule_date', 'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'day_of_month', 'task_function',
            'task_parameters', 'max_execution_time', 'retry_on_failure',
            'max_retries', 'retry_delay', 'is_public', 'user_id'
        ]
    
    def validate(self, data):
        """Custom validation for task creation"""
        # Set default user if not provided
        request = self.context.get('request')
        if request and hasattr(request, 'user') and 'user' not in data:
            data['user'] = request.user
        
        return super().validate(data)


class ScheduledTaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing scheduled tasks"""
    
    class Meta:
        model = ScheduledTask
        fields = [
            'name', 'description', 'task_type', 'schedule_type', 'schedule_time',
            'schedule_date', 'monday', 'tuesday', 'wednesday', 'thursday',
            'friday', 'saturday', 'sunday', 'day_of_month', 'task_function',
            'task_parameters', 'status', 'max_execution_time', 'retry_on_failure',
            'max_retries', 'retry_delay', 'is_public'
        ]
    
    def validate_status(self, value):
        """Validate status changes"""
        instance = self.instance
        if instance and instance.status == 'active' and value == 'inactive':
            # Task is being deactivated, this is allowed
            pass
        elif instance and instance.status == 'inactive' and value == 'active':
            # Task is being activated, validate configuration
            if not instance.task_function:
                raise serializers.ValidationError(
                    "Cannot activate task without a valid task function"
                )
        
        return value


class TaskStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating task status"""
    
    status = serializers.ChoiceField(choices=ScheduledTask.STATUS_CHOICES)
    
    def validate_status(self, value):
        """Validate status change"""
        instance = self.instance
        if not instance:
            raise serializers.ValidationError("No task instance provided")
        
        if value == 'active':
            # Check if task can be activated
            if not instance.task_function:
                raise serializers.ValidationError(
                    "Cannot activate task without a valid task function"
                )
            
            # Validate schedule configuration
            if instance.schedule_type == 'weekly':
                weekdays = [instance.monday, instance.tuesday, instance.wednesday,
                           instance.thursday, instance.friday, instance.saturday, instance.sunday]
                if not any(weekdays):
                    raise serializers.ValidationError(
                        "Cannot activate weekly task without selecting weekdays"
                    )
            
            elif instance.schedule_type == 'monthly':
                if not instance.day_of_month:
                    raise serializers.ValidationError(
                        "Cannot activate monthly task without setting day of month"
                    )
        
        return value


class TaskRunSerializer(serializers.Serializer):
    """Serializer for manually running tasks"""
    
    parameters = serializers.JSONField(required=False, default=dict)
    force_run = serializers.BooleanField(default=False)
    
    def validate_parameters(self, value):
        """Validate task parameters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a JSON object")
        return value


class TaskLogFilterSerializer(serializers.Serializer):
    """Serializer for filtering task logs"""
    
    status = serializers.ChoiceField(
        choices=ScheduledTaskLog.STATUS_CHOICES,
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


class TaskStatisticsSerializer(serializers.Serializer):
    """Serializer for task statistics"""
    
    total_tasks = serializers.IntegerField()
    active_tasks = serializers.IntegerField()
    inactive_tasks = serializers.IntegerField()
    paused_tasks = serializers.IntegerField()
    
    tasks_by_type = serializers.DictField()
    tasks_by_status = serializers.DictField()
    
    recent_executions = serializers.IntegerField()
    successful_executions = serializers.IntegerField()
    failed_executions = serializers.IntegerField()
    
    average_execution_time = serializers.FloatField()
    total_execution_time = serializers.FloatField()
