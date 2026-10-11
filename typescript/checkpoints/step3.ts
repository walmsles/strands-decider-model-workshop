// Step 3: the decision model sorts, your code decides, an LLM handles the messages the model is unsure about.
import { readFileSync } from "node:fs";

export const DECIDER_URL = "http://127.0.0.1:8000/v1/systemone";
const OLLAMA_URL = "http://127.0.0.1:11434/api/chat";
const LLM_MODEL = "llama3.2:1b";
export const THRESHOLD = 0.7; // below this confidence, the message goes to the LLM

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

export const QUESTIONS = {
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

// Ask the decision model, then apply our own rules to pick a lane.
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

// Ask a local LLM to draft a reply, for a person to check before sending.
export async function draftReply(message: string): Promise<string> {
  const prompt = "You work at a university student help desk. Write a short, friendly reply " +
    "(two or three sentences) to this message. If it's unclear what they need, " +
    "ask one clarifying question.\n\nMessage: " + message;
  const response = await fetch(OLLAMA_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: LLM_MODEL, stream: false, messages: [{ role: "user", content: prompt }] }),
  });
  if (!response.ok) throw new Error(`LLM said ${response.status}`);
  return (await response.json()).message.content;
}

// Only run this when you run the file yourself, not when the board loads it.
if (import.meta.main) {
  const messages: { text: string }[] = JSON.parse(readFileSync("messages.json", "utf-8"));
  for (const item of messages) {
    const result = await decide(item.text);
    console.log(`${result.lane.padEnd(11)} conf ${result.confidence.toFixed(2)}  ${result.ms.toFixed(0).padStart(4)} ms  ${item.text.slice(0, 50)}`);
    if (result.lane === "escalated") {
      try {
        console.log("   LLM draft:", (await draftReply(item.text)).trim().slice(0, 150));
      } catch {
        console.log("   (No LLM running. This message would go to the LLM.)");
      }
    }
  }
}
