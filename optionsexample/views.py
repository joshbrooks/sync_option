from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


# Create your views here.

def groups_view(request):
    return render(request, 'optionsexample/groups.html')

def options_view(request, group_name):
    return render(request, 'optionsexample/options.html', {'group_name': group_name})

def relations_view(request):
    return render(request, 'optionsexample/relations.html')
