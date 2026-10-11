// The live board. It runs YOUR triage.ts and shows every decision it makes.
//
//   node board.ts                                # uses triage.ts
//   node board.ts --agent checkpoints/step3.ts   # uses a checkpoint instead
//   node board.ts --share                        # let others on the network send messages
//
// Then open http://localhost:8080
// You don't need to change this file.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { networkInterfaces } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const option = (name: string, fallback: string) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};
const agentPath = option("--agent", join(HERE, "triage.ts"));
const port = Number(option("--port", "8080"));
const share = args.includes("--share");

const agent = await import(pathToFileURL(resolve(agentPath)).href);
for (const name of ["decide", "QUESTIONS", "THRESHOLD"]) {
  if (!(name in agent)) {
    console.log(`${agentPath} doesn't export ${name}. Finish Lab 4 first, or run: node board.ts --agent checkpoints/step3.ts`);
    process.exit(1);
  }
}

type Card = { id: number; text: string; expected: string | null; status: string; [key: string]: any };

let threshold: number = agent.THRESHOLD;
let cards = new Map<number, Card>();
let nextId = 1;
let decisionMs: number[] = [];
let llmMs: number[] = [];
let error = "";
const drafts = new Map<string, { reply: string | null; ms: number }>();
const decideQueue: number[] = [];
const llmQueue: number[] = [];

function add(text: string, expected: string | null = null) {
  const id = nextId++;
  cards.set(id, { id, text, expected, status: "waiting" });
  decideQueue.push(id);
}

// Decisions run one at a time, in order, like the Python board.
async function decideWorker() {
  while (true) {
    const id = decideQueue.shift();
    if (id === undefined) { await new Promise((r) => setTimeout(r, 50)); continue; }
    const card = cards.get(id);
    if (!card) continue;
    try {
      const result = await agent.decide(card.text, threshold);
      error = "";
      Object.assign(card, result, { status: "done" });
      decisionMs.push(result.ms ?? 0);
      if (result.lane === "escalated" && !("reply" in card)) llmQueue.push(id);
    } catch (err: any) {
      const message = String(err?.message ?? err);
      error = message.startsWith("Can't reach")
        ? `${message} Start it in another terminal (see Lab 1 of the guide).`
        : `Your decide() threw: ${message}`;
      card.status = "error";
    }
  }
}

async function llmWorker() {
  while (true) {
    const id = llmQueue.shift();
    if (id === undefined) { await new Promise((r) => setTimeout(r, 100)); continue; }
    const card = cards.get(id);
    if (!card || "reply" in card) continue;
    if (!drafts.has(card.text)) {
      if (typeof agent.draftReply !== "function") {
        drafts.set(card.text, { reply: null, ms: 0 });
      } else {
        const start = performance.now();
        try {
          const reply = (await agent.draftReply(card.text)).trim();
          const ms = performance.now() - start;
          llmMs.push(ms);
          drafts.set(card.text, { reply, ms });
        } catch {
          drafts.set(card.text, { reply: null, ms: 0 });
        }
      }
    }
    const draft = drafts.get(card.text)!;
    card.reply = draft.reply;
    card.reply_ms = draft.ms;
  }
}

function snapshot() {
  const all = [...cards.values()].reverse();
  const scored = all.filter((c) => c.status === "done" && c.expected);
  const correct = scored.filter((c) => (c.spam > 0.5 ? "spam" : c.team) === c.expected).length;
  const avg = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
  return {
    threshold,
    lanes: [...Object.keys(agent.QUESTIONS.team.criteria), "escalated", "spam"],
    cards: all,
    error,
    stats: {
      decisions: decisionMs.length,
      decision_ms: avg(decisionMs),
      escalated: all.filter((c) => c.lane === "escalated").length,
      llm_ms: avg(llmMs),
      correct,
      scored: scored.length,
    },
  };
}

const server = createServer(async (req, res) => {
  const send = (code: number, body: string, type: string) => {
    res.writeHead(code, { "Content-Type": `${type}; charset=utf-8` });
    res.end(body);
  };
  if (req.method === "GET" && req.url === "/") return send(200, readFileSync(join(HERE, "board.html"), "utf-8"), "text/html");
  if (req.method === "GET" && req.url === "/api/state") return send(200, JSON.stringify(snapshot()), "application/json");
  if (req.method !== "POST") return send(404, "Not found", "text/plain");

  let body = "";
  for await (const chunk of req) body += chunk;
  const data = body ? JSON.parse(body) : {};
  if (req.url === "/api/message" && data.text?.trim()) {
    add(data.text.trim().slice(0, 500));
  } else if (req.url === "/api/samples") {
    for (const item of JSON.parse(readFileSync(join(HERE, "messages.json"), "utf-8"))) add(item.text, item.expected ?? null);
  } else if (req.url === "/api/threshold") {
    threshold = Number(data.value);
    decideQueue.push(...cards.keys());
  } else if (req.url === "/api/clear") {
    cards = new Map();
    decisionMs = [];
    llmMs = [];
  }
  send(200, "{}", "application/json");
});

decideWorker();
llmWorker();
server.listen(port, share ? "0.0.0.0" : "127.0.0.1", () => {
  console.log(`Board running with ${agentPath}`);
  console.log(`Open http://localhost:${port}`);
  if (share) {
    const ip = Object.values(networkInterfaces()).flat().find((n) => n && n.family === "IPv4" && !n.internal)?.address;
    console.log(`Others on this network can send messages at http://${ip ?? "<this laptop's IP>"}:${port}`);
    console.log("Only the board is shared. The decision model stays private to this laptop.");
  }
});
