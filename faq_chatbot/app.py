import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from chatbot import FAQChatbot

app = Flask(__name__)
BASE_DIR = Path(__file__).parent
bot = FAQChatbot(str(BASE_DIR / "data" / "faqs.csv"), min_confidence=0.15)

# --- General AI fallback (Claude) ---------------------------------------
# Used for anything the FAQ matcher isn't confident about, so the bot can
# answer general questions too, not just ones in faqs.csv.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
AI_MODEL = "claude-sonnet-5"  # swap for "claude-haiku-4-5-20251001" if you want faster/cheaper replies
_anthropic_client = None

if ANTHROPIC_API_KEY:
    from anthropic import Anthropic
    _anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

SHOP_SYSTEM_PROMPT = (
    "You are the help-desk assistant for Northbound Bikes, a bike shop. "
    "Answer the user's question helpfully and concisely (2-4 sentences). "
    "If it's about the shop specifically and you don't actually know the "
    "answer, say so honestly rather than inventing shop policy."
)


def ask_ai(user_message: str) -> str:
    """Ask Claude to answer a general question the FAQ list can't cover."""
    if not _anthropic_client:
        return (
            "I don't have a confident FAQ match, and no AI fallback is "
            "configured yet. Set the ANTHROPIC_API_KEY environment variable "
            "to enable general question answering."
        )
    response = _anthropic_client.messages.create(
        model=AI_MODEL,
        max_tokens=300,
        system=SHOP_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    result = bot.respond(message)

    # Low-confidence FAQ match -> hand off to the general AI fallback
    if result["matched_question"] is None:
        ai_answer = ask_ai(message)
        result = {
            "answer": ai_answer,
            "confidence": result["confidence"],
            "matched_question": None,
            "source": "ai",
            "alternatives": result.get("alternatives", []),
        }
    else:
        result["source"] = "faq"

    return jsonify(result)


@app.route("/api/faqs")
def faqs():
    """Return the full FAQ list, used to populate suggestion chips."""
    return jsonify(
        [{"question": q} for q in bot.questions]
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
