import requests
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class ZohoService:

    def __init__(self, integration):
        self.integration = integration

    def _is_token_expired(self):
        return timezone.now() >= self.integration.expires_at

    def _refresh_access_token(self):

        token_url = "https://accounts.zoho.in/oauth/v2/token"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.integration.refresh_token,
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
        }

        response = requests.post(token_url, data=payload)
        data = response.json()

        if "access_token" not in data:
            raise Exception("Failed to refresh token")

        self.integration.access_token = data["access_token"]
        self.integration.expires_at = (
            timezone.now() + timedelta(seconds=int(data.get("expires_in", 3600)))
        )
        self.integration.save()

    def _get_valid_access_token(self):

        if self._is_token_expired():
            self._refresh_access_token()

        return self.integration.access_token

    def get_employees(self):

        access_token = self._get_valid_access_token()

        url = "https://people.zoho.in/people/api/forms/employee/getRecords"

        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }

        response = requests.get(url, headers=headers)

        return response.json()