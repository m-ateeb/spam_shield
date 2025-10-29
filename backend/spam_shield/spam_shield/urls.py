from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from email_connector import views

@api_view(['GET'])
def test_auth(request):
    return Response({"message": "Authenticated", "user_id": request.user.id})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oauth/google/', views.google_login),
    path('oauth/google/callback/', views.google_callback),
    path('gmail/fetch/', views.fetch_recent_gmail),
    path('oauth/microsoft/', views.microsoft_login),
    path('oauth/microsoft/callback/', views.microsoft_callback),
    path('webhook/gmail/', views.gmail_webhook),
    path('webhook/outlook/', views.outlook_webhook),
]