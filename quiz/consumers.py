from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

import json
import random
import logging

from quiz.models import Question, CodingProblem, CustomUser
from quiz.utils import call_judge0
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# ---------------------------
# SIMPLE QUIZ GAME CONSUMER
# ---------------------------

# Store rooms in memory.
# This is enough for a small project / demo.
ROOMS = {}


class QuizConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info("Quiz WebSocket connected")

    async def disconnect(self, close_code):
        logger.info(f"Quiz WebSocket disconnected: {close_code}")
        # For now we don't remove from ROOMS.
        # (Can be improved later.)

    async def receive(self, text_data=None, bytes_data=None):
        # Basic JSON parsing
        try:
            data = json.loads(text_data)
        except Exception:
            await self.send(json.dumps({"error": "invalid json"}))
            return

        action = data.get("action")

        if action == "create":
            await self.handle_create(data)
        elif action == "join":
            await self.handle_join(data)
        elif action == "answer":
            await self.handle_answer(data)
        # you can add "leave" later if needed

    async def handle_create(self, data):
        """Create a new quiz room with one player."""
        room_name = f"room_{random.randint(1000, 9999)}"
        player = data.get("player", "Player")

        config = {
            "topic": data.get("topic", "any"),
            "difficulty": data.get("difficulty", "any"),
            "num_questions": int(data.get("num_questions", 5)),
        }

        ROOMS[room_name] = {
            "players": [player],
            "config": config,
            "questions": [],
            "current_q_index": 0,
            "scores": {player: 0},
            "current_answers": {},
            "game_active": False,
        }

        self.room_name = room_name
        self.player_name = player

        await self.channel_layer.group_add(room_name, self.channel_name)

        await self.send(json.dumps({
            "event": "created",
            "room": room_name,
            "players": ROOMS[room_name]["players"],
        }))

    async def handle_join(self, data):
        """Second player joins an existing room."""
        room_name = data.get("room")
        player = data.get("player", "Player2")

        if not room_name or room_name not in ROOMS:
            await self.send(json.dumps({"error": "Room not found"}))
            return

        room = ROOMS[room_name]

        if len(room["players"]) >= 2:
            await self.send(json.dumps({"error": "Room is full"}))
            return

        # If duplicate name, make it unique
        if player in room["players"]:
            player = f"{player}_{random.randint(1, 99)}"

        room["players"].append(player)
        room["scores"][player] = 0

        self.room_name = room_name
        self.player_name = player

        await self.channel_layer.group_add(room_name, self.channel_name)

        # Notify both players
        await self.channel_layer.group_send(
            room_name,
            {
                "type": "player_joined_event",
                "players": room["players"],
                "player": player,
            }
        )

        # Start game when 2 players in room
        if len(room["players"]) == 2:
            await self.start_game(room_name)

    async def start_game(self, room_name):
        """Fetch questions from DB and start the quiz."""
        room = ROOMS[room_name]
        room["game_active"] = True

        questions = await self.get_questions(
            topic=room["config"]["topic"],
            difficulty=room["config"]["difficulty"],
            num_questions=room["config"]["num_questions"],
        )

        room["questions"] = questions
        await self.send_question(room_name)

    @database_sync_to_async
    def get_questions(self, topic, difficulty, num_questions):
        """Simple version: just filter and pick random questions."""
        qs = Question.objects.all()

        if topic != "any":
            qs = qs.filter(category__iexact=topic)
        if difficulty != "any":
            qs = qs.filter(difficulty__iexact=difficulty)

        qs = qs.order_by("?")[:num_questions]

        result = []
        for q in qs:
            options = q.options
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except Exception:
                    options = []

            if not isinstance(options, list):
                options = []

            try:
                correct_idx = int(q.correct_answer)
            except Exception:
                correct_idx = 0

            result.append({
                "id": q.id,
                "question_text": q.question_text,
                "options": options,
                "correct_option": correct_idx,
                "explanation": q.explanation or "No explanation available",
            })

        return result

    async def send_question(self, room_name):
        """Send current question to both players."""
        room = ROOMS[room_name]
        idx = room["current_q_index"]

        if idx >= len(room["questions"]):
            await self.finish_game(room_name)
            return

        q = room["questions"][idx]
        room["current_answers"] = {}

        await self.channel_layer.group_send(
            room_name,
            {
                "type": "question_event",
                "question_text": q["question_text"],
                "options": q["options"],
                "order": idx + 1,
                "total": len(room["questions"]),
            }
        )

    async def handle_answer(self, data):
        """Handle answer from a player."""
        room_name = data.get("room")
        player = data.get("player")
        selected_idx = data.get("selected")

        if not room_name or room_name not in ROOMS:
            return

        room = ROOMS[room_name]
        if not room["game_active"]:
            return

        # Ignore if this player already answered
        if player in room["current_answers"]:
            return

        room["current_answers"][player] = selected_idx

        q_idx = room["current_q_index"]
        q = room["questions"][q_idx]

        is_correct = (selected_idx == q["correct_option"])
        if is_correct:
            # simple +10 score
            room["scores"][player] += 10

        # When all players answered, go to next question
        if len(room["current_answers"]) == len(room["players"]):
            room["current_q_index"] += 1
            await self.send_question(room_name)

    async def finish_game(self, room_name):
        """Send final scores and update basic stats."""
        room = ROOMS[room_name]
        room["game_active"] = False

        scores = room["scores"]
        max_score = max(scores.values())
        winners = [p for p, s in scores.items() if s == max_score]

        results = {
            "scores": scores,
            "winners": winners,
        }

        await self.channel_layer.group_send(
            room_name,
            {
                "type": "finished_event",
                "results": results,
            }
        )

        # Simple stats update (optional)
        for player_name, score in scores.items():
            try:
                username = player_name.split("_")[0]
                user = await database_sync_to_async(CustomUser.objects.get)(
                    username=username
                )
                won = (player_name in winners)
                await database_sync_to_async(user.update_stats)(score, won=won)
            except Exception as e:
                logger.error(f"Error updating stats for {player_name}: {e}")

    # --- Events sent to clients ---

    async def player_joined_event(self, event):
        await self.send(json.dumps({
            "event": "player_joined",
            "players": event["players"],
            "player": event["player"],
        }))

    async def question_event(self, event):
        await self.send(json.dumps({
            "event": "question",
            "question_text": event["question_text"],
            "options": event["options"],
            "order": event["order"],
            "total": event["total"],
        }))

    async def finished_event(self, event):
        await self.send(json.dumps({
            "event": "finished",
            "results": event["results"],
        }))


