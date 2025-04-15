from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .trie import compare_first_level, compare_second_level

# Create your views here.

def groups_view(request):
    return render(request, 'optionsexample/groups.html')

def options_view(request, group_name):
    return render(request, 'optionsexample/options.html', {'group_name': group_name})

def relations_view(request):
    return render(request, 'optionsexample/relations.html')

@csrf_exempt
@require_http_methods(["POST"])
def compare_first_level_view(request):
    """
    Compare first level of client trie with server trie.
    Expects POST data in format:
    {
        "01": {"hash": "abc", "count": 5},
        "02": {"hash": "def", "count": 3}
    }
    """
    try:
        client_trie = json.loads(request.body)
        # TODO: Get server trie from database/cache
        server_trie = {}  # Placeholder
        
        result = compare_first_level(client_trie, server_trie)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def compare_second_level_view(request, prefix):
    """
    Compare second level of client subtree with server subtree.
    URL pattern: /sync/level2/<prefix>
    Expects POST data in format:
    {
        "01/H9": {"hash": "abc", "count": 3},
        "01/H8": {"hash": "def", "count": 2}
    }
    """
    try:
        client_subtree = json.loads(request.body)
        # TODO: Get server subtree from database/cache
        server_subtree = {}  # Placeholder
        
        result = compare_second_level(client_subtree, server_subtree)
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
