# Build a local AI agent with a decision model

A two-hour, hands-on meetup session. You'll build a help desk agent that runs entirely on
your laptop. A **decision model**, Strands Decider, reads each student message and answers
questions about it: which team, how urgent, is it spam. It doesn't write text. It picks
from the options you give it and tells you how confident it is. Your code then decides
what happens, and anything the model isn't sure about goes to a small local LLM.

You'll build in **Python** or **TypeScript**. Pick one. Both tracks do exactly the same
thing, with no extra libraries. Python files are in `python/`, TypeScript files in
`typescript/`. You'll edit one file, `triage.py` or `triage.ts`, and by the end it drives a
live board that sorts messages as you type them.

## Workshop outline

| Lab | Title | What you do | Time |
|---|---|---|---|
| 1 | Prerequisites | Install `uv`, `nvm`, Ollama; kick off the Strands Decider download | 20 min |
| 🍕 | **Pizza & networking break** | Eat while the decider download finishes in the background | |
| 2 | Ask the model a question | Call the decision model from the terminal, then from code | 10 min |
| 3 | Ask three questions at once | Add urgency and spam checks; run the full sample set | 18 min |
| 4 | Let your code decide | Turn answers + confidence into routing rules; hand off to a local LLM | 18 min |
| 5 | The live board | Run the web dashboard that visualises your `decide()` function | 14 min |
| 6 | Apply it to your own use case | Design a decision task for a problem from your own work | 10–15 min |

Lab 1 is part of the session itself — don't assume anyone has these tools already. Kick
off the Strands Decider download (a few GB) first thing in Lab 1, then do the rest of the
installs; by the time everyone's eaten, it's usually done.

Lab 6 is the point of the whole session — it's where you take the pattern home. If time's
tight, it's the one to protect; everything else can be caught up from the checkpoints.

---

## Lab 1: Prerequisites (20 min, then pizza)

Three tools plus one multi-gigabyte download. The order below starts the slow download
first, in its own terminal, so it runs in the background while you install everything
else — don't wait for it to finish before moving on to 1.2.

### 1.1 Install `uv` (Python)

