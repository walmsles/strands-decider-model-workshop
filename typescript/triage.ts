// Your triage agent. You'll grow this file through the workshop.
//
// Lab 2, step 1: fill in the two TODOs below, then run:  node triage.ts
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
    // TODO 1: write the question. For example: "Which team should handle this student's message?"
    instructions: "",
    criteria: {
      // TODO 2: one line per team, saying when that team applies. For example:
      // it_support: "logins, passwords, wifi, laptops, printing, online systems",
      // library: "books, loans, overdue items, study rooms",
    },
  },
};

if (!QUESTIONS.team.instructions || Object.keys(QUESTIONS.team.criteria).length < 2) {
  console.log("Fill in TODO 1 and TODO 2 first. You need a question and at least two teams.");
  process.exit(1);
}

const answers = await ask("I can't log in to the student portal, it says my password has expired.", QUESTIONS);
console.log(JSON.stringify(answers, null, 2));
