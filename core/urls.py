"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# 1. Create the bridge function
@login_required
def redirect_to_streamlit(request):
    name = request.user.first_name or request.user.username
    email = request.user.email
    # Send the user to Streamlit, and attach their name and email to the URL!
    return redirect(f"http://localhost:8501/?name={name}&email={email}")

# 2. Add it to your routes
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('streamlit-login/', redirect_to_streamlit, name='streamlit_login'), # New route
]