[`uv`](https://docs.astral.sh/uv/) replaces `pip` and `venv`. It can also fetch Python itself,
so you don't need Python pre-installed.

macOS / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Check it:
```bash
uv --version
```
Everyone needs this, including the TypeScript track — it's how the decision model is
installed and run.

### 1.2 Get the workshop kit and start the decider download

Unzip the kit and open a terminal in the folder. Start the decision model server now, in
its own terminal — the first run downloads the model (a few GB), so get it going before
you do anything else:

```bash
uvx strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000
```

On an Apple-silicon Mac, add `--device mps`:

```bash
uvx strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000 --device mps
```

If you see "You are sending unauthenticated requests to the HF Hub" and the download looks
slow, it's a Hugging Face rate limit, not your connection — a free account removes it. Sign
up at [huggingface.co/join](https://huggingface.co/join), grab a **Read** token from
[huggingface.co/settings/tokens](https://huggingface.co/settings/tokens), then
`export HF_TOKEN=hf_your_token_here` and restart the command. Not required otherwise.

Leave this terminal running — it's your model server for the rest of the workshop. `uvx`
caches the tool environment after the first run, so later invocations start fast. While it
downloads, open a **second terminal** and keep going with 1.3 and 1.4.

### 1.3 Install `nvm` and Node — TypeScript track only

[`nvm`](https://github.com/nvm-sh/nvm) manages Node versions. Node 24+ runs `.ts` files
directly, so there's nothing else to install.

macOS / Linux:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
# then restart your terminal, or: source ~/.nvm/nvm.sh
nvm install 24
nvm use 24
```
Windows: use [nvm-windows](https://github.com/coreybutler/nvm-windows) instead, then
`nvm install 24` / `nvm use 24`.

Check it:
```bash
node --version   # v24.x or newer (v22.22+ also works)
```
Python track? Skip this.

### 1.4 Install Ollama and pull a small local LLM

Decisions go through the decider model; only the small number of messages it's *unsure*
about get handed to a real LLM to draft a reply. We don't need a big model for that — just
something fast enough to run on a laptop CPU. We're using **`llama3.2:1b`** (1 billion
parameters, about 1.3 GB on disk): small enough to download quickly and run without a GPU,
and good enough for a two- or three-sentence draft reply.

macOS / Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Windows:
```powershell
irm https://ollama.com/install.ps1 | iex
```
Or download the installer from [ollama.com/download](https://ollama.com/download).

Then pull the model:
```bash
ollama pull llama3.2:1b
```
This step is optional but recommended — Lab 4 still works without it, the board just shows
where the LLM would be used.

### 1.5 Verify everything

Once the decider server in 1.2 says it's serving on `http://127.0.0.1:8000`, run the
checker from your second terminal — no virtual environment to create, `uv run` handles it:

```bash
uv run setup_check.py
```

Every line should say PASS (WARN is fine). If anything says FAIL, follow its instructions or
ask the facilitator.

You'll use these same **two terminals** for the rest of the workshop: one running the
model (from 1.2), one for your work. In the work terminal, change into your track's
folder: `cd python` or `cd typescript`.

---

## Lab 2: ask the model a question (10 min)

First, from the terminal, so you can see the model working before any code:
```bash
uvx strands-decider ask StrandsAgents/strands-decider-2B-hobson-v19 \
  --state "I can't log in to the student portal" \
  --choice "Which team should handle this?=it_support,library,enrolments"
```
You get a choice, a probability for every option, and a confidence.

Now open `triage.py` or `triage.ts`. The `ask()` function is all it takes to call the model: it
sends the message (the *state*) and your questions, and returns the answers. Fill in the two
TODOs: write the question, and list the teams with a short description of when each applies.
Then run it:
```bash
uv run triage.py        # or: node triage.ts
```
You should see the team it picked, the probabilities, and a confidence between 0 and 1.

Try this: change the message to something vague, like "I need help", and run it again. Watch
the confidence drop. That number is what makes decision models useful.

Stuck? Copy `checkpoints/step1.py` (or `.ts`) over your triage file and carry on.

## Lab 3: ask three questions at once (18 min)

The model reads the message once, so extra questions are almost free. Add these two to your
`QUESTIONS`, after the `team` question.

Python:
```python
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this message?",
        "criteria": ["low", "medium", "high"],
    },
    "spam": {
        "type": "noul",
        "instructions": "Is this message spam or a scam?",
    },
```
TypeScript:
```ts
  urgency: {
    type: "score",
    instructions: "How urgent is this message?",
    criteria: ["low", "medium", "high"],
  },
  spam: {
    type: "noul",
    instructions: "Is this message spam or a scam?",
  },
```
That's all three question types: **choice** (pick one), **score** (a level on a scale) and
**noul** (a yes/no probability).

Now replace everything after `QUESTIONS` (the TODO check and the last two lines) with a loop
over the 20 sample messages.

Python (also add `import time` at the top):
```python
for item in json.load(open("messages.json")):
    start = time.perf_counter()
    answers = ask(item["text"], QUESTIONS)
    ms = (time.perf_counter() - start) * 1000

    team = answers["team"]["choice"]
    confidence = answers["team"]["confidence"]
    urgency = answers["urgency"]["score"]  # 0 = low, 1 = medium, 2 = high
    spam = answers["spam"]["noul"]         # 0 = not spam, 1 = spam

    print(f"{team:<11} conf {confidence:.2f}  urgency {urgency:.1f}  spam {spam:.2f}  {ms:4.0f} ms  {item['text'][:50]}")
```
TypeScript (also add `import { readFileSync } from "node:fs";` at the top):
```ts
const messages: { text: string }[] = JSON.parse(readFileSync("messages.json", "utf-8"));

for (const item of messages) {
  const start = performance.now();
  const answers = await ask(item.text, QUESTIONS);
  const ms = performance.now() - start;

  const team: string = answers.team.choice;
  const confidence: number = answers.team.confidence;
  const urgency: number = answers.urgency.score; // 0 = low, 1 = medium, 2 = high
  const spam: number = answers.spam.noul;        // 0 = not spam, 1 = spam

  console.log(`${team.padEnd(11)} conf ${confidence.toFixed(2)}  urgency ${urgency.toFixed(1)}  spam ${spam.toFixed(2)}  ${ms.toFixed(0).padStart(4)} ms  ${item.text.slice(0, 50)}`);
}
```
Run it. You'll see every message sorted, with timings in milliseconds.

Try this: look for the messages with low confidence. Open `messages.json` and you'll see many
of them are marked `"tricky"`. Then try improving a team's description in `criteria` and run
it again. Better descriptions usually mean better answers.

Stuck? `checkpoints/step2.py` (or `.ts`).

## Lab 4: let your code decide (18 min)

The model gives answers and confidence. **Your code** decides what to do with them. Replace
your loop with a `decide()` function. Read the `if` statements: these are your rules.

Python:
```python
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
LLM_MODEL = "llama3.2:1b"
THRESHOLD = 0.70  # below this confidence, the message goes to the LLM


def decide(message, threshold=THRESHOLD):
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
```
TypeScript (the board in Lab 5 needs these exported, so also put `export` in front of
`const QUESTIONS`):
```ts
const OLLAMA_URL = "http://127.0.0.1:11434/api/chat";
const LLM_MODEL = "llama3.2:1b";
export const THRESHOLD = 0.7; // below this confidence, the message goes to the LLM

export async function decide(message: string, threshold = THRESHOLD) {
  const start = performance.now();
  const answers = await ask(message, QUESTIONS);
  const ms = performance.now() - start;

  const team: string = answers.team.choice;
  const confidence: number = answers.team.confidence;
  const spam: number = answers.spam.noul;
  let lane: string;
  let note = "";

  if (spam > 0.5) {
    lane = "spam";
  } else if (team === "wellbeing") {
    lane = "wellbeing";
    note = "Our rule: a person always replies to wellbeing messages";
  } else if (confidence < threshold) {
    lane = "escalated";
  } else {
    lane = team;
  }

  return { lane, team, confidence, spam, urgency: answers.urgency.score as number, ms, note };
}
```
Notice the wellbeing rule. That's a decision you don't leave to a model, so it's plain code.

Then copy two more pieces from the bottom of `checkpoints/step3.py` (or `.ts`): the reply
function (`draft_reply` / `draftReply`), which asks the local LLM to write a reply for
escalated messages, and the run block (`if __name__ == "__main__":` / `if (import.meta.main)`),
which only runs when you run the file yourself so the board can load it in Lab 5. Run your
file again.

Escalated messages get an LLM draft. Notice how much slower the LLM is than the decision
model. If you didn't install Ollama, you'll see where the LLM would be used instead.

Try this: change `THRESHOLD` to 0.5, then 0.9, and run again. Higher means fewer mistakes but
more work for the LLM.

Stuck? `checkpoints/step3.py` (or `.ts`).

## Lab 5: the live board (14 min)

```bash
uv run board.py        # or: node board.ts
```
Open http://localhost:8080. This runs **your** triage file. The board only displays what your
code decides.

- Press **Send sample messages** and watch them sort.
- Type your own messages. Try to fool it.
- Drag **Confidence needed**. The orange mark on each card moves, and messages re-sort around
  it.

Try this: add a new team to `criteria` (for example `careers`), restart the board, and a new
column appears.

## Lab 6: apply it to your own use case (10–15 min)

Everything so far used one example — a student help desk — so the pattern doesn't stay
tied to it. This lab is about spotting the same shape in a problem you actually have, and
sketching it out before you leave.

### 6.1 Spot a decision-shaped problem

Strands Decider is a fit when a step in your workflow needs to **pick, rate, or classify**
something from free text (or an image), and today that step is either hard-coded with
brittle keyword rules, or sent to a full LLM that's overkill for the question being asked.
Signs a problem fits:

- You can describe the answer as **one of a few options**, **a score on a scale**, or
  **yes/no** — not as free text. If the honest answer is "write me a paragraph", you need
  an LLM, not a decider.
- The input is a chunk of text (a message, a ticket, a log line, a transcript, a tool-call
  argument) that a person would currently read and categorise by eye.
- Getting it wrong sometimes is fine, **as long as you know when** — you want a confidence
  score to decide whether to trust the answer or check it.

Examples beyond help-desk triage: routing support tickets by product area; flagging a
pull request description as needing a security review; scoring how well a generated
summary matches its source before showing it to a user; deciding whether an agent's next
tool call needs a human to confirm; tagging incoming leads by intent. If your use case
doesn't fit this shape, say so out loud — knowing when *not* to reach for a decider is
part of the lesson.

### 6.2 Design your questions

Pick one real problem from your own work and write it down using the same three question
types from Lab 3:

| Type | Use it for | Looks like |
|---|---|---|
| `choice` | Routing to one of a fixed set of categories | `"criteria": {"option_a": "when this applies", "option_b": "when this applies"}` |
| `score` | A level on an ordered scale (severity, confidence, sentiment) | `"criteria": ["low", "medium", "high"]` |
| `noul` | A yes/no judgement, returned as a probability | just `"instructions"`, no criteria |

For each question, write:
1. The `instructions` — the question, in plain language, as you'd ask a colleague.
2. The `criteria` — for `choice`, one line per option describing when it applies (the
   model reads these, so be as specific as the team descriptions in `triage.py`); for
   `score`, the ordered labels.
3. What **your code** does with the answer — a routing rule, a threshold, a log line. The
   model never acts on its own answer; Lab 4's `decide()` is the template for this.

### 6.3 Try it from the terminal

You don't need to write any code to test a question — use the same `ask` command from
Lab 2 with your own state and criteria:
```bash
uvx strands-decider ask StrandsAgents/strands-decider-2B-hobson-v19 \
  --state "paste a real example of your input text here" \
  --choice "Your question?=option_a,option_b,option_c"
```
Try two or three real examples from your own data, including an ambiguous one. If the
confidence stays high and the choice looks right, the question is well specified. If
confidence is consistently low, the categories probably overlap — tighten the `criteria`
descriptions, the same way you improved the team descriptions in Lab 3.

### 6.4 Decide what to take home

Before you leave, write down (on paper, in a note, wherever):

- The one decision in your own system this could replace or support.
- The `choice` / `score` / `noul` question(s) it needs.
- The confidence threshold below which a human (or an LLM) should get involved.

That's the whole pattern: a typed question, an answer with a confidence, and your code
deciding what counts as "sure enough". Everything else in this kit — the board, the LLM
hand-off, the sample messages — is one example of applying it.

## When things go wrong

| You see | Do this |
|---|---|
| "Connection refused" or "Can't reach the decision model" | The model isn't running. Start it in your other terminal (see Lab 1, step 1.2). |
| `uvx: command not found` or `uv: command not found` | `uv` isn't installed, or your terminal hasn't picked up the new `PATH`. Reopen the terminal, or re-run the Lab 1 install script. |
| `messages.json` not found | Change into your track's folder first: `cd python` or `cd typescript`. |
| `KeyError` or `undefined` | Check your question names match: `team`, `urgency`, `spam`. |
| `SyntaxError` | Usually a missing comma or bracket in `QUESTIONS`. Compare with the checkpoint file. |
| Board says your file has no `decide` | Finish Lab 4 (TypeScript: check the `export`s), or run the board with `--agent checkpoints/step3.py` (or `.ts`). |
| `node` says it can't run `.ts` files | Your Node is too old. Run `nvm install 24 && nvm use 24`. |
| Everything is slow | Decisions take longer on laptops without a GPU. It still works. Pair up if it's painful. |

## What you built, and what's next

A decision model call is a function that returns a choice and a confidence. Everything else
in your agent is ordinary code: rules, thresholds, and a hand-off to an LLM only when it's
needed. Lab 6 turned that into a repeatable design move: spot a pick/rate/classify step
hiding in your own workflow, write it as `choice`/`score`/`noul` questions, and let your
code own the threshold.

Things to try next:

- Build out the use case you sketched in Lab 6 — swap `triage.py`'s `QUESTIONS` for your
  own and point the board at it.
- The same pattern works for routing prompts to the right LLM, checking an agent's tool calls
  before they run, and catching prompt injection.
- The [Strands Decider repository](https://github.com/strands-labs/strands-decider) has an
  example that checks a tool call inside a Strands agent (`examples/strands/`), and the full
  recipe used to train the model.
- Ask questions on the Strands Decider Discord, linked from the repository.

Strands Decider is from AWS Strands Labs, open source under Apache 2.0.
