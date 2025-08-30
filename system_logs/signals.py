from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import traceback
import sys
import hashlib
import json
from .models import SystemLog, ErrorPattern, ErrorPatternLog


def log_system_event(
    log_type='SYSTEM',
    severity='INFO',
    error_message='',
    error_type='',
    module='',
    function='',
    line_number=None,
    file_path='',
    user=None,
    user_ip=None,
    user_agent='',
    request_method='',
    request_url='',
    request_data=None,
    execution_time=None,
    memory_usage='',
    cpu_usage=None,
    content_type=None,
    object_id=None,
    object_name='',
    tags=None,
    context_data=None,
    environment='production',
    version='',
    stack_trace='',
    exception_details=None
):
    """
    Utility function to log system events programmatically
    """
    try:
        # Create system log entry
        log_entry = SystemLog.objects.create(
            log_type=log_type,
            severity=severity,
            error_message=error_message,
            error_type=error_type,
            module=module,
            function=function,
            line_number=line_number,
            file_path=file_path,
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            request_data=request_data or {},
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            content_type=content_type,
            object_id=object_id,
            object_name=object_name,
            tags=tags or [],
            context_data=context_data or {},
            environment=environment,
            version=version,
            stack_trace=stack_trace,
            exception_details=exception_details or {}
        )
        
        # Check for error patterns if this is an error
        if severity in ['ERROR', 'CRITICAL', 'FATAL'] and error_type:
            check_and_update_error_patterns(log_entry)
        
        return log_entry
    
    except Exception as e:
        # Fallback logging to prevent infinite loops
        print(f"Failed to create system log entry: {e}")
        return None


def check_and_update_error_patterns(log_entry):
    """
    Check if log entry matches existing error patterns and update accordingly
    """
    try:
        # Create a signature for the error
        signature_data = f"{log_entry.error_type}:{log_entry.module}:{log_entry.function}"
        pattern_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        # Try to find existing pattern
        try:
            pattern = ErrorPattern.objects.get(pattern_hash=pattern_hash)
            # Update existing pattern
            pattern.update_statistics(log_entry)
            
            # Link log to pattern
            ErrorPatternLog.objects.get_or_create(
                pattern=pattern,
                log_entry=log_entry
            )
            
        except ErrorPattern.DoesNotExist:
            # Create new pattern
            pattern = ErrorPattern.objects.create(
                pattern_type='EXCEPTION',
                pattern_hash=pattern_hash,
                error_signature=signature_data,
                error_type=log_entry.error_type,
                module=log_entry.module,
                function=log_entry.function,
                avg_severity=log_entry.severity,
                max_severity=log_entry.severity,
                avg_execution_time=log_entry.execution_time
            )
            
            # Link log to pattern
            ErrorPatternLog.objects.create(
                pattern=pattern,
                log_entry=log_entry
            )
    
    except Exception as e:
        print(f"Failed to check/update error patterns: {e}")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log user login events
    """
    try:
        user_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        log_system_event(
            log_type='INFO',
            severity='INFO',
            error_message=f'User {user.username} logged in successfully',
            error_type='USER_LOGIN',
            module='authentication',
            function='user_logged_in',
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            request_method=request.method,
            request_url=request.build_absolute_uri(),
            request_data={
                'session_id': request.session.session_key,
                'login_time': timezone.now().isoformat()
            },
            tags=['authentication', 'login', 'success'],
            environment=getattr(request, 'environment', 'production')
        )
    
    except Exception as e:
        print(f"Failed to log user login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout events
    """
    try:
        user_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        log_system_event(
            log_type='INFO',
            severity='INFO',
            error_message=f'User {user.username} logged out',
            error_type='USER_LOGOUT',
            module='authentication',
            function='user_logged_out',
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            request_method=request.method,
            request_url=request.build_absolute_uri(),
            request_data={
                'session_id': request.session.session_key if hasattr(request, 'session') else None,
                'logout_time': timezone.now().isoformat()
            },
            tags=['authentication', 'logout'],
            environment=getattr(request, 'environment', 'production')
        )
    
    except Exception as e:
        print(f"Failed to log user logout: {e}")


