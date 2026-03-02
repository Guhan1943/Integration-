import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Integration
from .services.zoho_service import ZohoService


User = get_user_model()


# ============================
# 1️⃣ Generate Zoho Auth URL
# ============================
class ZohoAuthURL(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        url = (
            "https://accounts.zoho.in/oauth/v2/auth"
            "?scope=ZohoPeople.forms.ALL"
            f"&client_id={settings.ZOHO_CLIENT_ID}"
            "&response_type=code"
            "&access_type=offline"
            "&prompt=consent"
            f"&redirect_uri={settings.ZOHO_REDIRECT_URI}"
            f"&state={request.user.id}"
        )

        return Response({"auth_url": url})


# ============================
# 2️⃣ OAuth Callback
# ============================
class ZohoCallback(APIView):
    """
    ⚠️ No authentication here.
    OAuth redirect does NOT include session.
    We identify user via state.
    """

    def get(self, request):

        code = request.GET.get("code")
        user_id = request.GET.get("state")

        if not code:
            return Response({"error": "Authorization code missing"}, status=400)

        if not user_id:
            return Response({"error": "State parameter missing"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "Invalid user"}, status=400)

        token_url = "https://accounts.zoho.in/oauth/v2/token"

        payload = {
            "grant_type": "authorization_code",
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "redirect_uri": settings.ZOHO_REDIRECT_URI,
            "code": code,
        }

        response = requests.post(token_url, data=payload)
        token_data = response.json()

        if "access_token" not in token_data:
            return Response(
                {
                    "error": "Failed to obtain access token",
                    "details": token_data
                },
                status=400
            )

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        expires_at = timezone.now() + timedelta(seconds=int(expires_in))

        Integration.objects.update_or_create(
            user=user,
            tool_name="zoho",
            defaults={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at
            }
        )

        return Response({"message": "Zoho connected successfully"})


# ============================
# 3️⃣ Fetch Employee Data
# ============================
class ZohoEmployeesView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        integration = Integration.objects.filter(
            user=request.user,
            tool_name="zoho"
        ).first()

        if not integration:
            return Response({"error": "Zoho not connected"}, status=400)

        service = ZohoService(integration)
        data = service.get_employees()

        return Response(data)