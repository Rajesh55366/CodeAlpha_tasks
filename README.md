# Northbound Bikes — FAQ Chatbot

A small FAQ chatbot: it matches a user's question against a set of known
FAQs using NLP preprocessing (NLTK) and TF-IDF + cosine similarity
(scikit-learn), then returns the best-matching answer with a confidence
score. Includes a simple chat web UI.

## How it works

1. **Collect FAQs** — `data/faqs.csv` holds `question,answer` pairs
   (sample topic: a bike shop). Swap in your own CSV for any other topic.
2. **Preprocess** (`chatbot.py: preprocess()`) — lowercase, strip
   punctuation, tokenize, remove stopwords, and lemmatize with NLTK.
3. **Vectorize & match** — FAQ questions are TF-IDF vectorized
   (unigrams + bigrams). An incoming message is cleaned the same way,
   vectorized, and compared against every FAQ with cosine similarity.
4. **Respond** — the highest-scoring FAQ's answer is returned if its score
   clears `min_confidence` (default 0.15); otherwise a fallback message
   is shown along with a couple of near-miss alternatives.
5. **Chat UI** (`templates/index.html`, `static/`) — a Flask-served page
   that posts messages to `/api/chat` and renders the reply with a
   confidence "gauge."

## Setup

```bash
pip install -r requirements.txt
```

The first run downloads a few small NLTK corpora automatically
(punkt, stopwords, wordnet) — this needs internet access once.

## Run

**Command line:**
```bash
python chatbot.py
```

**Web chat UI:**
```bash
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

## Using your own FAQs

Replace `data/faqs.csv` with your own two-column CSV (`question,answer`
header row required), or point `FAQChatbot(...)` at a different path in
`app.py` / `chatbot.py`.

## General AI fallback

The FAQ matcher only answers what's in `data/faqs.csv`. To make it answer
*any* question, low-confidence FAQ matches are handed off to Claude
(Anthropic's API).

1. Get a free API key at https://console.anthropic.com/settings/keys
2. Set it as an environment variable before running the app:

   **Windows (PowerShell):**
   ```powershell
   $env:ANTHROPIC_API_KEY = "sk-ant-...your-key..."
   python app.py
   ```
   (This only lasts for the current PowerShell session — you'll need to
   set it again next time you open a new terminal, unless you add it to
   your system environment variables permanently.)

   **macOS/Linux:**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-...your-key..."
   python app.py
   ```

Without a key set, the app still works — FAQ matches answer normally, and
anything outside the FAQ list gets a message asking you to configure the
key, instead of a real AI answer.

Note the Anthropic API is pay-as-you-go (small free credit for new
accounts, then billed per request) — it's not unlimited/free like using
Claude.ai in a browser.

## Notes / limitations

- TF-IDF + cosine similarity matches on shared *words*, not meaning — it
  won't know "open" means "hours" unless both words appear somewhere in
  your FAQ set. For stronger semantic matching, swap the vectorizer for
  sentence embeddings (e.g. `sentence-transformers`).
- `min_confidence` in `app.py` controls how strict matching is — lower it
  to answer more (riskier) questions, raise it to fall back more often.
