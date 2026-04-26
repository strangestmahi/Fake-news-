from flask import Flask, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

app = Flask(__name__)

print("Server starting...")

client = chromadb.PersistentClient(path="db")
collection = client.get_or_create_collection("news")
model = SentenceTransformer('all-MiniLM-L6-v2')


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


def fetch_real_news(query):
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []
    try:
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
        response = requests.get(url).json()
        articles = response.get("articles", [])
        return [article["title"] for article in articles[:5]]
    except:
        return []


def get_llm_verdict(text, sources):
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
    You are a fake news detection system.

    Classification rules:
    - HIGH = Real / credible news
    - MEDIUM = Uncertain / partially true
    - LOW = Fake / misleading news

    News: {text}
    Related real news: {sources}

    Return ONLY valid JSON:
    {{
      "verdict": "high/medium/low",
      "score": number between 0-100,
      "explanation": "short explanation that matches the verdict"
    }}

    IMPORTANT:
    - If explanation says fake → verdict MUST be LOW
    - If explanation says real → verdict MUST be HIGH
    - Keep verdict and explanation consistent
    """

    chat = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )

    response = chat.choices[0].message.content

    try:
        return json.loads(response)
    except:
        return {
            "verdict": "medium",
            "score": 50,
            "explanation": response
        }


@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    text = data.get('text', '')

    query_emb = model.encode([text]).tolist()

    real_news = fetch_real_news(text)

    llm_result = get_llm_verdict(text, real_news)

    verdict = llm_result.get("verdict", "medium").lower()
    score = llm_result.get("score", 50)
    explanation = llm_result.get("explanation", "No explanation")

    exp_lower = explanation.lower()

    if "fake" in exp_lower or "misleading" in exp_lower:
        verdict = "low"
        score = min(score, 40)
    elif "real" in exp_lower or "credible" in exp_lower:
        verdict = "high"
        score = max(score, 60)

    return jsonify({
        "score": score,
        "verdict": verdict,
        "context": explanation,
        "summary": explanation,
        "sources": [
            {
                "title": news,
                "url": "https://news.google.com",
                "publisher": "News API",
                "date": "2026"
            } for news in real_news
        ]
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7860, debug=False)