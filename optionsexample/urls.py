from django.urls import path
from . import views



urlpatterns = [
    path('groups/', views.groups_view, name='groups'),
    path('groups/<str:group_name>/', views.options_view, name='options'),
    path('relations/', views.relations_view, name='relations'),
    path('options/<str:group_name>/<str:value>/', views.ExampleOptionDetailView.as_view(), name='option_detail'),
]