"""
FAQ Chatbot matching engine.

Pipeline:
  1. Load FAQ pairs (question, answer) from a CSV file.
  2. Preprocess each question with NLTK (lowercase, tokenize, strip
     punctuation/stopwords, lemmatize).
  3. Vectorize the cleaned FAQ questions with TF-IDF.
  4. For an incoming user message, preprocess it the same way, vectorize it,
     and rank FAQs by cosine similarity against the TF-IDF matrix.
  5. Return the best-matching answer (plus a confidence score) if it clears
     a minimum similarity threshold, otherwise a fallback message.
"""

import csv
import re
from pathlib import Path

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _ensure_nltk_data():
    """Download required NLTK corpora on first run if they're missing."""
    resources = {
        "tokenizers/punkt_tab": "punkt_tab",
        "corpora/stopwords": "stopwords",
        "corpora/wordnet": "wordnet",
        "corpora/omw-1.4": "omw-1.4",
    }
    for path, package in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(package, quiet=True)


_ensure_nltk_data()

from nltk.corpus import stopwords  # noqa: E402
from nltk.stem import WordNetLemmatizer  # noqa: E402
from nltk.tokenize import word_tokenize  # noqa: E402

STOPWORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()


def preprocess(text: str) -> str:
    """Clean and normalize text: lowercase, strip punctuation, tokenize,
    remove stopwords, and lemmatize. Returns a space-joined string ready
    for TF-IDF vectorization."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in STOPWORDS and t.strip()]
    tokens = [LEMMATIZER.lemmatize(t) for t in tokens]
    return " ".join(tokens)


class FAQChatbot:
    """Loads a FAQ CSV and answers questions via TF-IDF + cosine similarity."""

    def __init__(self, csv_path: str, min_confidence: float = 0.2):
        self.csv_path = csv_path
        self.min_confidence = min_confidence
        self.questions = []
        self.answers = []
        self._load(csv_path)
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self._matrix = self._vectorizer.fit_transform(
            [preprocess(q) for q in self.questions]
        )

    def _load(self, csv_path: str):
        path = Path(csv_path)
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = row.get("question", "").strip()
                a = row.get("answer", "").strip()
                if q and a:
                    self.questions.append(q)
                    self.answers.append(a)

    def match(self, user_message: str, top_k: int = 3):
        """Return the top_k FAQ matches for a user message as a list of
        dicts: {question, answer, score}, sorted by descending score."""
        cleaned = preprocess(user_message)
        if not cleaned:
            return []
        user_vec = self._vectorizer.transform([cleaned])
        scores = cosine_similarity(user_vec, self._matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:top_k]:
            results.append(
                {
                    "question": self.questions[i],
                    "answer": self.answers[i],
                    "score": round(float(scores[i]), 4),
                }
            )
        return results

    def respond(self, user_message: str):
        """Return the single best answer plus metadata for a user message."""
        matches = self.match(user_message, top_k=3)
        if not matches or matches[0]["score"] < self.min_confidence:
            return {
                "answer": (
                    "I'm not sure I have an answer for that yet. Try rephrasing, "
                    "or ask about repairs, rentals, warranties, sizing, or store hours."
                ),
                "confidence": matches[0]["score"] if matches else 0.0,
                "matched_question": None,
                "alternatives": matches,
            }
        best = matches[0]
        return {
            "answer": best["answer"],
            "confidence": best["score"],
            "matched_question": best["question"],
            "alternatives": matches[1:],
        }


if __name__ == "__main__":
    bot = FAQChatbot(str(Path(__file__).parent / "data" / "faqs.csv"))
    print("FAQ Chatbot ready. Type 'quit' to exit.\n")
    while True:
        msg = input("You: ").strip()
        if msg.lower() in {"quit", "exit"}:
            break
        result = bot.respond(msg)
        pct = round(result["confidence"] * 100)
        print(f"Bot ({pct}% match): {result['answer']}\n")