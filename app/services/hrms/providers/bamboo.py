from datetime import datetime

import requests

from app.services.hrms.base import BaseHRMSConnector


class BambooConnector(BaseHRMSConnector):
    def get_authorization_url(self, state):
        # Bamboo integration is API-key based and does not require OAuth redirects.
        return ""

    def exchange_code_for_token(self, code):
        raise Exception("Bamboo does not use OAuth token exchange")

    def fetch_employees(self, updated_after=None, status=None):
        api_key = self.connection.access_token
        subdomain = self.connection.refresh_token

        if not api_key or not subdomain:
            raise Exception("Bamboo connection is missing api_key or subdomain")

        url = f"https://api.bamboohr.com/api/gateway.php/{subdomain}/v1/employees/directory"

        response = requests.get(
            url,
            auth=(api_key, "x"),
            headers={"Accept": "application/json"},
            timeout=15,
        )

        if response.status_code != 200:
            raise Exception(f"Bamboo API error: {response.text}")

        data = response.json()

        if not status:
            return data

        employees = data.get("employees", [])
        normalized_status = status.lower()
        filtered = []

        for employee in employees:
            employee_status = str(
                employee.get("status")
                or employee.get("employmentStatus")
                or employee.get("employeeStatus")
                or ""
            ).lower()

            if employee_status == normalized_status:
                filtered.append(employee)

        data["employees"] = filtered
        data["filtered_at"] = datetime.utcnow().isoformat()

        return data
