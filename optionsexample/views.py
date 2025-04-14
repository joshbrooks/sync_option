from django.shortcuts import render

# Create your views here.

def groups_view(request):
    return render(request, 'optionsexample/groups.html')

def options_view(request, group_name):
    return render(request, 'optionsexample/options.html', {'group_name': group_name})
