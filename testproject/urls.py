"""
URL configuration for testproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from sync_option.api import router as sync_option_router

# Create the main API instance
api = NinjaAPI()

# Include the sync_option router under the /api prefix
api.add_router("/sync-option", sync_option_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),  # Django Ninja API endpoints
]
