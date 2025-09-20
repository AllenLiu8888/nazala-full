from functools import wraps
from django.http import JsonResponse, Http404


def require_player(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not getattr(request, "player", None):
            return JsonResponse(
                {"ok": False, "error": "PLAYER_AUTH_REQUIRED", "message": "Auth token missing or invalid."},
                status=401
            )
        return view_func(request, *args, **kwargs)
    return _wrapped


def json_response(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        result = view_func(request, *args, **kwargs)
        if isinstance(result, JsonResponse):
            return result
        if isinstance(result, dict):
            return JsonResponse(result)
        assert (
            isinstance(result, tuple) and len(result) >= 2,
            f"View must return a tuple, got type={type(result)}, len={len(result)}."
        )
        res = dict(status=result[0], data=result[1])
        if len(result) >= 3:
            res["error"] = result[2]
        return JsonResponse(res)
    return _wrapped


def with_game(view_func):
    @wraps(view_func)
    def _wrapped(request, game_id, *args, **kwargs):
        from .models import Game
        try:
            game = Game.get(id=game_id)
        except Game.DoesNotExist:
            raise Http404(f"Game(id={game_id}) not found")
        
        return view_func(request, game, *args, **kwargs)
    return _wrapped
