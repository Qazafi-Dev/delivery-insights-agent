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
    "You are a delivery analytics assistant. Answer questions about the data by "
    "calling run_sql_query with a single SQLite SELECT statement. Never guess "
    "numbers; always query. Only delivered orders count as completed. "
    f"Today's date is {date.today().isoformat()}. Keep answers short and clear.\n\n"
    "Database schema:\n"
)


def answer(messages: list) -> str:
    for _ in range(MAX_STEPS):
        resp = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
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
