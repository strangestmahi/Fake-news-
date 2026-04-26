from flask import Flask, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

print("Server starting...")

# load vector DB 
client = chromadb.PersistentClient(path="db")
collection = client.get_or_create_collection("news")
model = SentenceTransformer('all-MiniLM-L6-v2')


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


# fetch real news 
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


def generate_explanation(text, sources):
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""
    Analyze the following news and determine whether it is real or fake.
    News: {text}
    Related real news: {sources}
    Give a short and clear explanation.
    """
    chat = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    return chat.choices[0].message.content


@app.route('/api/check', methods=['POST', 'OPTIONS'])
def check():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    text = data.get('text', '')

    query_emb = model.encode([text]).tolist()

    if collection.count() == 0:
        similar_meta = []
    else:
        results = collection.query(
            query_embeddings=query_emb,
            n_results=3
        )
        similar_meta = results['metadatas'][0]

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

    real_news = fetch_real_news(text)
    explanation = generate_explanation(text, real_news)

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
    app.run(port=5000, debug=True)