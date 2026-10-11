"""Run this during Lab 1, once the decider server is up:  uv run setup_check.py

Start the decision model first, in another terminal:
    uvx strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000
"""
import json
import subprocess
import platform
import shutil
import sys
import time
import urllib.error
import urllib.request

DECIDER_URL = "http://127.0.0.1:8000/v1/systemone"
OLLAMA_URL = "http://127.0.0.1:11434"
LLM_MODEL = "llama3.2:1b"

results = []


def report(ok, required, name, detail):
    results.append((ok, required))
    mark = "PASS" if ok else ("FAIL" if required else "WARN")
    print(f"[{mark}] {name}: {detail}")


def post(url, payload):
    body = json.dumps(payload).encode()
    request = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


print(f"Checking {platform.system()} {platform.machine()}, Python {platform.python_version()}\n")

report(sys.version_info >= (3, 10), True, "Python version",
       "OK" if sys.version_info >= (3, 10) else "need Python 3.10 or newer (3.12 recommended)")

report(shutil.which("uv") is not None, True, "uv installed",
       "found" if shutil.which("uv") else "not found. Install from https://docs.astral.sh/uv/")

report(shutil.which("uvx") is not None, True, "uvx installed",
       "found" if shutil.which("uvx") else "not found. uvx ships with uv; reinstall uv")

node = shutil.which("node")
if node:
    version = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    major, minor = (int(x) for x in version.lstrip("v").split(".")[:2])
    node_ok = major >= 24 or (major == 22 and minor >= 22)
    report(node_ok, False, "Node.js (TypeScript track only)",
           f"{version} OK" if node_ok else f"{version} is too old. Install Node 24 or newer: nvm install 24")
else:
    report(False, False, "Node.js (TypeScript track only)",
           "not found. Only needed for the TypeScript track: install nvm, then run: nvm install 24")

test = {
    "state": "Help! My payouts have been failing for 3 days!",
    "questions": {
        "team": {"type": "choice", "instructions": "Which team should handle this?",
                 "criteria": {"billing": "payments and payouts", "sales": "buying", "retail": "shops"}},
        "urgency": {"type": "score", "instructions": "How urgent is this?", "criteria": ["low", "medium", "high"]},
        "spam": {"type": "noul", "instructions": "Is this message spam?"},
    },
}
try:
    post(DECIDER_URL, test)  # first call warms the model up
    start = time.perf_counter()
    answers = post(DECIDER_URL, test)["answers"]
    ms = (time.perf_counter() - start) * 1000
    shape_ok = ("choice" in answers["team"] and "confidence" in answers["team"]
                and "score" in answers["urgency"] and "noul" in answers["spam"])
    report(shape_ok, True, "Decision model answers",
           f"team={answers['team'].get('choice')} in {ms:.0f} ms" if shape_ok
           else f"unexpected answer shape, tell the facilitator: {json.dumps(answers)[:300]}")
    if shape_ok and ms > 1500:
        report(False, False, "Decision speed", f"{ms:.0f} ms is slow. It will work, but consider pairing up.")
except urllib.error.HTTPError as exc:
    report(False, True, "Decision model answers",
           f"server said {exc.code}: {exc.read().decode()[:300]}. Tell the facilitator.")
except OSError:
    report(False, True, "Decision model answers",
           "not running. In another terminal run:\n"
           "       uvx strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000")

try:
    with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=5) as response:
        names = [m["name"] for m in json.load(response).get("models", [])]
    has_model = any(n.startswith(LLM_MODEL) for n in names)
    report(has_model, False, "Local LLM (optional)",
           f"{LLM_MODEL} ready" if has_model else f"Ollama is running but {LLM_MODEL} is missing. Run: ollama pull {LLM_MODEL}")
except OSError:
    report(False, False, "Local LLM (optional)",
           "Ollama not running. Lab 4 still works without it, the board just shows where the LLM would be used.")

failed = [r for r in results if not r[0] and r[1]]
print("\nAll set. On to Lab 2." if not failed else "\nFix the FAIL items above before moving on.")
