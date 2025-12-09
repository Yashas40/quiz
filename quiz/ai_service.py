import json
import time
import threading
import os
from functools import lru_cache

import google.generativeai as genai
from django.conf import settings
from django.db.models.functions import Lower
from .models import Question

# Configure Gemini
try:
    # Try to get key from settings first, then env
    api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv("GEMINI_API_KEY"))
    if api_key:
        genai.configure(api_key=api_key)
except Exception:
    pass

@lru_cache(maxsize=4)
def get_gemini_model(model_name: str):
    """
    Cached Gemini model loader so we don't reinitialize models repeatedly.
    """
    return genai.GenerativeModel(model_name)

class GeminiQuestionGenerator:
    def __init__(self):
        # Default stable model
        self.model_name = "gemini-1.5-flash"
        self.model = get_gemini_model(self.model_name)

    def list_available_models(self):
        """Helper method to list available models for debugging."""
        try:
            models = genai.list_models()
            available = [
                m.name
                for m in models
                if hasattr(m, "supported_generation_methods")
                and "generateContent" in m.supported_generation_methods
            ]
            print("Available Gemini models:", available)
            return available
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def generate_questions(self, topic, difficulty="medium", num_questions=5):
        """
        Main entry: try batch generation first (fast), then fallback to per-question.
        """
        questions_data = []
        
        if not genai:
            print("Gemini API not configured")
            return []

        try:
            batch_questions = self._generate_questions_batch(
                topic=topic,
                difficulty=difficulty,
                num_questions=num_questions,
            )
            if batch_questions and len(batch_questions) >= num_questions:
                questions_data = batch_questions
            else:
                print(
                    "Batch generation failed or insufficient, "
                    "falling back to individual question generation"
                )
                questions_data = self._generate_questions_individual(
                    topic=topic,
                    difficulty=difficulty,
                    num_questions=num_questions,
                )
        except Exception as e:
            print(f"Batch generation error: {e}, falling back to individual generation")
            questions_data = self._generate_questions_individual(
                topic=topic,
                difficulty=difficulty,
                num_questions=num_questions,
            )

        return questions_data

    def _generate_questions_batch(self, topic, difficulty="medium", num_questions=5):
        """
        Generate multiple questions in a single API call (faster and cheaper).
        Uses streaming + better prompt + cached DB uniqueness check.
        """
        max_retries = 3
        base_delay = 1  # smaller base delay
        max_delay = 4   # cap backoff

        # Load existing questions (normalized) once per batch
        existing_normalized = set(
            Question.objects.annotate(normalized=Lower("question_text"))
            .values_list("normalized", flat=True)
        )

        for attempt in range(max_retries):
            try:
                prompt = f"""
Generate exactly {num_questions} unique multiple-choice aptitude questions
on the topic: {topic}.
Difficulty: {difficulty}.

RULES:
- ALL questions MUST be original, creative, and non-repeated.
- DO NOT generate common textbook or standard aptitude questions.
- EACH question must focus on a different scenario, concept, or angle.
- Avoid plagiarism and do not copy known questions.

Strict output format: a valid JSON array ONLY, no markdown, no comments:

[
  {{
    "question": "The question text",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_answer": "Option 2",
    "explanation": "Very short explanation in one sentence."
  }},
  ...
]

Requirements:
- Exactly {num_questions} objects.
- Each has exactly 4 options.
- "correct_answer" MUST exactly match one of the options.
- No markdown code fences, no extra text.
"""

                # Use streaming for faster time-to-first-byte
                response = self.model.generate_content(prompt, stream=True)
                chunks = []
                for chunk in response:
                    if hasattr(chunk, "text") and chunk.text:
                        chunks.append(chunk.text)
                response_text = "".join(chunks).strip()

                # First, try direct JSON parse
                try:
                    batch_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # If model accidentally wrapped in ```json ... ``` or ``` ... ```
                    cleaned = response_text.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[len("```json"):].strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned[len("```"):].strip()
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3].strip()

                    batch_data = json.loads(cleaned)

                if not isinstance(batch_data, list):
                    raise ValueError("Response must be a JSON array of questions")

                valid_questions = []

                for q_data in batch_data:
                    if not isinstance(q_data, dict):
                        continue

                    # Validate required keys
                    if not all(
                        k in q_data
                        for k in ("question", "options", "correct_answer")
                    ):
                        continue

                    question_text = q_data.get("question", "").strip()
                    options = q_data.get("options", [])
                    correct = q_data.get("correct_answer", "").strip()

                    if (
                        not question_text
                        or not isinstance(options, list)
                        or len(options) != 4
                    ):
                        continue

                    if correct not in options:
                        continue

                    # Normalize & check uniqueness
                    normalized = question_text.lower()
                    if normalized not in existing_normalized:
                        existing_normalized.add(normalized)
                        valid_questions.append(
                            {
                                "question": question_text,
                                "options": options,
                                "correct_answer": correct,
                                "explanation": q_data.get("explanation", "").strip(),
                            }
                        )

                    if len(valid_questions) >= num_questions:
                        break

                if len(valid_questions) >= num_questions:
                    return valid_questions[:num_questions]
                else:
                    print(
                        f"Batch attempt {attempt + 1}: "
                        f"only {len(valid_questions)} valid unique questions"
                    )

                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        print(f"Retrying batch generation in {delay} seconds...")
                        time.sleep(delay)

            except json.JSONDecodeError as e:
                print(
                    f"JSON decode error in batch generation attempt {attempt + 1}: {e}"
                )
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    time.sleep(delay)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(
                        f"Rate limit hit, retrying batch generation in "
                        f"{delay} seconds..."
                    )
                    time.sleep(delay)
                elif (
                    "404" in error_str
                    or "not found" in error_str
                    or "not supported" in error_str
                ):
                    if self._try_fallback_model():
                        # Try again with new model
                        continue
                    else:
                        print(f"Error in batch generation: {e}")
                        break
                else:
                    print(
                        f"Error in batch generation attempt {attempt + 1}: {e}"
                    )
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        time.sleep(delay)

        print("Batch generation failed after all retries")
        return []

    def _generate_questions_individual(
        self, topic, difficulty="medium", num_questions=5
    ):
        """
        Fallback: generate questions one-by-one.
        Optimized to avoid repeated DB hits for uniqueness.
        """
        questions_data = []
        max_retries = 3
        base_delay = 1
        max_delay = 4

        # Load existing questions once
        existing_normalized = set(
            Question.objects.annotate(normalized=Lower("question_text"))
            .values_list("normalized", flat=True)
        )

        for i in range(num_questions):
            attempts = 0

            while attempts < max_retries:
                try:
                    prompt = f"""
Generate ONE highly unique multiple-choice aptitude question
on the topic: {topic}.
Difficulty: {difficulty}.

Rules:
- Question must be fully original and not a common textbook or exam question.
- Use a fresh scenario or idea.
- Avoid copying known problems.

Output STRICTLY as JSON (no markdown, no comments):

{{
  "question": "The question text",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "correct_answer": "Option 3",
  "explanation": "Very short explanation in one sentence."
}}

Requirements:
- Exactly 4 options.
- "correct_answer" MUST exactly match one option text.
"""

                    # Streaming again
                    response = self.model.generate_content(prompt, stream=True)
                    chunks = []
                    for chunk in response:
                        if hasattr(chunk, "text") and chunk.text:
                            chunks.append(chunk.text)
                    response_text = "".join(chunks).strip()

                    # Try direct JSON parse
                    try:
                        question_data = json.loads(response_text)
                    except json.JSONDecodeError:
                        cleaned = response_text.strip()
                        if cleaned.startswith("```json"):
                            cleaned = cleaned[len("```json"):].strip()
                        if cleaned.startswith("```"):
                            cleaned = cleaned[len("```"):].strip()
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3].strip()
                        question_data = json.loads(cleaned)

                    # Validate structure
                    if not all(
                        k in question_data
                        for k in ("question", "options", "correct_answer")
                    ):
                        raise ValueError("Missing required fields in generated question")

                    question_text = question_data["question"].strip()
                    options = question_data["options"]
                    correct = question_data["correct_answer"].strip()

                    if (
                        not question_text
                        or not isinstance(options, list)
                        or len(options) != 4
                    ):
                        raise ValueError("Invalid options format or length")

                    if correct not in options:
                        raise ValueError("Correct answer must be one of the options")

                    normalized = question_text.lower()
                    if normalized in existing_normalized:
                        attempts += 1
                        print(
                            f"Duplicate question detected (normalized), "
                            f"regenerating... (attempt {attempts})"
                        )
                        continue

                    existing_normalized.add(normalized)
                    questions_data.append(
                        {
                            "question": question_text,
                            "options": options,
                            "correct_answer": correct,
                            "explanation": question_data.get(
                                "explanation", ""
                            ).strip(),
                        }
                    )
                    break  # success

                except json.JSONDecodeError as e:
                    print(f"JSON decode error generating question {i + 1}: {e}")
                    attempts += 1
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                        delay = min(base_delay * (2 ** attempts), max_delay)
                        print(
                            f"Rate limit hit for question {i + 1}, "
                            f"retrying in {delay} seconds..."
                        )
                        time.sleep(delay)
                        attempts += 1
                    elif (
                        "404" in error_str
                        or "not found" in error_str
                        or "not supported" in error_str
                    ):
                        if self._try_fallback_model():
                            continue
                        else:
                            attempts += 1
                    else:
                        print(f"Error generating question {i + 1}: {e}")
                        attempts += 1

            if attempts >= max_retries:
                print(
                    f"Failed to generate unique question {i + 1} "
                    f"after {max_retries} attempts. Skipping."
                )
                continue

        if len(questions_data) < num_questions:
            print(
                f"Warning: Only generated {len(questions_data)} "
                f"out of {num_questions} requested questions"
            )

        return questions_data

    def _try_fallback_model(self):
        """
        Try switching to an alternative working model, using cached instances.
        """
        alternative_models = [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]

        for alt_model in alternative_models:
            for variant in (alt_model, f"models/{alt_model}"):
                try:
                    test_model = get_gemini_model(variant)
                    # Quick lightweight test
                    resp = test_model.generate_content("test", stream=False)
                    if hasattr(resp, "text"):
                        self.model = test_model
                        self.model_name = variant
                        print(f"Successfully switched to model: {variant}")
                        return True
                except Exception:
                    continue
        print("No fallback Gemini model worked.")
        return False
