# questions.py

QUESTIONS = [
    # Maths Questions
    {
        "question": "2 + 2 = ?",
        "options": ["3", "4", "5", "6"],
        "answer": "4",
        "category": "Maths"
    },
    {
        "question": "5 x 3 = ?",
        "options": ["12", "15", "18", "20"],
        "answer": "15",
        "category": "Maths"
    },
    {
        "question": "10 / 2 = ?",
        "options": ["2", "3", "4", "5"],
        "answer": "5",
        "category": "Maths"
    },
    
    # English Words (Synonyms/Antonyms)
    {
        "question": "What is the synonym of 'Happy'?",
        "options": ["Sad", "Joyful", "Angry", "Tired"],
        "answer": "Joyful",
        "category": "English"
    },
    {
        "question": "What is the opposite of 'Big'?",
        "options": ["Huge", "Large", "Small", "Giant"],
        "answer": "Small",
        "category": "English"
    },
    {
        "question": "Which word means 'to look quickly'?",
        "options": ["Stare", "Glance", "Gaze", "Peek"],
        "answer": "Glance",
        "category": "English"
    },
    
    # General Knowledge
    {
        "question": "What is the color of the sky?",
        "options": ["Green", "Red", "Blue", "Yellow"],
        "answer": "Blue",
        "category": "GK"
    },
    {
        "question": "How many days in a week?",
        "options": ["5", "6", "7", "8"],
        "answer": "7",
        "category": "GK"
    },
    
    # Add more questions here... (total 200+)
]

# To get random questions
import random

def get_random_questions(count=10):
    """Return random questions from the pool"""
    return random.sample(QUESTIONS, min(count, len(QUESTIONS)))
