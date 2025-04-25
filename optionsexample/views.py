from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from sync_option.views import OptionDetailView


# Create your views here.

def groups_view(request):
    return render(request, 'optionsexample/groups.html')

def options_view(request, group_name):
    return render(request, 'optionsexample/options.html', {'group_name': group_name})

def relations_view(request):
    return render(request, 'optionsexample/relations.html')

class ExampleOptionDetailView(OptionDetailView):
    template_name = 'optionsexample/option_detail.html'
    
    def get_object(self, queryset=None):
        """Get the option using group_name and value instead of pk"""
        group_name = self.kwargs.get('group_name')
        value = self.kwargs.get('value')
        return self.get_queryset().get(group__name=group_name, value=value)