def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Exception logging middleware signal
def log_exception(request, exception, exc_info=None):
    """
    Log exceptions that occur during request processing
    """
    try:
        user = getattr(request, 'user', None)
        user_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Get exception details
        exc_type, exc_value, exc_traceback = exc_info or sys.exc_info()
        error_type = exc_type.__name__ if exc_type else 'UnknownException'
        error_message = str(exc_value) if exc_value else 'Unknown error'
        
        # Get stack trace
        if exc_traceback:
            stack_trace = ''.join(traceback.format_tb(exc_traceback))
        else:
            stack_trace = ''
        
        # Determine severity based on exception type
        severity = 'ERROR'
        if 'ValidationError' in error_type:
            severity = 'WARNING'
        elif 'PermissionDenied' in error_type:
            severity = 'WARNING'
        elif 'Http404' in error_type:
            severity = 'INFO'
        elif 'DatabaseError' in error_type:
            severity = 'CRITICAL'
        elif 'TimeoutError' in error_type:
            severity = 'CRITICAL'
        
        # Get module and function information
        if exc_traceback:
            frame = exc_traceback.tb_frame
            module = frame.f_globals.get('__name__', 'unknown')
            function = frame.f_code.co_name
            line_number = frame.f_lineno
            file_path = frame.f_code.co_filename
        else:
            module = 'unknown'
            function = 'unknown'
            line_number = None
            file_path = ''
        
        # Log the exception
        log_system_event(
            log_type='EXCEPTION',
            severity=severity,
            error_message=error_message,
            error_type=error_type,
            module=module,
            function=function,
            line_number=line_number,
            file_path=file_path,
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            request_method=request.method,
            request_url=request.build_absolute_uri(),
            request_data={
                'path': request.path,
                'method': request.method,
                'get_params': dict(request.GET),
                'post_params': dict(request.POST) if request.method == 'POST' else {},
                'headers': dict(request.headers),
                'cookies': dict(request.COOKIES)
            },
            tags=['exception', 'request_error', error_type.lower()],
            environment=getattr(request, 'environment', 'production'),
            stack_trace=stack_trace,
            exception_details={
                'exception_type': error_type,
                'exception_message': error_message,
                'traceback': stack_trace
            }
        )
    
    except Exception as e:
        # Fallback logging to prevent infinite loops
        print(f"Failed to log exception: {e}")


# Performance monitoring signal
def log_performance_metric(
    module='',
    function='',
    execution_time=0,
    memory_usage='',
    cpu_usage=None,
    user=None,
    request=None,
    tags=None,
    context_data=None
):
    """
    Log performance metrics for functions and operations
    """
    try:
        # Determine severity based on execution time
        severity = 'INFO'
        if execution_time > 10:  # More than 10 seconds
            severity = 'CRITICAL'
        elif execution_time > 5:  # More than 5 seconds
            severity = 'HIGH'
        elif execution_time > 1:  # More than 1 second
            severity = 'WARNING'
        
        # Get request context if available
        user_ip = None
        user_agent = ''
        request_method = ''
        request_url = ''
        
        if request:
            user_ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            request_method = request.method
            request_url = request.build_absolute_uri()
        
        log_system_event(
            log_type='PERFORMANCE',
            severity=severity,
            error_message=f'Performance metric: {function} took {execution_time:.3f}s',
            error_type='PERFORMANCE_METRIC',
            module=module,
            function=function,
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            tags=tags or ['performance', 'monitoring'],
            context_data=context_data or {},
            environment=getattr(request, 'environment', 'production') if request else 'production'
        )
    
    except Exception as e:
        print(f"Failed to log performance metric: {e}")


# Security event logging
def log_security_event(
    event_type='',
    description='',
    severity='INFO',
    user=None,
    request=None,
    affected_object=None,
    security_details=None,
    tags=None
):
    """
    Log security-related events
    """
    try:
        # Get request context if available
        user_ip = None
        user_agent = ''
        request_method = ''
        request_url = ''
        
        if request:
            user_ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            request_method = request.method
            request_url = request.build_absolute_uri()
        
        # Get object information if available
        content_type = None
        object_id = None
        object_name = ''
        
        if affected_object:
            content_type = ContentType.objects.get_for_model(affected_object)
            object_id = affected_object.pk
            object_name = str(affected_object)
        
        log_system_event(
            log_type='SECURITY',
            severity=severity,
            error_message=description,
            error_type=event_type,
            module='security',
            function='security_event',
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            content_type=content_type,
            object_id=object_id,
            object_name=object_name,
            tags=tags or ['security', event_type.lower()],
            context_data=security_details or {},
            environment=getattr(request, 'environment', 'production') if request else 'production'
        )
    
    except Exception as e:
        print(f"Failed to log security event: {e}")


