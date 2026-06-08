# llm_eval_harness/apps/users/auth.py
from django.contrib.auth import get_user_model
from ninja.security import APIKeyHeader


class ApiKeyAuth(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        User = get_user_model()
        try:
            return User.objects.get(api_key=key, is_active=True)
        except User.DoesNotExist:
            return None
