# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def redirect_to_streamlit(request):
    name  = request.user.first_name or request.user.username
    email = request.user.email
    return redirect(f"http://localhost:8501/?name={name}&email={email}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('streamlit-login/', redirect_to_streamlit, name='streamlit_login'),
]