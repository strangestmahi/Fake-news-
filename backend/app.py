from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

print("Server starting...")

#  load vector DB 
client = chromadb.PersistentClient(path="db")
collection = client.get_or_create_collection("news")
model = SentenceTransformer('all-MiniLM-L6-v2')


#  fetch real news 
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


def is_obviously_fake(text):
    keywords = [
        "alien", "aliens", "ghost", "zombie",
        "time travel", "immortal", "flying humans",
        "dragon", "superpower"
    ]
    text = text.lower()
    return any(word in text for word in keywords)


def is_uncertain(text):
    keywords = ["will", "going to", "prediction", "future", "soon"]
    text = text.lower()
    return any(word in text for word in keywords)


# placeholder for LLM 
def generate_explanation(text, sources):
    prompt = f"""
    Analyze the following news and determine whether it is real or fake.

    News:
    {text}

    Related real news:
    {sources}

    Give a short and clear explanation.
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma:2b",
                "prompt": prompt,
                "stream": False
            }
        )
        result = response.json()
        return result.get("response", "No explanation generated.")
    except Exception as e:
        return f"Error generating explanation: {str(e)}"


@app.route('/api/check', methods=['POST'])
def check():
    data = request.get_json()
    text = data.get('text', '')

    #  vector search
    query_emb = model.encode([text]).tolist()

    if collection.count() == 0:
        similar_meta = []
    else:
        results = collection.query(
            query_embeddings=query_emb,
            n_results=3
        )
        similar_meta = results['metadatas'][0]

    #  logic
    if is_obviously_fake(text):
        verdict = "low"
        score = 10
    elif is_uncertain(text):
        verdict = "medium"
        score = 50
    else:
        fake_count = sum(1 for m in similar_meta if m["label"] == "FAKE")
        if fake_count == 3:
            verdict = "low"
            score = 30
        elif fake_count == 2:
            verdict = "medium"
            score = 50
        else:
            verdict = "high"
            score = 80

    # real-time sources
    real_news = fetch_real_news(text)

    # LLM placeholder
    explanation = generate_explanation(text, real_news)

    return jsonify({
        "score": score,
        "verdict": verdict,
        "context": explanation,
        "summary": explanation,
        "sources": [
            {
                "title": news,
                "url": "live news",
                "publisher": "News API",
                "date": "2026"
            } for news in real_news
        ]
    })


if __name__ == '__main__':
    app.run(port=5000, debug=True)