# Database operation logging - Temporarily disabled to allow migrations to complete
# @receiver(post_save)
# def log_model_changes(sender, instance, created, **kwargs):
#     """
#     Log model save operations
#     """
#     try:
#         # Skip logging for certain models
#         if sender._meta.app_label in ['admin', 'sessions', 'contenttypes']:
#             return
#         
#         # Skip logging for SystemLog to prevent infinite loops
#         if sender == SystemLog:
#             return
#         
#         # Determine action type
#         action_type = 'CREATE' if created else 'UPDATE'
#         
#         # Get user from request if available
#         user = None
#         try:
#             from django.contrib.auth.models import AnonymousUser
#             from django.contrib.auth import get_user
#             request = getattr(instance, '_request', None)
#             if request and hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
#                 user = request.user
#         except:
#             pass
#         
#         # Get changed fields for updates
#         changed_fields = []
#         if not created and hasattr(instance, '_state') and hasattr(instance._state, 'fields_cache'):
#             for field_name in instance._state.fields_cache:
#                 if field_name in instance._state.fields_cache:
#                     changed_fields.append(field_name)
#         
#         # Log the operation
#         log_system_event(
#             log_type='AUDIT',
#             severity='INFO',
#             error_message=f'{action_type} operation on {sender._meta.verbose_name}',
#             error_type=f'MODEL_{action_type}',
#             module=sender._meta.app_label,
#             function=sender._meta.model_name,
#             user=user,
#             content_type=ContentType.objects.get_for_model(sender),
#             object_id=instance.pk,
#             object_name=str(instance),
#             tags=['audit', 'model_operation', action_type.lower(), sender._meta.model_name],
#             context_data={
#                 'model_name': sender._meta.model_name,
#                 'app_label': sender._meta.app_label,
#                 'action': action_type,
#                 'changed_fields': changed_fields,
#                 'instance_id': instance.pk
#             }
#         )
#     
#     except Exception as e:
#         print(f"Failed to log model changes: {e}")


# @receiver(post_delete)
# def log_model_deletions(sender, instance, **kwargs):
#     """
#     Log model deletion operations
#     """
#     try:
#         # Skip logging for certain models
#         if sender._meta.app_label in ['admin', 'sessions', 'contenttypes']:
#             return
#         
#         # Skip logging for SystemLog to prevent infinite loops
#         if sender == SystemLog:
#             return
#         
#         # Get user from request if available
#         user = None
#         try:
#             from django.contrib.auth.models import AnonymousUser
#             request = getattr(instance, '_request', None)
#             if request and hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
#                 user = request.user
#         except:
#             pass
#         
#         # Log the deletion
#         log_system_event(
#             log_type='AUDIT',
#             severity='WARNING',
#             error_message=f'DELETE operation on {sender._meta.verbose_name}',
#             error_type='MODEL_DELETE',
#             module=sender._meta.app_label,
#             function=sender._meta.model_name,
#             user=user,
#             content_type=ContentType.objects.get_for_model(sender),
#             object_id=instance.pk,
#             object_name=str(instance),
#             tags=['audit', 'model_operation', 'delete', sender._meta.model_name],
#             context_data={
#                 'model_name': sender._meta.model_name,
#                 'app_label': sender._meta.app_label,
#                 'action': 'DELETE',
#                 'instance_id': instance.pk,
#                 'deleted_at': timezone.now().isoformat()
#             }
#         )
#     
#     except Exception as e:
#         print(f"Failed to log model deletion: {e}")


# Custom action logging decorator
def log_action(action_type, description='', severity='INFO', tags=None, context_data=None):
    """
    Decorator to log custom actions
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = timezone.now()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time = (timezone.now() - start_time).total_seconds()
                
                # Get user from request if available
                user = None
                request = None
                for arg in args:
                    if hasattr(arg, 'user') and hasattr(arg.user, 'is_authenticated'):
                        request = arg
                        user = arg.user if arg.user.is_authenticated else None
                        break
                
                # Log successful action
                log_system_event(
                    log_type='INFO',
                    severity=severity,
                    error_message=description,
                    error_type=action_type,
                    module=func.__module__,
                    function=func.__name__,
                    user=user,
                    request_method=getattr(request, 'method', '') if request else '',
                    request_url=getattr(request, 'build_absolute_uri', lambda: '')() if request else '',
                    execution_time=execution_time,
                    tags=tags or ['custom_action', action_type.lower()],
                    context_data=context_data or {}
                )
                
                return result
            
            except Exception as e:
                # Calculate execution time
                execution_time = (timezone.now() - start_time).total_seconds()
                
                # Get user from request if available
                user = None
                request = None
                for arg in args:
                    if hasattr(arg, 'user') and hasattr(arg.user, 'is_authenticated'):
                        request = arg
                        user = arg.user if arg.user.is_authenticated else None
                        break
                
                # Log failed action
                log_system_event(
                    log_type='EXCEPTION',
                    severity='ERROR',
                    error_message=f'{description} failed: {str(e)}',
                    error_type=f'{action_type}_FAILED',
                    module=func.__module__,
                    function=func.__name__,
                    user=user,
                    request_method=getattr(request, 'method', '') if request else '',
                    request_url=getattr(request, 'build_absolute_uri', lambda: '')() if request else '',
                    execution_time=execution_time,
                    tags=tags or ['custom_action', action_type.lower(), 'failed'],
                    context_data=context_data or {},
                    stack_trace=traceback.format_exc(),
                    exception_details={'exception': str(e), 'type': type(e).__name__}
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator
