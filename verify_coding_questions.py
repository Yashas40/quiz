import os
import django
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartquizarena.settings")
django.setup()

from quiz.views import generate_coding_questions
from quiz.models import CodingProblem

def verify():
    print("--- Verifying Coding Questions ---")
    
    # 1. Check if DB has questions
    count = CodingProblem.objects.count()
    print(f"Total CodingProblem in DB: {count}")
    if count != 30:
        print("FAIL: Expected 30 questions.")
        return

    # 2. Test Easy Questions Generation
    print("\nTesting 'Easy' generation (requesting 1 question)...")
    q1 = generate_coding_questions(1, [], "easy", 30)
    if not q1:
        print("FAIL: No questions returned.")
        return
    
    print(f"Question 1: {q1[0]['payload']['description']}")
    
    print("Testing 'Easy' generation again (requesting 1 question)...")
    q2 = generate_coding_questions(1, [], "easy", 30)
    print(f"Question 2: {q2[0]['payload']['description']}")
    
    if q1[0]['q_id'] != q2[0]['q_id']:
        print("SUCCESS: Random selection seems to be working (got different questions).")
    else:
        print("WARNING: Got the same question. Could be random chance (1/10), try running again.")

    # 3. Test Hard Questions
    print("\nTesting 'Hard' generation...")
    h_qs = generate_coding_questions(5, [], "hard", 30)
    print(f"Got {len(h_qs)} hard questions.")
    for q in h_qs:
        print(f"- {q['payload']['description'][:50]}...")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify()
