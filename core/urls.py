# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core import signing
import os


@login_required
def redirect_to_streamlit(request):
    """
    After Google OAuth completes, redirect to Streamlit with a signed token
    instead of raw email/name in the URL — prevents URL spoofing.
    Token expires in 5 minutes (enforced in /api/resolve-token).
    """
    token = signing.dumps(
        {"name": request.user.first_name or request.user.username, "email": request.user.email},
        salt='streamlit-login',
    )
    streamlit_url = os.getenv('STREAMLIT_URL', 'http://localhost:8501')
    return redirect(f"{streamlit_url}/?token={token}")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('streamlit-login/', redirect_to_streamlit, name='streamlit_login'),
]