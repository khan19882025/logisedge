from django.shortcuts import render, get_object_or_404, redirect
from .models import Port
from .forms import PortForm
from django.contrib import messages

# Create your views here.

def port_list(request):
    ports = Port.objects.all()
    return render(request, 'port/port_list.html', {'ports': ports})

def port_create(request):
    if request.method == 'POST':
        form = PortForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Port created successfully!')
            return redirect('port:port_list')
    else:
        form = PortForm()
    return render(request, 'port/port_form.html', {'form': form})

def port_edit(request, pk):
    port = get_object_or_404(Port, pk=pk)
    if request.method == 'POST':
        form = PortForm(request.POST, instance=port)
        if form.is_valid():
            form.save()
            messages.success(request, 'Port updated successfully!')
            return redirect('port:port_list')
    else:
        form = PortForm(instance=port)
    return render(request, 'port/port_form.html', {'form': form, 'port': port})

def port_detail(request, pk):
    port = get_object_or_404(Port, pk=pk)
    return render(request, 'port/port_detail.html', {'port': port})

def port_delete(request, pk):
    port = get_object_or_404(Port, pk=pk)
    if request.method == 'POST':
        port.delete()
        messages.success(request, 'Port deleted successfully!')
        return redirect('port:port_list')
    return render(request, 'port/port_confirm_delete.html', {'port': port})
