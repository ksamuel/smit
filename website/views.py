

from django.views.generic import CreateView
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required

from .models import Settings
from .forms import SettingsForm


@login_required
def dashboard(request):

    if not Settings.objects.filter(active=True).exists():
        return redirect('new_settings')

    groups = [g.name for g in request.user.groups.all()]
    translations = {'operator': 'Opérateur', 'helicopter_pilot': 'Pilote'}
    groups = {g: translations[g] for g in groups}
    ctx = {'groups': groups}
    return render(request, 'dashboard.html', ctx)


class SettingsCreateView(CreateView):
    form_class = SettingsForm
    template_name = 'first_settings.html'
    success_url = 'dashboard'


@login_required
def new_settings(request, form_view=SettingsCreateView.as_view()):
    if Settings.objects.filter(active=True).exists():
        return redirect('dashboard')
    return form_view(request)
