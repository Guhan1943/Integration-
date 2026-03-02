from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Integration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tool_name = models.CharField(max_length=50)

    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.tool_name}"