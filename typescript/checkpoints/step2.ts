// Step 2: ask three questions about every message, in one call each.
import { readFileSync } from "node:fs";

const DECIDER_URL = "http://127.0.0.1:8000/v1/systemone";

// Send a message (the state) and some questions to the decision model. Returns its answers.
async function ask(state: string, questions: object): Promise<any> {
  const response = await fetch(DECIDER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, questions }),
  }).catch(() => {
    throw new Error(`Can't reach the decision model at ${DECIDER_URL}. Is it running?`);
  });
  if (!response.ok) throw new Error(`Decision model said ${response.status}: ${await response.text()}`);
  return (await response.json()).answers;
}

const QUESTIONS = {
  team: {
    type: "choice",
    instructions: "Which team should handle this student's message?",
    criteria: {
      it_support: "logins, passwords, wifi, laptops, printing, online systems",
      enrolments: "enrolling, subjects, tutorials, timetables, fees, official letters",
      library: "books, loans, overdue items, study rooms",
      wellbeing: "stress, health, money worries, personal difficulties",
    },
  },
  urgency: {
    type: "score",
    instructions: "How urgent is this message?",
    criteria: ["low", "medium", "high"],
  },
  spam: {
    type: "noul",
    instructions: "Is this message spam or a scam?",
  },
};

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
