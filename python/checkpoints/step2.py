"""Step 2: ask three questions about every message, in one call each."""
import json
import time
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
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this message?",
        "criteria": ["low", "medium", "high"],
    },
    "spam": {
        "type": "noul",
        "instructions": "Is this message spam or a scam?",
    },
}

for item in json.load(open("messages.json")):
    start = time.perf_counter()
    answers = ask(item["text"], QUESTIONS)
    ms = (time.perf_counter() - start) * 1000

    team = answers["team"]["choice"]
    confidence = answers["team"]["confidence"]
    urgency = answers["urgency"]["score"]  # 0 = low, 1 = medium, 2 = high
    spam = answers["spam"]["noul"]         # 0 = not spam, 1 = spam

    print(f"{team:<11} conf {confidence:.2f}  urgency {urgency:.1f}  spam {spam:.2f}  {ms:4.0f} ms  {item['text'][:50]}")
