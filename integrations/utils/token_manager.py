import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def refresh_zoho_token(integration):

    if integration.expires_at > timezone.now():
        return integration.access_token

    token_url = "https://accounts.zoho.com/oauth/v2/token"

    payload = {
        "grant_type": "refresh_token",
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "refresh_token": integration.refresh_token,
    }

    response = requests.post(token_url, data=payload)
    data = response.json()

    integration.access_token = data["access_token"]
    integration.expires_at = timezone.now() + timedelta(seconds=data["expires_in"])
    integration.save()

    return integration.access_token