from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Avg, Max, Sum, Q

import json
import uuid
import random

from .models import (
    Question, QuizSession, PlayerScore, SessionQuestion,
    CustomUser, CodingProblem
)

# ==================== BASIC VIEWS ====================

def home(request):
    """Home page view"""
    return render(request, 'quiz/home.html')

def single_player(request):
    """Single player quiz view (SPA entry point)"""
    return render(request, 'quiz/single_player.html')

def multiplayer(request):
    """Multiplayer quiz view"""
    return render(request, 'quiz/multiplayer.html')

def coding_battle(request):
    """Coding battle page"""
    return render(request, 'quiz/coding_battle.html')

# ==================== AUTH ====================

def signup_view(request):
    """Simple signup view"""
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "quiz/signup.html")

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "quiz/signup.html")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "quiz/signup.html")

        # Very simple user creation (for mini project)
        user = CustomUser(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.password = password1  # NOTE: not secure, but ok for demo
        user.save()
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        messages.success(request, f"Welcome to SmartQuizArena, {username}!")
        return redirect("quiz:dashboard")

    return render(request, "quiz/signup.html")


def login_view(request):
    """Simple login view"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Try normal Django auth
        user = authenticate(request, username=username, password=password)

        # Fallback: check raw password saved as string
        if user is None:
            try:
                user_obj = CustomUser.objects.get(username=username)
                if user_obj.password == password:
                    user = user_obj
                    user.backend = "django.contrib.auth.backends.ModelBackend"
            except CustomUser.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get("next", "quiz:dashboard")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "quiz/login.html")


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("quiz:login")

# ==================== SINGLE PLAYER FLOW ====================

@csrf_exempt
def start_single_session(request):
    """
    Start a new single-player quiz session.
    Frontend sends topics, difficulty, number of questions, time-per-question.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    topics = data.get("topics", [])
    difficulty = data.get("difficulty", "mixed")
    num_questions = int(data.get("num_questions", 5))
    time_limit = int(data.get("time_per_question_seconds", 15))

    # Create a quiz session
    session = QuizSession.objects.create(
        session_type="single",
        max_players=1,
        time_limit=time_limit,
        difficulty_level=difficulty,
    )

    # Fetch questions (simple version)
    questions_data = generate_mcq_questions(
        count=num_questions,
        topics=topics,
        difficulty=difficulty,
        time_limit=time_limit,
    )

    # Link questions to session with order
    for index, q_data in enumerate(questions_data):
        # If we already have this question in DB by id, use it
        if "db_id" in q_data:
            question_obj = Question.objects.get(id=q_data["db_id"])
        else:
            # Create a new question record
            question_obj = Question.objects.create(
                question_text=q_data["question_text"],
                question_type="multiple_choice",
                difficulty=q_data.get("difficulty", "medium"),
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer"),
                explanation=q_data.get("explanation", ""),
                category=q_data.get("category", ""),
                is_ai_generated=q_data.get("is_ai_generated", False),
            )

        SessionQuestion.objects.create(
            session=session,
            question=question_obj,
            order=index,
        )

    return JsonResponse({"session_id": session.id})


@csrf_exempt
def submit_answer(request):
    """
    API endpoint to submit an answer in single player mode.
    Updates PlayerScore and returns next question or final summary.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    question_id = request.POST.get("question_id")
    answer = request.POST.get("answer")
    session_id = request.POST.get("session_id")

    if not question_id or not session_id:
        return JsonResponse({"error": "Missing question_id or session_id"}, status=400)

    try:
        question = Question.objects.get(id=question_id)
        session = QuizSession.objects.get(id=session_id)
    except Question.DoesNotExist:
        return JsonResponse({"error": "Question not found"}, status=404)
    except QuizSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    # Check answer
    is_correct = question.is_correct(answer)

    # Resolve user (anonymous or logged in)
    if request.user.is_authenticated:
        user = request.user
    else:
        user, _ = CustomUser.objects.get_or_create(
            username="anonymous",
            defaults={"email": "anonymous@example.com"},
        )

    score, _ = PlayerScore.objects.get_or_create(
        player=user,
        session=session,
        defaults={"score": 0, "correct_answers": 0, "total_answers": 0},
    )

    score.total_answers += 1
    if is_correct:
        score.correct_answers += 1
        score.score += 1
    score.save()

    # Move to next question
    next_q = session.next_question()

    response = {
        "status": "ok",
        "score": score.score,
    }

    if next_q is None:
        # Session finished
        session.end_session()

        per_question = []
        for sq in session.sessionquestion_set.order_by("order"):
            q = sq.question

            try:
                correct_idx = int(q.correct_answer)
            except Exception:
                correct_idx = None

            per_question.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "options": q.options,
                "correct_index": correct_idx,
                "explanation": q.explanation or "",
            })

        response["session_finished"] = True
        response["final_summary"] = {
            "total_questions": score.total_answers,
            "correct_answers": score.correct_answers,
            "incorrect_answers": score.total_answers - score.correct_answers,
            "score": score.score,
            "accuracy": score.accuracy,
            "per_question_summary": per_question,
        }

        # Simple user stats update
        if request.user.is_authenticated:
            is_win = score.accuracy >= 50
            request.user.update_stats(score.score, won=is_win)

    return JsonResponse(response)

# ==================== GENERIC QUIZ SESSION GENERATOR ====================

@csrf_exempt
def generate_quiz_session(request):
    """
    Generic API to generate a quiz or mixed session.
    Used by Smart Quiz Arena to get MCQ and coding questions together.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    mode = data.get("mode", "single")
    session_id = data.get("session_id", str(uuid.uuid4()))
    battle_id = data.get("battle_id") if mode == "multiplayer" else None
    num_questions = data.get("num_questions", 5)
    topics = data.get("topics", [])
    difficulty = data.get("difficulty", "mixed")
    format_type = data.get("format", "mcq")  # "mcq", "coding", "mixed"
    mix = data.get("mix", {"mcq_percent": 80, "coding_percent": 20})
    time_per_question = data.get("time_per_question_seconds", 30)

    seed = data.get("seed")
    if seed is not None:
        random.seed(seed)
    else:
        seed = random.randint(0, 1_000_000)
        random.seed(seed)

    if format_type == "mcq":
        questions = generate_mcq_questions(num_questions, topics, difficulty, time_per_question)
    elif format_type == "coding":
        questions = generate_coding_questions(num_questions, topics, difficulty, time_per_question)
    else:  # mixed
        mcq_count = int(num_questions * (mix.get("mcq_percent", 80) / 100))
        coding_count = num_questions - mcq_count
        mcq_questions = generate_mcq_questions(mcq_count, topics, difficulty, time_per_question)
        coding_questions = generate_coding_questions(coding_count, topics, difficulty, time_per_question)
        questions = mcq_questions + coding_questions
        random.shuffle(questions)

    scoring_rules = {
        "base_points_correct": 10,
        "time_bonus_per_second": 1,
        "penalty_incorrect": 0,
    }

    response = {
        "mode": mode,
        "session_id": session_id,
        "battle_id": battle_id,
        "seed_used": seed,
        "scoring_rules": scoring_rules,
        "questions": questions,
        "final_instructions": "After answering all questions, review your performance and explanations.",
    }

    # In multiplayer we don't send hidden answers
    if mode == "multiplayer":
        for q in response["questions"]:
            if "hidden_answer" in q:
                del q["hidden_answer"]

    return JsonResponse(response)

# ==================== QUESTION HELPERS ====================

def generate_mcq_questions(count, topics, difficulty, time_limit, user=None):
    """
    Simple MCQ generator:
    1) Try to get questions from DB matching topic + difficulty.
    2) If not enough, use a small hardcoded fallback list.
    """
    qs = Question.objects.filter(question_type="multiple_choice")

    # Filter by topics
    if topics and topics != [""]:
        topic_filter = Q()
        for topic in topics:
            if topic:
                topic_filter |= Q(category__icontains=topic) | Q(question_text__icontains=topic)
        qs = qs.filter(topic_filter)

    # Filter by difficulty
    if difficulty != "mixed":
        qs = qs.filter(difficulty__iexact=difficulty)

    # Shuffle and pick some
    qs = qs.order_by("?")[:count]
    question_dicts = []

    for q in qs:
        question_dicts.append({
            "question_text": q.question_text,
            "question_type": "multiple_choice",
            "difficulty": q.difficulty,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation or "",
            "category": q.category or "General",
            "is_ai_generated": q.is_ai_generated,
            "db_id": q.id,
        })

    # Fallback if DB doesn't have enough
    if len(question_dicts) < count:
        needed = count - len(question_dicts)
        fallback = get_all_mcq_questions()
        random.shuffle(fallback)
        for item in fallback[:needed]:
            question_dicts.append({
                "question_text": item["question_text"],
                "question_type": "multiple_choice",
                "difficulty": item.get("difficulty", "easy"),
                "options": item["options"],
                "correct_answer": item["correct_answer"],
                "explanation": item.get("explanation", ""),
                "category": item.get("category", "General"),
                "is_ai_generated": False,
            })

    return question_dicts[:count]


def generate_coding_questions(count, topics, difficulty, time_limit):
    """
    Generate coding questions by fetching from the CodingProblem model.
    """
    questions = []
    
    # Filter by difficulty if specified
    if difficulty != "mixed":
        available_qs = list(CodingProblem.objects.filter(difficulty=difficulty))
    else:
        available_qs = list(CodingProblem.objects.all())

    # If we need random selection (especially for Easy as requested)
    # We shuffle the available questions to ensure randomness
    random.shuffle(available_qs)
    
    # Select the requested number of questions
    selected = available_qs[:count]
    
    for q_data in selected:
        questions.append({
            "q_id": f"coding_{q_data.id}",
            "type": "coding",
            "topic": "Programming", # CodingProblem doesn't have topic yet, default to Programming
            "difficulty": q_data.difficulty,
            "time_limit_seconds": time_limit,
            "payload": {
                "description": q_data.description,
                "input_description": q_data.input_format,
                "output_description": q_data.output_format,
                "constraints": "None", 
                "function_signature": q_data.starter_code or "def solution():\n    pass",
                "allowed_languages": ["python"],
                "sample_tests": q_data.test_cases[:1] if q_data.test_cases else [],
            },
            "reveal_after_submission": True,
            "hidden_answer": {
                "reference_solution_notes": "",
                "canonical_tests": q_data.test_cases, 
                "hidden_tests": [],
            },
        })

    return questions


def get_all_mcq_questions():
    """Hardcoded fallback MCQs + DB ones."""
    fallback_questions = [
        {
            "question_text": "What is Python?",
            "options": ["A programming language", "A snake", "A database", "A web framework"],
            "correct_answer": 0,
            "explanation": "Python is a high-level programming language.",
            "category": "Programming",
            "difficulty": "easy",
        },
        {
            "question_text": "Which of these is NOT a valid variable name in Python?",
            "options": ["my_var", "2var", "_var", "var2"],
            "correct_answer": 1,
            "explanation": "Variable names cannot start with a number.",
            "category": "Programming",
            "difficulty": "easy",
        },
        {
            "question_text": "What is the output of print(2 ** 3)?",
            "options": ["6", "8", "9", "5"],
            "correct_answer": 1,
            "explanation": "2 raised to the power of 3 is 8.",
            "category": "Programming",
            "difficulty": "easy",
        },
        {
            "question_text": "Which keyword is used to define a function in Python?",
            "options": ["func", "def", "function", "define"],
            "correct_answer": 1,
            "explanation": "The 'def' keyword is used to define functions.",
            "category": "Programming",
            "difficulty": "easy",
        },
        {
            "question_text": "What data type is the result of: 3 / 2 ?",
            "options": ["int", "float", "str", "bool"],
            "correct_answer": 1,
            "explanation": "Division always returns a float in Python 3.",
            "category": "Programming",
            "difficulty": "easy",
        },
    ]

    try:
        db_qs = Question.objects.filter(question_type="multiple_choice")
        for q in db_qs:
            fallback_questions.append({
                "question_text": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation or "No explanation available.",
                "category": q.category or "General",
                "difficulty": q.difficulty,
            })
    except Exception:
        pass

    return fallback_questions


def get_all_coding_questions():
    """Deprecated: Use CodingProblem model instead."""
    return []

# ==================== QUESTION NAVIGATION ====================

@csrf_exempt
def get_next_question(request, session_id):
    """Return the next question for a quiz session."""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        session = QuizSession.objects.get(id=session_id)
        q = session.get_current_question()
        if not q:
            if session.current_question_index >= session.sessionquestion_set.count():
                return JsonResponse({"error": "Session finished"}, status=404)
            return JsonResponse({"error": "No question found"}, status=404)

        return JsonResponse({
            "question_id": q.id,
            "question_text": q.question_text,
            "options": q.options,
            "time_limit": session.time_limit,
            "difficulty": q.difficulty,
            "category": q.category,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ==================== DASHBOARD & LEADERBOARD ====================

@login_required(login_url="quiz:login")
def dashboard_view(request):
    """Simple dashboard with stats and a small trend chart."""
    user = request.user
    user_scores = PlayerScore.objects.filter(player=user).select_related("session")

    total_quizzes = user_scores.count()
    avg_score = user_scores.aggregate(Avg("score"))["score__avg"] or 0
    best_score = user_scores.aggregate(Max("score"))["score__max"] or 0
    total_questions = user_scores.aggregate(total=Sum("total_answers"))["total"] or 0
    total_correct = user_scores.aggregate(total=Sum("correct_answers"))["total"] or 0

    win_rate = 0
    if total_questions > 0:
        win_rate = (total_correct / total_questions) * 100

    stats = {
        "total_quizzes": total_quizzes,
        "average_score": round(avg_score, 1),
        "best_score": best_score,
        "total_questions": total_questions,
        "win_rate": round(win_rate, 1),
    }

    recent_quizzes = user_scores.order_by("-session__created_at")[:5]
    recent_quiz_data = []
    for score in recent_quizzes:
        recent_quiz_data.append({
            "date": score.session.created_at,
            "score": score.score,
            "accuracy": score.accuracy,
            "mode": score.session.session_type,
        })

    trend_data = user_scores.order_by("session__created_at")[:10]
    trend_dates = [s.session.created_at.strftime("%m/%d") for s in trend_data]
    trend_scores = [s.score for s in trend_data]

    context = {
        "stats": stats,
        "recent_quizzes": recent_quiz_data,
        "trend_dates": json.dumps(trend_dates),
        "trend_scores": json.dumps(trend_scores),
        "user": user,
    }
    return render(request, "quiz/dashboard.html", context)


def leaderboard_view(request):
    """Simple global leaderboard"""
    top_users = CustomUser.objects.order_by("-total_score")[:50]

    leaderboard_data = []
    for idx, u in enumerate(top_users):
        leaderboard_data.append({
            "rank": idx + 1,
            "username": u.username,
            "score": u.total_score,
            "games_played": u.games_played,
            "win_rate": round(u.win_rate, 1),
            "is_current": request.user.is_authenticated and u.id == request.user.id,
        })

    return render(request, "quiz/leaderboard.html", {"leaderboard": leaderboard_data})
