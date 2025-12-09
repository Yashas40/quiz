import pytest
from utils.blackbox_validator import validate_payload


def test_valid_generate_minimal():
    payload = {
        "mode": "single",
        "session_id": "sess1",
        "num_questions": 5,
        "topics": ["python"],
        "difficulty": "easy",
        "format": "mcq",
        "mix": {"mcq_percent": 100, "coding_percent": 0},
        "time_per_question_seconds": 15
    }
    ok, err = validate_payload(payload)
    assert ok and err is None


def test_generate_missing_field():
    payload = {"mode": "single", "session_id": "s1"}
    ok, err = validate_payload(payload)
    assert not ok
    assert "Missing required field" in err


def test_generate_invalid_topic():
    payload = {
        "mode": "single",
        "session_id": "s2",
        "num_questions": 3,
        "topics": ["history"]
    }
    ok, err = validate_payload(payload)
    assert not ok
    assert "Invalid topic" in err


def test_valid_edit_mode_with_questions():
    mcq_q = {
        "q_id": "mcq1",
        "type": "mcq",
        "topic": "python",
        "difficulty": "easy",
        "time_limit_seconds": 15,
        "payload": {
            "prompt": "What is Python?",
            "options": ["A language", "A snake", "A car"],
            "option_ids": ["A","B","C"]
        },
        "hidden_answer": {
            "correct_option_id": "A",
            "explanation": "Python is a programming language."
        },
        "reveal_after_submission": True
    }

    coding_q = {
        "q_id": "code1",
        "type": "coding",
        "topic": "python",
        "difficulty": "medium",
        "time_limit_seconds": 120,
        "payload": {
            "description": "Return sum of list.",
            "input_description": "A list of integers.",
            "output_description": "An integer sum.",
            "constraints": "len(list) <= 1000",
            "function_signature": "def sum_list(nums: List[int]) -> int:",
            "allowed_languages": ["python","ada","javascript"],
            "sample_tests": [{"input": "[1,2,3]", "expected_output": "6"}]
        },
        "hidden_answer": {
            "reference_solution_notes": "Sum elements in a loop or use built-in sum.",
            "canonical_tests": [
                {"input": "[1,2]", "expected_output": "3"},
                {"input": "[]", "expected_output": "0"}
            ],
            "hidden_tests": [
                {"input": "[1000]", "expected_output": "1000"},
                {"input": "[-1,1]", "expected_output": "0"},
                {"input": "[0,0,0]", "expected_output": "0"}
            ]
        },
        "reveal_after_submission": False
    }

    payload = {
        "source_package": {"questions": [mcq_q, coding_q]},
        "edit_request": {"action": "modify", "targets": ["mcq1"]}
    }

    ok, err = validate_payload(payload)
    assert ok and err is None


def test_edit_mode_missing_part():
    payload = {"edit_request": {"action": "add"}}
    ok, err = validate_payload(payload)
    assert not ok
    assert "Both 'source_package' and 'edit_request' must be present" in err


def test_multiplayer_requires_players():
    payload = {
        "mode": "multiplayer",
        "session_id": "m1",
        "num_questions": 5,
        "players": ["only_one"]
    }
    ok, err = validate_payload(payload)
    assert not ok
    assert "Multiplayer mode requires" in err


def test_coding_hidden_tests_requirement():
    bad_coding = {
        "q_id": "code_bad",
        "type": "coding",
        "topic": "python",
        "difficulty": "medium",
        "time_limit_seconds": 60,
        "payload": {
            "description": "Do something",
            "input_description": "x",
            "output_description": "y",
            "constraints": "",
            "allowed_languages": ["python","ada","javascript"],
            "sample_tests": [{"input":"1","expected_output":"1"}]
        },
        "hidden_answer": {
                "reference_solution_notes": "Note",
                "canonical_tests": [{"input":"1","expected_output":"1"}, {"input":"0","expected_output":"0"}],
                "hidden_tests": [{"input":"2","expected_output":"2"}]  # only 1 hidden test
            },
        "reveal_after_submission": True
    }

    payload = {"source_package": {"questions": [bad_coding]}, "edit_request": {"action":"modify"}}
    ok, err = validate_payload(payload)
    assert not ok
    assert "hidden_tests must be a list with at least 3 tests" in err

