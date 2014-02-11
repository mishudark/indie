from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from indie.forms import UploadForm
from django.http import HttpResponse, Http404

import json

@login_required
def upload(request):
    if not request.method == 'POST':
        raise Http404

    form = UploadForm(data=request.POST)
    if not form.is_valid():
        data = {'error': True, 'msg': 'invalid data'}
    else:
        form.save()
        data = {'error': False, 'msg': 'saved'}

    return HttpResponse(json.dumps(data), mimetype='application/json')

