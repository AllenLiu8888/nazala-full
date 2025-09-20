import logging
import time

from django.utils.deprecation import MiddlewareMixin
from .models import Player

logger = logging.getLogger(__name__)

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request
        start_time = time.time()
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        logger.info(f"API Request: {request.method} {request.path} from {client_ip}")
        
        response = self.get_response(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(f"API Response: {response.status_code} for {request.method} {request.path} ({duration:.3f}s)")
        
        return response


AUTH_HEADER = "HTTP_AUTHORIZATION"  # Django will transfer Authorization to HTTP_AUTHORIZATION
SCHEME = "Bearer"


class PlayerAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.player = None
        raw = request.META.get(AUTH_HEADER, "")
        token = ""

        # Authorization: Bearer <token>
        if raw.startswith(f"{SCHEME} "):
            token = raw[len(SCHEME) + 1:].strip()

        if not token:
            token = request.META.get("HTTP_X_AUTH_TOKEN", "")

        if not token and request.GET.get("auth_token") is not None:
            token = request.GET.get("auth_token")

        if not token:
            return

        try:
            player = Player.objects.get(auth_token=token)
            if player.is_token_valid():
                request.player = player
                player.touch(
                    ip=request.META.get("REMOTE_ADDR", ""),
                    ua=request.META.get("HTTP_USER_AGENT", ""),
                )
        except Player.DoesNotExist:
            pass