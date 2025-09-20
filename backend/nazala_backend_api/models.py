import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet


ATTR_A_NAME = "Memory Equality"
ATTR_B_NAME = "Technical Control"
ATTR_C_NAME = "Society Cohesion"
ATTR_D_NAME = "Autonomy Control"

DEFAULT_ATTR_ABCD = 0


def _generate_token() -> str:
    return secrets.token_urlsafe(32)

def _dt_to_iso(dt: timezone.datetime) -> str:
    return dt.isoformat() if dt else None


class Game(models.Model):
    STATUS_WAITING = 0
    STATUS_ONGOING = 1
    STATUS_FINISHED = 10
    STATUS_ARCHIVED = 20

    max_turns = models.IntegerField(default=12)
    status = models.IntegerField(default=STATUS_WAITING)
    join_token = models.CharField(max_length=64, unique=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Game(id={self.id})(status={self.status})"

    @classmethod
    def get(cls, id: int) -> "Game":
        return cls.objects.get(id=id)

    @property
    def is_waiting(self) -> bool:
        return self.status == self.STATUS_WAITING

    @property
    def is_ongoing(self) -> bool:
        return self.status == self.STATUS_ONGOING

    @property
    def is_finished(self) -> bool:
        return self.status == self.STATUS_FINISHED
    
    @property
    def is_archived(self) -> bool:
        return self.status == self.STATUS_ARCHIVED

    def start_game(self) -> None:
        assert self.is_waiting, "Game can only be started from waiting status."
        self.status = self.STATUS_ONGOING
        self.started_at = timezone.now()
        self.save()

    def finish_game(self) -> None:
        assert self.is_ongoing, "Game can only be finished from ongoing status."
        self.status = self.STATUS_FINISHED
        self.ended_at = timezone.now()
        self.save()

    def archive_game(self) -> None:
        assert self.is_finished, "Game can only be archived from finished status."
        self.status = self.STATUS_ARCHIVED
        self.save()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "max_turns": self.max_turns,
            "join_token": self.join_token,
            "started_at": _dt_to_iso(self.started_at),
            "ended_at": _dt_to_iso(self.ended_at),
            "players_count": self.get_players_count(),
            "turns_count": self.get_turns_count(),
        }

    @classmethod
    def create_new(cls, max_turns: int = 12) -> "Game":
        join_token = secrets.token_urlsafe(16)
        return cls.objects.create(max_turns=max_turns, join_token=join_token)

    @classmethod
    def get_current(cls) -> "Game":
        last_game = cls.objects.order_by('-id').first()
        if not last_game or last_game.is_archived:
            return cls.create_new()
        return last_game
    
    def create_new_player(self) -> "Player":
        return Player.create_by_game(self)

    def get_players(self) -> "QuerySet[Player]":
        return Player.gets_by_game(self)

    def get_players_count(self) -> int:
        return Player.count_by_game(self)

    def get_current_turn(self) -> "Turn":
        if not self.is_ongoing:
            return None
        return self.turns.order_by('-index').first()

    def get_turns_count(self) -> int:
        return self.turns.count()

    def create_new_turn(self) -> "Turn":
        # TODO: remove this
        return Turn.create_by_game(game=self, question_text=f"Turn {self.get_turns_count()} question text")

class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    display_name = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    auth_token = models.CharField(max_length=128, unique=True, db_index=True, default=_generate_token)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    last_seen = models.DateTimeField(null=True, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"Player(id={self.id}) - {self.game}"

    def touch(self, ip: str = "", ua: str = ""):
        self.last_seen = timezone.now()
        if ip:
            self.last_ip = ip
        if ua:
            self.user_agent = ua[:1000]
        self.save(update_fields=["last_seen", "last_ip", "user_agent"])

    def is_token_valid(self) -> bool:
        return bool(self.auth_token) and (
            not self.token_expires_at or timezone.now() < self.token_expires_at
        )

    def issue_token(self, lifetime_hours: int = 30 * 24):
        self.auth_token = _generate_token()
        self.token_expires_at = timezone.now() + timedelta(hours=lifetime_hours)
        self.save(update_fields=["auth_token", "token_expires_at"])

    def update_name(self, name: str) -> None:
        self.display_name = name
        self.save(update_fields=["display_name"])

    @classmethod
    def create_by_game(cls, game: Game) -> "Player":
        player_count = game.players.count()
        display_name = f"Player_{player_count + 1}"
        return cls.objects.create(game=game, display_name=display_name)

    @classmethod
    def gets_by_game(cls, game: Game) -> "QuerySet[Player]":
        return cls.objects.filter(game=game)
    
    @classmethod
    def count_by_game(cls, game: Game) -> int:
        return cls.objects.filter(game=game).count()

    def make_choice(self, option: "Option") -> "Choice":
        return Choice.create_by_user_and_option(self, option)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "game": self.game.to_dict(),
            "auth_token": self.auth_token,
            "token_expires_at": _dt_to_iso(self.token_expires_at),
        }

class TurnSnapshot(models.Model):
    turn = models.OneToOneField('Turn', on_delete=models.CASCADE, related_name='snapshot')
    attr_a = models.IntegerField()
    attr_b = models.IntegerField()
    attr_c = models.IntegerField()
    attr_d = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"TurnSnapshot(id={self.id}) - {self.turn}"

    @classmethod
    def create_by_turn(cls, turn: "Turn", attr_a: int, attr_b: int, attr_c: int, attr_d: int) -> "TurnSnapshot":
        return cls.objects.create(
            turn=turn,
            attr_a=attr_a,
            attr_b=attr_b,
            attr_c=attr_c,
            attr_d=attr_d
        )


