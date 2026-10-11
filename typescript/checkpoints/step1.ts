// Step 1: ask the decision model one question about one message.
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
};

const answers = await ask("I can't log in to the student portal, it says my password has expired.", QUESTIONS);
console.log(JSON.stringify(answers, null, 2));
