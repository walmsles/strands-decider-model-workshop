"""Your triage agent. You'll grow this file through the workshop.

Lab 2, step 1: fill in the two TODOs below, then run:  uv run triage.py
"""
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
        # TODO 1: write the question. For example: "Which team should handle this student's message?"
        "instructions": "",
        "criteria": {
            # TODO 2: one line per team, saying when that team applies. For example:
            # "it_support": "logins, passwords, wifi, laptops, printing, online systems",
            # "library": "books, loans, overdue items, study rooms",
        },
    },
}

if not QUESTIONS["team"]["instructions"] or len(QUESTIONS["team"]["criteria"]) < 2:
    raise SystemExit("Fill in TODO 1 and TODO 2 first. You need a question and at least two teams.")

answers = ask("I can't log in to the student portal, it says my password has expired.", QUESTIONS)
print(json.dumps(answers, indent=2))
