import difflib

def is_similar(text1, text2, threshold=0.85):
    """Check if two texts are similar using SequenceMatcher"""
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio() > threshold

def test_fuzzy_matching():
    print("Testing Fuzzy Matching Logic...")
    
    cases = [
        ("What is Python?", "What is Python?", True, "Exact match"),
        ("What is Python?", "what is python", True, "Case insensitive"),
        ("What is Python?", "What is Python", True, "Missing punctuation"),
        ("What is a variable?", "What is a variable in programming?", True, "High similarity"),
        ("What is Python?", "What is Java?", False, "Different topics"),
        ("Explain recursion", "Define recursion", True, "Similar meaning/phrasing (might fail if threshold too high)"),
    ]
    
    for t1, t2, expected, desc in cases:
        result = is_similar(t1, t2)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] {desc}: '{t1}' vs '{t2}' -> {result} (Expected: {expected})")
        if result != expected:
            print(f"   Similarity: {difflib.SequenceMatcher(None, t1.lower(), t2.lower()).ratio()}")

if __name__ == "__main__":
    test_fuzzy_matching()
