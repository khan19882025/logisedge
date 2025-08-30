from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Q
import json

from .models import RFUser, ScanSession, ScanRecord, Location, Item
from .forms import RFLoginForm, ScanForm, SessionForm


def rf_login(request):
    """RF Scanner Login View"""
    if request.user.is_authenticated:
        return redirect('rf_scanner:dashboard')
    
    if request.method == 'POST':
        form = RFLoginForm(request, data=request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            password = form.cleaned_data.get('password')
            employee_id = form.cleaned_data.get('employee_id')
            
            # Try to authenticate using the name as username
            user = authenticate(username=name, password=password)
            if user is not None:
                # Check if user has RF profile with matching employee_id
                try:
                    rf_user = RFUser.objects.get(user=user, employee_id=employee_id, is_active=True)
                    login(request, user)
                    messages.success(request, f'Welcome, {name}!')
                    return redirect('rf_scanner:dashboard')
                except RFUser.DoesNotExist:
                    messages.error(request, 'Invalid Employee ID or user not authorized for RF Scanner.')
            else:
                messages.error(request, 'Invalid name or password.')
    else:
        form = RFLoginForm()
    
    return render(request, 'rf_scanner/login.html', {'form': form})


@login_required
def rf_logout(request):
    """RF Scanner Logout View"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('rf_scanner:login')


@login_required
def dashboard(request):
    """RF Scanner Dashboard"""
    try:
        rf_user = request.user.rf_profile
    except RFUser.DoesNotExist:
        messages.error(request, 'You are not authorized to use the RF Scanner.')
        return redirect('rf_scanner:login')
    
    # Get active session if any
    active_session = ScanSession.objects.filter(user=rf_user, is_active=True).first()
    
    # Get recent scans
    recent_scans = ScanRecord.objects.filter(session__user=rf_user).order_by('-scan_time')[:10]
    
    # Get session statistics
    today_sessions = ScanSession.objects.filter(
        user=rf_user,
        start_time__date=timezone.now().date()
    )
    
    session_stats = {
        'inbound': today_sessions.filter(session_type='inbound').count(),
        'outbound': today_sessions.filter(session_type='outbound').count(),
        'location_change': today_sessions.filter(session_type='location_change').count(),
        'physical_check': today_sessions.filter(session_type='physical_check').count(),
    }
    
    context = {
        'rf_user': rf_user,
        'active_session': active_session,
        'recent_scans': recent_scans,
        'session_stats': session_stats,
        'today': timezone.now(),
    }
    
    return render(request, 'rf_scanner/dashboard.html', context)


@login_required
def start_session(request):
    """Start a new scanning session"""
    try:
        rf_user = request.user.rf_profile
    except RFUser.DoesNotExist:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            # End any existing active session
            ScanSession.objects.filter(user=rf_user, is_active=True).update(
                is_active=False,
                end_time=timezone.now()
            )
            
            # Create new session
            session = form.save(commit=False)
            session.user = rf_user
            session.save()
            
            messages.success(request, f'Started {session.get_session_type_display()} session.')
            return redirect('rf_scanner:scan', session_id=session.id)
    else:
        form = SessionForm()
    
    return render(request, 'rf_scanner/start_session.html', {'form': form})


@login_required
def end_session(request, session_id):
    """End a scanning session"""
    session = get_object_or_404(ScanSession, id=session_id, user=request.user.rf_profile)
    
    if session.is_active:
        session.is_active = False
        session.end_time = timezone.now()
        session.save()
        messages.success(request, f'Ended {session.get_session_type_display()} session.')
    
    return redirect('rf_scanner:dashboard')


@login_required
def scan(request, session_id):
    """Scanning interface"""
    session = get_object_or_404(ScanSession, id=session_id, user=request.user.rf_profile)
    
    if not session.is_active:
        messages.error(request, 'This session has ended.')
        return redirect('rf_scanner:dashboard')
    
    if request.method == 'POST':
        form = ScanForm(request.POST)
        if form.is_valid():
            scan_record = form.save(commit=False)
            scan_record.session = session
            
            # Try to get item details from barcode
            try:
                item = Item.objects.get(barcode=scan_record.barcode, is_active=True)
                scan_record.item_code = item.item_code
                scan_record.item_name = item.item_name
            except Item.DoesNotExist:
                pass
            
            scan_record.save()
            
            messages.success(request, f'Scanned: {scan_record.barcode}')
            form = ScanForm()  # Reset form for next scan
    else:
        form = ScanForm()
    
    # Get recent scans for this session
    recent_scans = ScanRecord.objects.filter(session=session).order_by('-scan_time')[:20]
    
    context = {
        'session': session,
        'form': form,
        'recent_scans': recent_scans,
    }
    
    return render(request, 'rf_scanner/scan.html', context)


@csrf_exempt
@login_required
def api_scan(request):
    """API endpoint for scanning (for mobile apps)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            barcode = data.get('barcode')
            session_id = data.get('session_id')
            quantity = data.get('quantity', 1)
            location = data.get('location', '')
            
            session = get_object_or_404(ScanSession, id=session_id, user=request.user.rf_profile)
            
            if not session.is_active:
                return JsonResponse({'error': 'Session ended'}, status=400)
            
            scan_record = ScanRecord.objects.create(
                session=session,
                barcode=barcode,
                quantity=quantity,
                location=location
            )
            
            # Try to get item details
            try:
                item = Item.objects.get(barcode=barcode, is_active=True)
                scan_record.item_code = item.item_code
                scan_record.item_name = item.item_name
                scan_record.save()
            except Item.DoesNotExist:
                pass
            
            return JsonResponse({
                'success': True,
                'scan_id': scan_record.id,
                'barcode': scan_record.barcode,
                'item_name': scan_record.item_name or 'Unknown Item',
                'scan_time': scan_record.scan_time.isoformat()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def session_history(request):
    """View session history"""
    try:
        rf_user = request.user.rf_profile
    except RFUser.DoesNotExist:
        return redirect('rf_scanner:login')
    
    sessions = ScanSession.objects.filter(user=rf_user).order_by('-start_time')
    
    return render(request, 'rf_scanner/session_history.html', {'sessions': sessions})


@login_required
def session_detail(request, session_id):
    """View session details and scans"""
    session = get_object_or_404(ScanSession, id=session_id, user=request.user.rf_profile)
    scans = ScanRecord.objects.filter(session=session).order_by('-scan_time')
    
    return render(request, 'rf_scanner/session_detail.html', {
        'session': session,
        'scans': scans
    })


@login_required
def search_items(request):
    """Search items by barcode or name"""
    query = request.GET.get('q', '')
    items = []
    
    if query:
        items = Item.objects.filter(
            Q(barcode__icontains=query) | 
            Q(item_name__icontains=query) |
            Q(item_code__icontains=query),
            is_active=True
        )[:10]
    
    return render(request, 'rf_scanner/search_items.html', {
        'items': items,
        'query': query
    })
