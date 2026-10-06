import datetime
from datetime import date

import ollama

from .db import get_schema, run_query

MODEL = "qwen2.5:1.5b"
MAX_STEPS = 5

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Run a read-only SQLite SELECT query on the delivery database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A single SELECT statement",
                    }
                },
                "required": ["query"],
            },
        },
    }
]

SYSTEM = (
    "You are a delivery analytics assistant. You only answer questions about "
    "delivery data: orders, restaurants, drivers, delivery times, tips and cancellations. "
    "Get every number by calling the run_sql_query tool. Never write SQL in your reply. "
    "You cannot process refunds, cancel orders, or change any data. If the request is "
    "outside delivery analytics, say so in one or two sentences and suggest a question "
    "you can answer instead. Only delivered orders count as completed. "
    f"Today's date is {date.today().isoformat()}. Keep answers short and clear.\n\n"
    "Database schema:\n"
)

FALLBACK = (
    "I can only answer questions about the delivery data: orders, restaurants, "
    "drivers, delivery times, tips and cancellations. I can't process refunds or "
    'change orders. Try: "Which restaurant has the slowest deliveries?"'
)


def answer(messages: list) -> str:
    used_tool = False
    for _ in range(MAX_STEPS):
        resp = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.message
        messages.append(msg)
        if not msg.tool_calls:
            if used_tool:
                return msg.content
            messages.pop()  # drop the bad reply so it can't pollute the history
            messages.append({"role": "assistant", "content": FALLBACK})
            return FALLBACK
        used_tool = True
        for call in msg.tool_calls:
            try:
                result = run_query(call.function.arguments["query"])
            except Exception as e:
                result = f"Error: {e}"
            messages.append(
                {
                    "role": "tool",
                    "tool_name": call.function.name,
                    "content": str(result),
                }
            )
    return "I couldn't work that out. Try rephrasing the question."


def main() -> None:
    messages = [{"role": "system", "content": SYSTEM + get_schema()}]
    print("Delivery Insights Assistant. Type 'quit' to exit.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue
        messages.append({"role": "user", "content": question})
        print("\nAssistant:", answer(messages))


if __name__ == "__main__":
    main()
