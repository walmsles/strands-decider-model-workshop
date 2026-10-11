"""The live board. It runs YOUR triage.py and shows every decision it makes.

    uv run board.py                              # uses triage.py
    uv run board.py --agent checkpoints/step3.py # uses a checkpoint instead
    uv run board.py --share                      # let others on the network send messages

Then open http://localhost:8080
You don't need to change this file.
"""
import argparse
import importlib.util
import json
import queue
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent


def load_agent(path):
    spec = importlib.util.spec_from_file_location("agent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("decide", "QUESTIONS", "THRESHOLD"):
        if not hasattr(module, name):
            raise SystemExit(f"{path} has no {name}. Finish Lab 4 first, or run: "
                             "uv run board.py --agent checkpoints/step3.py")
    return module


class Board:
    def __init__(self, agent):
        self.agent = agent
        self.threshold = agent.THRESHOLD
        self.lock = threading.Lock()
        self.cards = {}
        self.order = []
        self.next_id = 1
        self.decide_jobs = queue.Queue()
        self.llm_jobs = queue.Queue()
        self.drafts = {}
        self.decision_ms = []
        self.llm_ms = []
        self.error = ""
        threading.Thread(target=self.decide_worker, daemon=True).start()
        threading.Thread(target=self.llm_worker, daemon=True).start()

    def add(self, text, expected=None):
        with self.lock:
            card_id = self.next_id
            self.next_id += 1
            self.cards[card_id] = {"id": card_id, "text": text, "expected": expected, "status": "waiting"}
            self.order.append(card_id)
        self.decide_jobs.put(card_id)

    def set_threshold(self, value):
        self.threshold = value
        with self.lock:
            ids = list(self.order)
        for card_id in ids:
            self.decide_jobs.put(card_id)

    def clear(self):
        with self.lock:
            self.cards.clear()
            self.order.clear()
            self.decision_ms.clear()
            self.llm_ms.clear()

    def decide_worker(self):
        while True:
            card_id = self.decide_jobs.get()
            with self.lock:
                card = self.cards.get(card_id)
            if card is None:
                continue
            try:
                result = self.agent.decide(card["text"], self.threshold)
            except OSError:
                self.error = (f"Can't reach the decision model at {self.agent.DECIDER_URL}. "
                              "Start it in another terminal (see Lab 1 of the guide).")
                with self.lock:
                    card["status"] = "error"
                continue
            except Exception as exc:  # show mistakes in triage.py on the board, don't crash
                self.error = f"Your decide() raised {type(exc).__name__}: {exc}"
                with self.lock:
                    card["status"] = "error"
                continue
            self.error = ""
            with self.lock:
                card.update(result, status="done")
                self.decision_ms.append(result.get("ms", 0))
                if result["lane"] == "escalated" and "reply" not in card:
                    self.llm_jobs.put(card_id)

    def llm_worker(self):
        while True:
            card_id = self.llm_jobs.get()
            with self.lock:
                card = self.cards.get(card_id)
            if card is None or "reply" in card:
                continue
            text = card["text"]
            if text not in self.drafts:
                if not hasattr(self.agent, "draft_reply"):
                    self.drafts[text] = (None, 0)
                else:
                    start = time.perf_counter()
                    try:
                        reply = self.agent.draft_reply(text).strip()
                        ms = (time.perf_counter() - start) * 1000
                        self.llm_ms.append(ms)
                        self.drafts[text] = (reply, ms)
                    except Exception:
                        self.drafts[text] = (None, 0)
            reply, ms = self.drafts[text]
            with self.lock:
                card["reply"] = reply
                card["reply_ms"] = ms

    def snapshot(self):
        with self.lock:
            teams = list(self.agent.QUESTIONS["team"]["criteria"])
            cards = [dict(self.cards[i]) for i in reversed(self.order)]
            scored = [c for c in cards if c.get("status") == "done" and c.get("expected")]
            correct = sum(1 for c in scored
                          if ("spam" if c["spam"] > 0.5 else c["team"]) == c["expected"])
            avg = lambda xs: sum(xs) / len(xs) if xs else 0
            return {
                "threshold": self.threshold,
                "lanes": teams + ["escalated", "spam"],
                "cards": cards,
                "error": self.error,
                "stats": {
                    "decisions": len(self.decision_ms),
                    "decision_ms": avg(self.decision_ms),
                    "escalated": sum(1 for c in cards if c.get("lane") == "escalated"),
                    "llm_ms": avg(self.llm_ms),
                    "correct": correct,
                    "scored": len(scored),
                },
            }


def make_handler(board):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/state":
                return self.send(200, json.dumps(board.snapshot()), "application/json")
            if self.path == "/":
                return self.send(200, (HERE / "board.html").read_text(encoding="utf-8"), "text/html")
            self.send(404, "Not found", "text/plain")

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(length) or "{}")
            if self.path == "/api/message" and data.get("text", "").strip():
                board.add(data["text"].strip()[:500])
            elif self.path == "/api/samples":
                for item in json.load(open(HERE / "messages.json", encoding="utf-8")):
                    board.add(item["text"], item.get("expected"))
            elif self.path == "/api/threshold":
                board.set_threshold(float(data["value"]))
            elif self.path == "/api/clear":
                board.clear()
            self.send(200, "{}", "application/json")

        def send(self, code, text, kind):
            out = text.encode()
            self.send_response(code)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Live board for your triage agent")
    parser.add_argument("--agent", default=str(HERE / "triage.py"))
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--share", action="store_true", help="accept messages from other devices on this network")
    args = parser.parse_args()

    board = Board(load_agent(args.agent))
    host = "0.0.0.0" if args.share else "127.0.0.1"
    server = ThreadingHTTPServer((host, args.port), make_handler(board))
    print(f"Board running with {args.agent}")
    print(f"Open http://localhost:{args.port}")
    if args.share:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.connect(("10.255.255.255", 1))
                ip = s.getsockname()[0]
            except OSError:
                ip = "<this laptop's IP>"
        print(f"Others on this network can send messages at http://{ip}:{args.port}")
        print("Only the board is shared. The decision model stays private to this laptop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
