"""Step 3: the decision model sorts, your code decides, an LLM handles the messages the model is unsure about."""
import json
import time
import urllib.request

DECIDER_URL = "http://127.0.0.1:8000/v1/systemone"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
LLM_MODEL = "llama3.2:1b"
THRESHOLD = 0.70  # below this confidence, the message goes to the LLM


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


def decide(message, threshold=THRESHOLD):
    """Ask the decision model, then apply our own rules to pick a lane."""
    start = time.perf_counter()
    answers = ask(message, QUESTIONS)
    ms = (time.perf_counter() - start) * 1000

    team = answers["team"]["choice"]
    confidence = answers["team"]["confidence"]
    spam = answers["spam"]["noul"]
    note = ""

    if spam > 0.5:
        lane = "spam"
    elif team == "wellbeing":
        lane = "wellbeing"
        note = "Our rule: a person always replies to wellbeing messages"
    elif confidence < threshold:
        lane = "escalated"
    else:
        lane = team

    return {"lane": lane, "team": team, "confidence": confidence, "spam": spam,
            "urgency": answers["urgency"]["score"], "ms": ms, "note": note}


def draft_reply(message):
    """Ask a local LLM to draft a reply, for a person to check before sending."""
    prompt = ("You work at a university student help desk. Write a short, friendly reply "
              "(two or three sentences) to this message. If it's unclear what they need, "
              "ask one clarifying question.\n\nMessage: " + message)
    body = json.dumps({"model": LLM_MODEL, "stream": False,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    request = urllib.request.Request(OLLAMA_URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)["message"]["content"]


if __name__ == "__main__":
    for item in json.load(open("messages.json")):
        result = decide(item["text"])
        print(f"{result['lane']:<11} conf {result['confidence']:.2f}  {result['ms']:4.0f} ms  {item['text'][:50]}")
        if result["lane"] == "escalated":
            try:
                print("   LLM draft:", draft_reply(item["text"]).strip()[:150])
            except OSError:
                print("   (No LLM running. This message would go to the LLM.)")
