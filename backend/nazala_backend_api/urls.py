from django.urls import path
from .views import (
    game_current, my_profile,
    game_id_detail, game_id_start, game_id_archive,
    game_id_turn_current, game_id_turn_init, game_id_turn_submit,
    game_id_player_init, game_id_player_submit
)

urlpatterns = [
    path("api/game/current/", game_current, name="game_current"),
    path("api/game/my_profile/", my_profile, name="my_profile"),

    path("api/game/<int:game_id>/detail/", game_id_detail, name="game_id_detail"),
    path("api/game/<int:game_id>/start/", game_id_start, name="game_id_start"),
    path("api/game/<int:game_id>/archive/", game_id_archive, name="game_id_archive"),

    path("api/game/<int:game_id>/turn/current", game_id_turn_current, name="game_id_turn_current"),
    path("api/game/<int:game_id>/turn/init", game_id_turn_init, name="game_id_turn_init"),
    path("api/game/<int:game_id>/turn/submit", game_id_turn_submit, name="game_id_turn_submit"),
    
    path("api/game/<int:game_id>/player/init/", game_id_player_init, name="game_id_player_init"),
    path("api/game/<int:game_id>/player/submit/", game_id_player_submit, name="game_id_player_submit"),
]
