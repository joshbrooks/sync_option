from django.shortcuts import render

# Create your views here.

def groups_view(request):
    return render(request, 'optionsexample/groups.html')
