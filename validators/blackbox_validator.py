"""
Blackbox payload validator for GENERATE and EDIT modes.

Provides `validate_blackbox_payload(payload)` which returns (True, None)
on success or (False, error_message) on failure.

This module is used by the Django API endpoint that accepts generation
and edit requests for quiz/coding sessions.
"""
from typing import Tuple, Any, Dict, List

ALLOWED_TOPICS = {"ada", "python", "web_development"}
ALLOWED_MODES = {"single", "multiplayer"}
ALLOWED_FORMATS = {"mcq", "coding", "mixed"}
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "mixed"}
ALLOWED_EDIT_ACTIONS = {
    "add", "remove", "replace", "modify", "shuffle",
    "adjust_scoring", "adjust_difficulty", "adjust_topic",
    "regenerate_tests", "rewrite_explanations", "sanitize"
}


def _is_string(s: Any) -> bool:
    return isinstance(s, str) and len(s) > 0


def _is_positive_int(n: Any) -> bool:
    return isinstance(n, int) and n > 0


def validate_blackbox_payload(payload: Dict) -> Tuple[bool, str]:
    """Validate payload for GENERATE or EDIT mode.

    Returns (True, None) when valid, otherwise (False, error_message).
    """
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object."

    # EDIT MODE: both keys must be present and objects
    if "source_package" in payload or "edit_request" in payload:
        if "source_package" not in payload or "edit_request" not in payload:
            return False, "EDIT MODE ERROR: Both 'source_package' and 'edit_request' must be present."
        if not isinstance(payload["source_package"], dict):
            return False, "'source_package' must be an object."
        if not isinstance(payload["edit_request"], dict):
            return False, "'edit_request' must be an object."

        edit = payload["edit_request"]
        action = edit.get("action")
        if action not in ALLOWED_EDIT_ACTIONS:
            return False, f"Invalid edit action: {action}."

        targets = edit.get("targets")
        if targets is not None and not (targets == "all" or isinstance(targets, list)):
            return False, "'targets' must be a list of q_id strings or the string 'all'."

        count = edit.get("count")
        if count is not None and not isinstance(count, int):
            return False, "'count' must be an integer when provided in edit_request."

        # Basic OK for edit mode
        return True, None

    # GENERATE MODE: check required keys
    generate_keys = {"mode", "session_id", "num_questions"}
    if any(k in payload for k in generate_keys):
        for k in generate_keys:
            if k not in payload:
                return False, f"GENERATE MODE ERROR: Missing required field '{k}'."

        mode = payload.get("mode")
        if mode not in ALLOWED_MODES:
            return False, "Field 'mode' must be either 'single' or 'multiplayer'."

        if not _is_string(payload.get("session_id")):
            return False, "'session_id' must be a non-empty string."

        if not isinstance(payload.get("num_questions"), int) or payload.get("num_questions") <= 0:
            return False, "'num_questions' must be a positive integer."

        topics = payload.get("topics", [])
        if not isinstance(topics, list):
            return False, "'topics' must be an array (possibly empty)."
        # Normalize and filter topics: if empty OK, otherwise ensure allowed set
        for t in topics:
            if not isinstance(t, str):
                return False, "Each topic must be a string."
            if t and t.lower() not in ALLOWED_TOPICS:
                # Treat unknown topics as 'mixed' per upstream rules, but warn as error here
                return False, f"Invalid topic: {t}. Allowed: {sorted(list(ALLOWED_TOPICS))}."

        difficulty = payload.get("difficulty", "mixed")
        if difficulty not in ALLOWED_DIFFICULTIES:
            return False, "Invalid difficulty. Allowed: easy, medium, hard, mixed."

        fmt = payload.get("format", "mcq")
        if fmt not in ALLOWED_FORMATS:
            return False, "Invalid format. Allowed: mcq, coding, mixed."

        mix = payload.get("mix", {"mcq_percent": 80, "coding_percent": 20})
        if not isinstance(mix, dict):
            return False, "'mix' must be an object with mcq_percent and coding_percent."
        mcq_p = mix.get("mcq_percent")
        coding_p = mix.get("coding_percent")
        if not isinstance(mcq_p, (int, float)) or not isinstance(coding_p, (int, float)):
            return False, "Mix percentages must be numeric."
        if mcq_p + coding_p != 100:
            return False, "Mix percentages must add up to 100."

        tps = payload.get("time_per_question_seconds")
        if tps is not None and (not isinstance(tps, int) or tps <= 0):
            return False, "'time_per_question_seconds' must be a positive integer if provided."

        seed = payload.get("seed")
        if seed is not None and not isinstance(seed, int):
            return False, "'seed' must be an integer when provided."

        if mode == "multiplayer":
            players = payload.get("players")
            if not isinstance(players, list) or len(players) < 2:
                return False, "Multiplayer mode requires a 'players' array with at least two players."

        return True, None

    return False, "Missing payload: provide GENERATE or EDIT fields."
