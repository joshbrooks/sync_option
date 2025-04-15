from django.urls import path
from . import views

urlpatterns = [
    path('groups/', views.groups_view, name='groups'),
    path('groups/<str:group_name>/', views.options_view, name='options'),
    path('relations/', views.relations_view, name='relations'),
    path('sync/level1/', views.compare_first_level_view, name='compare_first_level'),
    path('sync/level2/<str:prefix>/', views.compare_second_level_view, name='compare_second_level'),
] 