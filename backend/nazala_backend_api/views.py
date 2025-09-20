import json
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest
from .models import Game, Option, Player
from .decorators import require_player, json_response, with_game
from .llm_interaction import ask_first_question_from_llm, ask_next_question_from_llm, create_turn_from_llm_response


@require_http_methods(["GET"])
@require_player
@json_response
def my_profile(request: HttpRequest):
    return True, {
        "player": request.player.to_dict(),
    }



@require_http_methods(["GET"])
@json_response
def game_current(request: HttpRequest):
    return True, {
        "game": Game.get_current().to_dict(),
    }


@require_http_methods(["GET"])
@json_response
@with_game
def game_id_detail(request: HttpRequest, game: Game):
    return True, {
        "game": game.to_dict(),
    }



# @require_http_methods(["POST"])  # TODO: enable POST method after testing
@json_response
@with_game
def game_id_start(request: HttpRequest, game: Game):
    if not game.is_waiting:
        return False, {}, "Game is not in waiting status."

    if game.get_players_count() < 1:
        return False, {}, "At least 1 players are required to start the game."

    game.start_game()

    return True, {
        "game": game.to_dict(),
    }


# @require_http_methods(["POST"])  # TODO: enable POST method after testing
@json_response
@with_game
def game_id_archive(request: HttpRequest, game: Game):
    if not game.is_finished:
        return False, {}, "Game is not in finished status."

    game.archive_game()

    return True, {
        "game": game.to_dict(),
    }


@json_response
@with_game
def game_id_turn_current(request: HttpRequest, game: Game):
    if not game.is_ongoing:
        return False, {}, "Game is not ongoing."
    turn = game.get_current_turn()
    if not turn:
        return False, {}, "Current turn does not exist."

    return True, {
        "turn": turn.to_dict(),
    }


# @require_http_methods(["POST"])  # TODO: enable POST method after testing
@json_response
@with_game
def game_id_turn_init(request: HttpRequest, game: Game):
    if not game.is_ongoing:
        return False, {}, "Game is not ongoing."
    turn = game.get_current_turn()
    # if turn.get_options_count() == 0:
    #     turn.delete()
    #     turn = None
    if turn:
        return False, {}, "Current turn already exists."

    # TODO: make it asynchronous
    llm_resp = ask_first_question_from_llm()
    turn = create_turn_from_llm_response(game, llm_resp)

    return True, {
        "turn": turn.to_dict(),
    }


# @require_http_methods(["POST"])  # TODO: enable POST method after testing
@json_response
@with_game
def game_id_turn_submit(request: HttpRequest, game: Game):
    if not game.is_ongoing:
        return False, {}, "Game is not ongoing."
    turn = game.get_current_turn()
    if turn is None:
        return False, {}, "Current turn should not be None."
    if not turn.all_players_made_choice():
        return False, {}, "Not all players have made their choices yet."

    # TODO: make it asynchronous
    llm_resp = ask_next_question_from_llm(turn)
    next_turn = create_turn_from_llm_response(llm_resp)

    return True, {
        "next_turn": next_turn.to_dict(),
    }



# @require_http_methods(["POST"])  # TODO: enable POST method after testing
@json_response
@with_game
def game_id_player_init(request: HttpRequest, game: Game):
    if request.player is not None and request.player.game == game:
        return True, {
            "player": request.player.to_dict(),
        }
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}

    player = game.create_new_player()
    player.issue_token(lifetime_hours=24 * 30)
    if payload.get("display_name"):
        player.update_name(payload.get("display_name", "").strip()[:120])

    return True, {
        "player": player.to_dict(),
    }



# @require_http_methods(["POST"])  # TODO: enable POST method after testing
@json_response
@require_player
@with_game
def game_id_player_submit(request: HttpRequest, game: Game):
    if not game.is_ongoing:
        return False, {}, "Game is not ongoing."
    
    player = request.player # type: Player
    current_turn = game.get_current_turn()
    if not current_turn:
        return False, {}, "No current turn available."
    
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return False, {}, "Invalid JSON in request body."
    
    option_id = payload.get("option_id")
    if not option_id:
        return False, {}, "option_id is required."
    
    try:
        option = Option.get(id=option_id)
    except Option.DoesNotExist:
        return False, {}, f"{option} not found."
    
    if option.turn != current_turn:
        return False, {}, f"{option} does not belong to the current turn."
    
    if current_turn.player_has_made_choice(player):
        return False, {}, "Player has already made a choice for this turn."
    
    player.make_choice(option)

    return True, {
        "option": option.to_dict(),
        "turn": current_turn.to_dict(),
        "game": game.to_dict(),
    }