# ------------------------------
# SIMPLE CODING BATTLE CONSUMER
# ------------------------------

BATTLES = {}


class CodingBattleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info("CodingBattle WebSocket connected")

    async def disconnect(self, close_code):
        logger.info(f"CodingBattle WebSocket disconnected: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
        except Exception:
            return

        action = data.get("action")

        if action == "create":
            await self.handle_create(data)
        elif action == "join":
            await self.handle_join(data)
        elif action == "submit":
            await self.handle_submit(data)

    async def handle_create(self, data):
        room_name = f"battle_{random.randint(1000, 9999)}"
        player = data.get("player", "Player")
        difficulty = data.get("difficulty", "mixed")

        # Try to start with "Hello World"
        problem = await self.get_specific_problem("Hello World")
        if not problem:
            problem = await self.get_random_problem(difficulty)

        BATTLES[room_name] = {
            "players": [player],
            "problem": problem,
            "submissions": {},
            "game_active": False,
        }

        self.room_name = room_name
        self.player_name = player

        await self.channel_layer.group_add(room_name, self.channel_name)

        await self.send(json.dumps({
            "event": "created",
            "room": room_name,
            "players": BATTLES[room_name]["players"],
            "problem": self.serialize_problem(problem),
        }))

    async def handle_join(self, data):
        room_name = data.get("room")
        player = data.get("player", "Player2")

        if not room_name or room_name not in BATTLES:
            await self.send(json.dumps({"error": "Room not found"}))
            return

        battle = BATTLES[room_name]

        if len(battle["players"]) >= 2:
            await self.send(json.dumps({"error": "Room is full"}))
            return

        if player in battle["players"]:
            player = f"{player}_{random.randint(1, 99)}"

        battle["players"].append(player)

        self.room_name = room_name
        self.player_name = player

        await self.channel_layer.group_add(room_name, self.channel_name)

        await self.send(json.dumps({
            "event": "joined",
            "room": room_name,
            "player": player,
        }))

        await self.channel_layer.group_send(
            room_name,
            {
                "type": "player_joined_event",
                "players": battle["players"],
                "player": player,
            }
        )

        # Start battle when 2 players are inside
        if len(battle["players"]) == 2:
            await self.start_battle(room_name)

    async def start_battle(self, room_name):
        battle = BATTLES[room_name]
        battle["game_active"] = True

        await self.channel_layer.group_send(
            room_name,
            {
                "type": "battle_started_event",
                "problem": self.serialize_problem(battle["problem"]),
            }
        )

    async def handle_submit(self, data):
        """Run user's code with Judge0 and send back results."""
        room_name = self.room_name
        player = self.player_name

        if room_name not in BATTLES:
            return

        battle = BATTLES[room_name]
        problem = battle["problem"]

        source_code = data.get("source_code", "")
        language_id = data.get("language_id")

        # Make sure test_cases is a list
        if isinstance(problem.test_cases, list):
            test_cases = problem.test_cases
        else:
            test_cases = json.loads(problem.test_cases)

        results = []
        passed_count = 0

        # Inform both sides that this player is running code
        await self.channel_layer.group_send(
            room_name,
            {
                "type": "submission_event",
                "player": player,
                "status": "running",
            }
        )

        total_runtime = 0.0

        for case in test_cases:
            res = await sync_to_async(call_judge0, thread_sensitive=False)(
                source_code,
                language_id,
                case["input"],
                case["expected_output"],
            )

            passed = (res.get("status_id") == 3)
            if passed:
                passed_count += 1

            runtime = float(res.get("time") or 0.0)
            total_runtime += runtime

            results.append({
                "input": case["input"],
                "expected": case["expected_output"],
                "actual": res.get("stdout"),
                "passed": passed,
                "error": res.get("stderr"),
            })

        submission_time = timezone.now().timestamp()

        battle["submissions"][player] = {
            "passed": passed_count,
            "total": len(test_cases),
            "results": results,
            "code": source_code,
            "runtime": total_runtime,
            "submission_time": submission_time,
        }

        await self.send(json.dumps({
            "event": "submission_result",
            "passed": passed_count,
            "total": len(test_cases),
            "results": results,
        }))

        # Inform opponent about result
        await self.channel_layer.group_send(
            room_name,
            {
                "type": "opponent_submission_event",
                "player": player,
                "passed": passed_count,
                "total": len(test_cases),
                "code": source_code,
            }
        )

        # Check winner when both players have submitted
        if len(battle["submissions"]) == 2:
            await self.determine_winner(room_name)

    async def determine_winner(self, room_name):
        battle = BATTLES[room_name]
        p1, p2 = battle["players"]

        if p1 not in battle["submissions"] or p2 not in battle["submissions"]:
            return

        s1 = battle["submissions"][p1]
        s2 = battle["submissions"][p2]

        winner = None
        reason = ""

        # 1. More passed tests
        if s1["passed"] > s2["passed"]:
            winner = p1
            reason = "Passed more tests"
        elif s2["passed"] > s1["passed"]:
            winner = p2
            reason = "Passed more tests"
        else:
            # 2. Faster runtime
            if s1["runtime"] < s2["runtime"]:
                winner = p1
                reason = "Better runtime"
            elif s2["runtime"] < s1["runtime"]:
                winner = p2
                reason = "Better runtime"
            else:
                # 3. Faster submission
                if s1["submission_time"] < s2["submission_time"]:
                    winner = p1
                    reason = "Submitted faster"
                else:
                    winner = p2
                    reason = "Submitted faster"

        await self.declare_winner(room_name, winner, reason)

    async def declare_winner(self, room_name, winner, reason):
        battle = BATTLES[room_name]
        battle["game_active"] = False

        await self.channel_layer.group_send(
            room_name,
            {
                "type": "game_over_event",
                "winner": winner,
                "reason": reason,
                "submissions": battle["submissions"],
            }
        )

        # Simple stats update
        for player_name in battle["players"]:
            try:
                username = player_name.split("_")[0]
                user = await database_sync_to_async(CustomUser.objects.get)(
                    username=username
                )
                is_win = (player_name == winner)
                score = 100 if is_win else 20
                await database_sync_to_async(user.update_stats)(score, won=is_win)
            except Exception as e:
                logger.error(f"Error updating stats for {player_name}: {e}")

    # ---- DB helpers ----

    @database_sync_to_async
    def get_random_problem(self, difficulty):
        qs = CodingProblem.objects.all()
        if difficulty != "mixed":
            qs = qs.filter(difficulty__iexact=difficulty)
        return qs.order_by("?").first()

    @database_sync_to_async
    def get_specific_problem(self, title):
        return CodingProblem.objects.filter(title__iexact=title).first()

    # ---- Serialization and events ----

    def serialize_problem(self, problem):
        if not problem:
            return {}
        return {
            "title": problem.title,
            "description": problem.description,
            "starter_code": problem.starter_code,
            "test_cases": problem.test_cases,
        }

    async def player_joined_event(self, event):
        await self.send(json.dumps({
            "event": "player_joined",
            "players": event["players"],
            "player": event["player"],
        }))

    async def battle_started_event(self, event):
        await self.send(json.dumps({
            "event": "battle_started",
            "problem": event["problem"],
        }))

    async def submission_event(self, event):
        if event["player"] != self.player_name:
            await self.send(json.dumps({
                "event": "opponent_running",
                "player": event["player"],
            }))

    async def opponent_submission_event(self, event):
        if event["player"] != self.player_name:
            await self.send(json.dumps({
                "event": "opponent_result",
                "player": event["player"],
                "passed": event["passed"],
                "total": event["total"],
                "code": event["code"],
            }))

    async def game_over_event(self, event):
        await self.send(json.dumps({
            "event": "game_over",
            "winner": event["winner"],
            "reason": event["reason"],
            "submissions": event["submissions"],
        }))
