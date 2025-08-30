from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponse
from company.company_model import Company

# Create your views here.

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the first active company
        company = Company.objects.filter(is_active=True).first()
        context['company_name'] = company.name if company else 'logisEdge'
        return context
    
    def form_valid(self, form):
        """Override form_valid to set session expiration"""
        response = super().form_valid(form)
        # Ensure session is saved
        self.request.session.save()
        return response

@login_required
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')
