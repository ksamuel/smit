
from django.shortcuts import render

from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    groups = [g.name for g in request.user.groups.all()]
    translations = {'operator': 'Opérateur', 'helicopter_pilot': 'Pilote'}
    groups = {g: translations[g] for g in groups}
    ctx = {'groups': groups}
    return render(request, 'dashboard.html', ctx)
