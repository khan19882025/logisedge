from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import floatformat
from ..models import ResignationRequest, ClearanceProcess, GratuityCalculation
from django.db import models

register = template.Library()


@register.filter
def status_badge(status):
    """Return Bootstrap badge for status"""
    status_classes = {
        'pending': 'bg-warning',
        'manager_review': 'bg-info',
        'hr_approval': 'bg-primary',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
        'exit_processing': 'bg-secondary',
        'completed': 'bg-dark',
        'cancelled': 'bg-danger',
    }
    
    class_name = status_classes.get(status, 'bg-secondary')
    return mark_safe(f'<span class="badge {class_name}">{status.replace("_", " ").title()}</span>')


@register.filter
def clearance_status_badge(status):
    """Return Bootstrap badge for clearance status"""
    status_classes = {
        'pending': 'bg-warning',
        'cleared': 'bg-success',
        'not_applicable': 'bg-secondary',
        'waived': 'bg-info',
    }
    
    class_name = status_classes.get(status, 'bg-secondary')
    return mark_safe(f'<span class="badge {class_name}">{status.replace("_", " ").title()}</span>')


@register.filter
def format_currency(amount):
    """Format amount as UAE currency"""
    if amount is None:
        return "AED 0.00"
    return f"AED {floatformat(amount, 2)}"


@register.filter
def progress_percentage(clearance_process):
    """Calculate completion percentage for clearance process"""
    if not clearance_process:
        return 0
    
    total_items = clearance_process.clearance_items.count()
    if total_items == 0:
        return 0
    
    completed_items = clearance_process.clearance_items.filter(status='cleared').count()
    return round((completed_items / total_items) * 100, 1)


@register.filter
def notice_period_remaining(resignation):
    """Calculate remaining notice period days"""
    if not resignation:
        return 0
    return max(0, resignation.notice_period_days - resignation.notice_period_served)


@register.filter
def is_notice_period_complete(resignation):
    """Check if notice period is complete"""
    if not resignation:
        return False
    return resignation.notice_period_served >= resignation.notice_period_days


@register.filter
def gratuity_breakdown(gratuity_calculation):
    """Return formatted gratuity breakdown"""
    if not gratuity_calculation:
        return ""
    
    breakdown = f"""
    <div class="gratuity-breakdown">
        <div class="row">
            <div class="col-md-6">
                <strong>First 5 Years:</strong> {gratuity_calculation.first_five_years} years<br>
                <strong>After 5 Years:</strong> {gratuity_calculation.after_five_years} years
            </div>
            <div class="col-md-6">
                <strong>Daily Rate (21 days):</strong> AED {floatformat(gratuity_calculation.daily_rate_21_days, 2)}<br>
                <strong>Daily Rate (30 days):</strong> AED {floatformat(gratuity_calculation.daily_rate_30_days, 2)}
            </div>
        </div>
        <hr>
        <div class="row">
            <div class="col-md-6">
                <strong>Gratuity (First 5):</strong> AED {floatformat(gratuity_calculation.gratuity_first_five, 2)}<br>
                <strong>Gratuity (After 5):</strong> AED {floatformat(gratuity_calculation.gratuity_after_five, 2)}
            </div>
            <div class="col-md-6">
                <strong>Total Gratuity:</strong> AED {floatformat(gratuity_calculation.total_gratuity, 2)}<br>
                <strong>Final Gratuity:</strong> AED {floatformat(gratuity_calculation.final_gratuity, 2)}
            </div>
        </div>
    </div>
    """
    
    return mark_safe(breakdown)


@register.filter
def settlement_breakdown(settlement):
    """Return formatted settlement breakdown"""
    if not settlement:
        return ""
    
    breakdown = f"""
    <div class="settlement-breakdown">
        <div class="row">
            <div class="col-md-6">
                <strong>Last Month Salary:</strong> AED {floatformat(settlement.last_month_salary, 2)}<br>
                <strong>Leave Encashment:</strong> AED {floatformat(settlement.leave_encashment, 2)}<br>
                <strong>Gratuity Amount:</strong> AED {floatformat(settlement.gratuity_amount, 2)}
            </div>
            <div class="col-md-6">
                <strong>Loan Deductions:</strong> AED {floatformat(settlement.loan_deductions, 2)}<br>
                <strong>Notice Period Deduction:</strong> AED {floatformat(settlement.notice_period_deduction, 2)}<br>
                <strong>Other Deductions:</strong> AED {floatformat(settlement.other_deductions, 2)}
            </div>
        </div>
        <hr>
        <div class="row">
            <div class="col-md-6">
                <strong>Gross Settlement:</strong> AED {floatformat(settlement.gross_settlement, 2)}
            </div>
            <div class="col-md-6">
                <strong>Net Settlement:</strong> AED {floatformat(settlement.net_settlement, 2)}
            </div>
        </div>
    </div>
    """
    
    return mark_safe(breakdown)


@register.simple_tag
def get_dashboard_stats():
    """Get dashboard statistics"""
    stats = {
        'total_resignations': ResignationRequest.objects.count(),
        'pending_resignations': ResignationRequest.objects.filter(status='pending').count(),
        'active_clearances': ClearanceProcess.objects.filter(is_completed=False).count(),
        'total_gratuity': GratuityCalculation.objects.aggregate(
            total=models.Sum('final_gratuity')
        )['total'] or 0,
    }
    return stats


@register.filter
def time_ago(timestamp):
    """Return human-readable time ago"""
    from django.utils import timezone
    from datetime import timedelta
    
    if not timestamp:
        return "Unknown"
    
    now = timezone.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


@register.filter
def workflow_step_status(resignation, step):
    """Return status for workflow step"""
    workflow_steps = {
        'resignation_submitted': 'completed',
        'manager_review': 'pending',
        'hr_approval': 'pending',
        'clearance_process': 'pending',
        'gratuity_calculation': 'pending',
        'final_settlement': 'pending',
        'exit_completed': 'pending',
    }
    
    if step == 'resignation_submitted':
        return 'completed'
    elif step == 'manager_review':
        if resignation.status in ['manager_review', 'hr_approval', 'approved', 'exit_processing', 'completed']:
            return 'completed'
        elif resignation.status == 'pending':
            return 'current'
        else:
            return 'pending'
    elif step == 'hr_approval':
        if resignation.status in ['hr_approval', 'approved', 'exit_processing', 'completed']:
            return 'completed'
        elif resignation.status == 'manager_review':
            return 'current'
        else:
            return 'pending'
    elif step == 'clearance_process':
        if hasattr(resignation, 'clearance_process'):
            if resignation.clearance_process.is_completed:
                return 'completed'
            else:
                return 'current'
        else:
            return 'pending'
    elif step == 'gratuity_calculation':
        if hasattr(resignation, 'gratuity_calculation'):
            return 'completed'
        else:
            return 'pending'
    elif step == 'final_settlement':
        if hasattr(resignation, 'final_settlement'):
            return 'completed'
        else:
            return 'pending'
    elif step == 'exit_completed':
        if resignation.status == 'completed':
            return 'completed'
        else:
            return 'pending'
    
    return 'pending' 