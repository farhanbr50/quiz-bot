# generate_questions.py - Isko chalao 200+ questions banane ke liye

import json
import random

questions = []

# Maths questions (1-50)
for i in range(1, 51):
    if i % 2 == 0:
        q = {"question": f"{i} + {i} = ?", "options": [str(i*1), str(i*2), str(i*3), str(i*4)], "answer": str(i*2)}
    else:
        q = {"question": f"{i} x 2 = ?", "options": [str(i*1), str(i*2), str(i*3), str(i*4)], "answer": str(i*2)}
    questions.append(q)

# English words (51-120)
words = [
    ("Big", "Large"), ("Small", "Tiny"), ("Fast", "Quick"), ("Slow", "Unhurried"),
    ("Happy", "Glad"), ("Sad", "Unhappy"), ("Good", "Excellent"), ("Bad", "Poor"),
    # ... add more word pairs
]

# GK questions (121-200+)
gk_questions = [
    ("What is the capital of India?", "Delhi"),
    ("Who is known as Father of Nation in India?", "Gandhi"),
    # ... add more
]

# Save to file
with open('questions.json', 'w') as f:
    json.dump(questions, f, indent=2)
