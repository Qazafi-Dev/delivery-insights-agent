import datetime
from datetime import date

import ollama

from .db import get_schema, run_query

MODEL = "qwen2.5:3b"
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

# Fixed replies for requests this bot can never handle (it has past data only)
REFUND_REPLY = (
    "I can't process refunds or change orders. I only analyse past delivery data. "
    "Please contact the delivery app's support about refunds."
)
LIVE_TRACKING_REPLY = (
    "I can't see live orders or driver locations. I only have past delivery data. "
    "For an order in progress, please contact the restaurant or the delivery app's support."
)

# Each rule is (trigger words/phrases, reply). First matching rule wins.
OUT_OF_SCOPE_RULES = [
    (["refund", "money back", "complaint", "cancel my"], REFUND_REPLY),
    (
        [
            "where is",
            "still waiting",
            "my driver",
            "my order",
            "tracking",
            "track",
            "eta",
        ],
        LIVE_TRACKING_REPLY,
    ),
]


def out_of_scope_reply(question: str) -> str | None:
    """Return a fixed reply if the question is something we can't do, else None."""
    text = question.lower()  # lowercase so "Refund" matches "refund"
    # Split into whole words so "eta" doesn't match inside a longer word
    words = text.replace("?", " ").replace(",", " ").replace(".", " ").split()
    for phrases, reply in OUT_OF_SCOPE_RULES:
        for phrase in phrases:
            # multi-word phrases are searched in the full text; single words must match exactly
            matched = (phrase in text) if " " in phrase else (phrase in words)
            if matched:
                return reply
    return None  # nothing matched, so let the model handle it


def leaks_sql(text: str) -> bool:
    """True if the model's reply shows SQL as text instead of calling the tool."""
    return "```" in text or text.lstrip().upper().startswith("SELECT")


def answer(messages: list) -> str:
    """Take the whole chat so far and return the assistant's next reply."""
    question = messages[-1]["content"]  # the last message is the user's question

    blocked = out_of_scope_reply(question)  # step 1: is it something we can't do?
    if blocked:
        messages.append({"role": "assistant", "content": blocked})
        return blocked  # reply immediately, no model call needed

    for _ in range(MAX_STEPS):  # step 2: the agent loop (max 5 rounds)
        resp = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.message  # the model's reply

        if msg.tool_calls:  # the model asked to query the database
            messages.append(msg)
            for call in msg.tool_calls:
                try:
                    result = run_query(
                        call.function.arguments["query"]
                    )  # our code runs it
                except Exception as e:
                    result = f"Error: {e}"  # give the error back so the model can retry
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": call.function.name,
                        "content": str(result),
                    }
                )
            continue  # go around again so the model can read the result

        text = msg.content or ""  # a plain-text reply
        if leaks_sql(text):  # it showed SQL instead of using the tool
            # Don't save the bad reply. Nudge the model instead.
            messages.append(
                {
                    "role": "user",
                    "content": "Do not show SQL in your reply. Call the run_sql_query tool "
                    "to get the data, then answer in plain language.",
                }
            )
            continue

        messages.append(msg)  # normal reply (greeting, help, final answer)
        return text

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
