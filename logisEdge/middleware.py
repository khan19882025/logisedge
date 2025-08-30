from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class SessionExpirationMiddleware:
    """
    Middleware to handle session expiration and ensure users are logged out
    when the browser is closed.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and session is expired
        if request.user.is_authenticated:
            # Check if session has expired
            if not request.session.get('_auth_user_id'):
                # Session has expired, log out the user
                logout(request)
                messages.warning(request, 'Your session has expired. Please log in again.')
                return redirect('login')
        
        response = self.get_response(request)
        return response 