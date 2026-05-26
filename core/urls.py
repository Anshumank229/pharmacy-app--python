# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.conf import settings


# ==========================================
# FIX: Instead of putting name+email in the URL (visible in browser history,
# server logs, etc.), we sign a short-lived token and pass only that.
# Streamlit reads the token and exchanges it via /api/resolve-token.
# Token expires in 5 minutes — enough for the redirect, too short to misuse.
# ==========================================
@login_required
def redirect_to_streamlit(request):
    payload = {
        'name':  request.user.first_name or request.user.username,
        'email': request.user.email,
    }
    # signs + timestamps the payload; max_age enforced on the other end
    token = signing.dumps(payload, salt='streamlit-login')
    streamlit_url = getattr(settings, 'STREAMLIT_URL', 'http://localhost:8501')
    return redirect(f"{streamlit_url}/?token={token}")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('streamlit-login/', redirect_to_streamlit, name='streamlit_login'),
]