class Turn(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='turns')
    index = models.IntegerField()
    status = models.IntegerField(default=0)
    question_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['game', 'index'], name='unique_turn_index'),
    ]

    def __str__(self) -> str:
        return f"Turn(id={self.id}) - {self.game}"

    @classmethod
    def create_by_game(cls, game: Game, question_text: str) -> "Turn":
        turn_count = game.turns.count()
        return cls.objects.create(game=game, index=turn_count, question_text=question_text)

    @classmethod
    def get_by_game_and_index(cls, game: Game, index: int) -> "Turn":
        return cls.objects.get(game=game, index=index)

    def get_prev_snapshot(self) -> "TurnSnapshot":
        if not self.index:
            # TODO
            return None
        last_turn_index = self.index - 1
        prev_turn = self.get_by_game_and_index(game=self.game, index=last_turn_index)
        return prev_turn.snapshot

    def create_snapshot(self) -> "TurnSnapshot":
        # Get previous snapshot or start with zeros for first turn
        prev_snapshot = self.get_prev_snapshot()
        if prev_snapshot:
            base_a, base_b, base_c, base_d = prev_snapshot.attr_a, prev_snapshot.attr_b, prev_snapshot.attr_c, prev_snapshot.attr_d
        else:
            base_a = base_b = base_c = base_d = DEFAULT_ATTR_ABCD

        for choice in self.get_choices():
            base_a += choice.option.attr_a
            base_b += choice.option.attr_b
            base_c += choice.option.attr_c
            base_d += choice.option.attr_d

        # Create and return the snapshot
        return TurnSnapshot.create_by_turn(
            turn=self, attr_a=base_a, attr_b=base_b, attr_c=base_c, attr_d=base_d
        )
    
    def get_choices(self) -> "QuerySet[Choice]":
        return Choice.gets_by_turn(self)
    
    def get_choices_count(self) -> int:
        return self.get_choices().count()

    def all_players_made_choice(self) -> bool:
        return self.game.get_players_count() == self.get_choices_count()

    def player_has_made_choice(self, player: "Player") -> bool:
        return self.get_choices().filter(player=player).exists()

    def get_options(self) -> "QuerySet[Option]":
        return Option.gets_by_turn(self)

    def get_options_count(self) -> int:
        return self.get_options().count()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "game": self.game.to_dict(),
            "index": self.index,
            "status": self.status,
            "question_text": self.question_text,
            "options": [option.to_dict() for option in self.get_options()],
            "created_at": _dt_to_iso(self.created_at),
            "updated_at": _dt_to_iso(self.updated_at),
            "total_players": self.game.get_players_count(),
            "total_choices": self.get_choices_count(),
        }


class Option(models.Model):
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE, related_name='options')
    display_number = models.IntegerField()
    text = models.TextField()
    attr_a = models.IntegerField()
    attr_b = models.IntegerField()
    attr_c = models.IntegerField()
    attr_d = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['turn', 'display_number'], name='unique_option_per_turn'),
        ]

    def __str__(self) -> str:
        return f"Option(id={self.id}) - {self.turn}"
    
    @classmethod
    def get(cls, id: int) -> "Option":
        return cls.objects.get(id=id)

    @classmethod
    def create_by_turn(cls, turn: "Turn", text: str, attr_a: int, attr_b: int, attr_c: int, attr_d: int) -> "Option":
        return cls.objects.create(
            turn=turn,
            display_number=turn.get_options_count() + 1,
            text=text,
            attr_a=attr_a,
            attr_b=attr_b,
            attr_c=attr_c,
            attr_d=attr_d
        )

    @classmethod
    def gets_by_turn(cls, turn: "Turn") -> "QuerySet[Option]":
        return cls.objects.filter(turn=turn).order_by('display_number')

    def to_dict(self) -> dict:
        res = {
            "id": self.id,
            "turn_id": self.turn.id,
            "display_number": self.display_number,
            "text": self.text,
            "created_at": _dt_to_iso(self.created_at),
            "attrs": []
        }

        for (attr_name, attr_value) in [
            (ATTR_A_NAME, self.attr_a),
            (ATTR_B_NAME, self.attr_b),
            (ATTR_C_NAME, self.attr_c),
            (ATTR_D_NAME, self.attr_d),
        ]:
            res["attrs"].append({
                "name": attr_name,
                "value": attr_value
            })
        return res


class Choice(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='choices')
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='choices')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['player', 'option'], name='unique_choice_per_turn_of_player'),
        ]

    def __str__(self) -> str:
        return f"Choice(id={self.id}) - {self.option} - {self.player}"

    @classmethod
    def create_by_user_and_option(cls, player: "Player", option: "Option") -> "Choice":
        return cls.objects.create(player = player, option = option)

    @classmethod
    def gets_by_turn(cls, turn: "Turn") -> "QuerySet[Choice]":
        return cls.objects.filter(option__turn=turn)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "player_id": self.player.id,
            "option_id": self.option.id,
            "created_at": _dt_to_iso(self.created_at),
        }
