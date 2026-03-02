from django.urls import path
from .views import ZohoAuthURL, ZohoCallback , ZohoEmployeesView

urlpatterns = [
    path("zoho/auth-url/", ZohoAuthURL.as_view()),
    path("zoho/callback/", ZohoCallback.as_view()),
    # path("zoho/leads/", ZohoLeadsView.as_view()),
    path("zoho/employees/", ZohoEmployeesView.as_view()),
]