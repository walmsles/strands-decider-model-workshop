"""Step 1: ask the decision model one question about one message."""
import json
import urllib.request

DECIDER_URL = "http://127.0.0.1:8000/v1/systemone"


def ask(state, questions):
    """Send a message (the state) and some questions to the decision model. Returns its answers."""
    body = json.dumps({"state": state, "questions": questions}).encode()
    request = urllib.request.Request(DECIDER_URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["answers"]


QUESTIONS = {
    "team": {
        "type": "choice",
        "instructions": "Which team should handle this student's message?",
        "criteria": {
            "it_support": "logins, passwords, wifi, laptops, printing, online systems",
            "enrolments": "enrolling, subjects, tutorials, timetables, fees, official letters",
            "library": "books, loans, overdue items, study rooms",
            "wellbeing": "stress, health, money worries, personal difficulties",
        },
    },
}

answers = ask("I can't log in to the student portal, it says my password has expired.", QUESTIONS)
print(json.dumps(answers, indent=2))
