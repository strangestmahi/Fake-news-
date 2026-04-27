# VerifAI — AI News Credibility Engine

> Stop misinformation before it spreads.

VerifAI is a fake news detection web app that uses semantic vector search, real-time news fetching, and a large language model to score the credibility of any news headline or article.

**Live Demo:** [fakenews-checker.netlify.app](https://fakenews-checker.netlify.app)

---

## Features

- Paste any headline or article text and get an instant credibility score
- Real-time news fetching via GNews API for context
- LLM-powered verdict (HIGH / MEDIUM / LOW) using Groq + LLaMA 3
- Semantic vector embeddings with ChromaDB
- Clean, responsive frontend hosted on Netlify
- Flask REST API backend hosted on Hugging Face Spaces

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Vector DB | ChromaDB + SentenceTransformers |
| LLM | Groq API (LLaMA 3.1 8B) |
| News API | GNews API |
| Hosting (Frontend) | Netlify |
| Hosting (Backend) | Hugging Face Spaces |

---

## Project Structure

```
Fake-news-/
├── backend/
│   ├── app.py              # Flask API
│   ├── build_db.py         # Script to populate ChromaDB
│   ├── requirements.txt    # Python dependencies
│   ├── Fake.csv            # Fake news dataset
│   └── True.csv            # Real news dataset
├── index.html              # Frontend UI
├── app.js                  # Frontend logic
└── style.css               # Styling
```

---

## How It Works

1. **Input** — User pastes a news headline or article (up to 2000 characters)
2. **Embed** — SentenceTransformers converts the text into semantic vectors
3. **Retrieve** — ChromaDB finds similar verified articles from the local database
4. **Fetch** — GNews API pulls related real-world news for context
5. **Analyse** — Groq LLM (LLaMA 3.1 8B) returns a verdict, score, and explanation
6. **Display** — Frontend shows credibility score, context, sources, and AI summary

---

## API

### `POST /api/check`

**Request:**
```json
{
  "text": "your news headline or article here"
}
```

**Response:**
```json
{
  "score": 85,
  "verdict": "high",
  "context": "This news aligns with verified reporting...",
  "summary": "This news aligns with verified reporting...",
  "sources": [
    {
      "title": "Related article title",
      "url": "https://...",
      "publisher": "GNews",
      "date": "2026"
    }
  ]
}
```

---

## Local Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key
GNEWS_API_KEY=your_gnews_api_key
```

Build the vector database:
```bash
python build_db.py
```

Run the server:
```bash
python app.py
```

### Frontend
Just open `index.html` in your browser, or serve with any static server.

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLaMA 3 |
| `GNEWS_API_KEY` | GNews API key for real-time news |

---

## Deployment

- **Frontend** → Netlify (auto-deploys from GitHub on push)
- **Backend** → Hugging Face Spaces (push to HF Space repo)

---

## License

MIT License — free to use and modify.