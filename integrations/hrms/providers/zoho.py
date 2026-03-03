import json
from datetime import datetime, timedelta, timezone

import requests

from integrations.hrms.base import BaseHRMSConnector


class ZohoConnector(BaseHRMSConnector):
    AUTH_URL = "https://accounts.zoho.in/oauth/v2/auth"
    TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"
    EMPLOYEE_URL = "https://people.zoho.in/people/api/forms/employee/getRecords"

    def get_authorization_url(self, state):
        return (
            f"{self.AUTH_URL}?"
            f"scope=ZohoPeople.forms.ALL"
            f"&client_id={self.settings.ZOHO_CLIENT_ID}"
            f"&response_type=code"
            f"&access_type=offline"
            f"&prompt=consent"
            f"&redirect_uri={self.settings.ZOHO_REDIRECT_URI}"
            f"&state={state}"
        )

    def exchange_code_for_token(self, code):
        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": self.settings.ZOHO_CLIENT_ID,
                "client_secret": self.settings.ZOHO_CLIENT_SECRET,
                "redirect_uri": self.settings.ZOHO_REDIRECT_URI,
                "code": code,
            },
            timeout=10,
        )

        data = response.json()

        if "access_token" not in data:
            raise Exception(f"Zoho token exchange failed: {data}")

        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "expires_in": data.get("expires_in", 3600),
        }

    def _is_token_expired(self):
        token_expiry = self.connection.token_expiry
        if token_expiry.tzinfo is None:
            token_expiry = token_expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= token_expiry

    def refresh_access_token(self):
        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.connection.refresh_token,
                "client_id": self.settings.ZOHO_CLIENT_ID,
                "client_secret": self.settings.ZOHO_CLIENT_SECRET,
            },
            timeout=10,
        )

        data = response.json()

        if "access_token" not in data:
            raise Exception(f"Zoho refresh failed: {data}")

        self.connection.access_token = data["access_token"]
        self.connection.token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=int(data.get("expires_in", 3600))
        )
        self.db.add(self.connection)
        self.db.commit()

    def _get_valid_access_token(self):
        if self._is_token_expired():
            self.refresh_access_token()
        return self.connection.access_token

    def fetch_employees(self, updated_after=None, status=None):
        access_token = self._get_valid_access_token()

        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
        }

        params = {}

        if status:
            search_payload = {
                "searchField": "Employeestatus",
                "searchOperator": "Is",
                "searchText": status,
            }
            params["searchParams"] = json.dumps(search_payload)

        response = requests.get(
            self.EMPLOYEE_URL,
            headers=headers,
            params=params,
            timeout=10,
        )

        if response.status_code != 200:
            raise Exception(f"Zoho API error: {response.text}")

        return response.json()
