# your_app/tests/test_models.py
from django.test import TestCase
from django.db import IntegrityError

from nazala_backend_api.models import (
    Game, Player, Turn, Option, Choice, TurnSnapshot
)


class GameBasicsTests(TestCase):
    def test_game_lifecycle_and_counts(self):
        g = Game.create_new(max_turns=5)
        self.assertTrue(g.is_waiting)
        self.assertEqual(g.get_players_count(), 0)
        self.assertEqual(g.get_turns_count(), 0)
        self.assertIsNotNone(g.join_token)

        g.start_game()
        self.assertTrue(g.is_ongoing)
        self.assertIsNotNone(g.started_at)

        p1 = g.create_new_player()
        p2 = g.create_new_player()
        self.assertEqual(g.get_players_count(), 2)
        self.assertIn("Player_", p1.display_name)

        t0 = g.create_new_turn()
        self.assertEqual(g.get_turns_count(), 1)
        self.assertEqual(t0.index, 0)

        g.finish_game()
        self.assertTrue(g.is_finished)
        self.assertIsNotNone(g.ended_at)

        g.archive_game()
        self.assertTrue(g.is_archived)

    def test_get_current_skips_archived(self):
        g1 = Game.create_new()
        g1.archive_game()
        g2 = Game.get_current()
        self.assertNotEqual(g1.id, g2.id)
        self.assertTrue(g2.is_waiting)


class PlayerTests(TestCase):
    def test_token_and_touch_and_update_name(self):
        g = Game.create_new()
        p = g.create_new_player()

        # Initial state
        self.assertTrue(p.is_token_valid())
        old_token = p.auth_token

        p.issue_token(lifetime_hours=1)
        self.assertTrue(p.is_token_valid())
        self.assertNotEqual(old_token, p.auth_token)
        self.assertIsNotNone(p.token_expires_at)

        p.touch(ip="1.2.3.4", ua="UA-XYZ")
        self.assertIsNotNone(p.last_seen)
        self.assertEqual(p.last_ip, "1.2.3.4")
        self.assertEqual(p.user_agent, "UA-XYZ")

        p.update_name("Alice")
        self.assertEqual(p.display_name, "Alice")


class TurnOptionChoiceSnapshotTests(TestCase):
    def setUp(self):
        self.g = Game.create_new()
        self.g.start_game()
        self.p1 = self.g.create_new_player()
        self.p2 = self.g.create_new_player()

    def test_choice_unique_same_turn_any_option_disallowed(self):
        # create turn and options
        t0 = self.g.create_new_turn()
        o1 = Option.create_by_turn(t0, "A", 1, 0, 0, 0)
        o2 = Option.create_by_turn(t0, "B", 0, 1, 0, 0)

        # first choice should succeed
        Choice.create_by_user_and_option(self.p1, o1)

        # cannot choose again in the same turn
        with self.assertRaises(IntegrityError):
            Choice.create_by_user_and_option(self.p1, o2)

    def test_snapshot_turn0_and_turn1_accumulate(self):

        t0 = self.g.create_new_turn()
        oA = Option.create_by_turn(t0, "A", 1, 0, 0, 0)
        oB = Option.create_by_turn(t0, "B", 0, 2, 0, 0)
        Choice.create_by_user_and_option(self.p1, oA)
        Choice.create_by_user_and_option(self.p2, oB)
        s0 = t0.create_snapshot()
        assert (s0.attr_a, s0.attr_b, s0.attr_c, s0.attr_d) == (1, 2, 0, 0)

        t1 = self.g.create_new_turn()
        oC = Option.create_by_turn(t1, "C", 0, 0, 3, 0)
        Choice.create_by_user_and_option(self.p1, oC)
        s1 = t1.create_snapshot()
        assert (s1.attr_a, s1.attr_b, s1.attr_c, s1.attr_d) == (1, 2, 3, 0)