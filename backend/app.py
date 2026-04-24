from flask import Flask, request, jsonify 
from flask_cors import CORS 
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import requests 


def fetch_real_news(query):
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey=cf3503b586934eeb8e7c3778eb274cd3"
    response = requests.get(url).json()

    articles = response.get("articles", [])
    return [article["title"] for article in articles[:5]]

def is_obv_fake(text):
    keywords = ["aliens", "ghost", "time travel", "immortal", "zombie"]
    text = text.lower()
    return any(word in text for word in keywords)

def is_uncertain(text):
    keywords = ["will happen", "going to", "prediction", "future", "soon"]
    text = text.lower()

    import re
    if re.search(r"\b20[2-3][0-9]\b", text):
        return True 
    return any(word in text for word in keywords)

def llm_generate(prompt):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

    response = requests.post(
        API_URL, 
        headers=headers,
        json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 100,
                "temperature": 0.7
            }
            }
        )

    if response.status_code != 200:
        print("HF ERROR :", response.text)
        return "AI Unavailable"
    
    try:
        result = response.json()
    except:
        return "AI Unavailable"

    if isinstance(result, list):
        return result[0]["generated_text"]
    else:
        return "AI Unavailable"

app = Flask(__name__)
CORS(app)

print("Server starting...")

# db setup
client = chromadb.Client()
collection = client.create_collection("news")

model = SentenceTransformer('all-MiniLM-L6-v2')


fake_df = pd.read_csv("Fake.csv")
true_df = pd.read_csv("True.csv")

fake_df["label"] = "FAKE"
true_df["label"] = "REAL"

df = pd.concat([fake_df, true_df])
df = df.sample(200)

docs = df["text"].tolist()
labels = df["label"].tolist()

embeddings = model.encode(docs).tolist()

collection.add(
    documents=docs,
    embeddings=embeddings,
    ids=[str(i) for i in range(len(docs))],
    metadatas=[{"label": label} for label in labels]
)

@app.route('/api/check', methods=['POST'])
def check():
    data = request.get_json()
    text = data.get('text', '')

    query_emb = model.encode([text]).tolist()

    results = collection.query(
        query_embeddings=query_emb,
        n_results=3
    )

    similar_docs = results['documents'][0]
    similar_meta = results['metadatas'][0]
    real_news = fetch_real_news(text)
    all_sources = similar_docs + real_news 

    fake_count = sum(1 for m in similar_meta if m["label"] == "FAKE")

    if is_obv_fake(text):
        verdict = "low"
        score = 10
    elif is_uncertain(text):
        verdict = "medium"
        score = 50
    
    else:
        fake_count = sum(1 for m in similar_meta if m["label"] == "FAKE")

        if fake_count >=2:
            verdict = "low"
            score = 30
        else:
            verdict = "high"
            score = 80

    prompt = f"""
    You are an expert fact checker.
    Analyze the news and determine if it is real, fake, or uncertain.

    News: {text}

    If the claim is unrealistic, scientifically impossible, or lacks credibility, clearly say it is likely fake.

    Similar articles: {all_sources}

    Explain clearly in 2-3 sentences whether this news is real or fake and why.    
    """

    if verdict == "medium":
        llm_response = (
            "This claim refers to a future or uncertain event. There is no verified evidence" 
            "to confirm it at this time, so it should be treated with caution."
        )
    else:
        llm_response = llm_generate(prompt)

    if "AI Unavailable" in llm_response or len(llm_response) < 20:
        if verdict == "low":
            llm_response = " AI Analysis:\nThis claim appears misleading based on known misinformation patterns."
        else:
            llm_response = " AI Analysis:\nThis news appears credible based on similar verified reports."

    return jsonify({
        "score": score,
        "verdict": verdict,
        "context": llm_response,
        "summary": llm_response,
        "sources": [
            {
                "title": fetch_real_news,
                "url": "https://example.com",
                "publisher": "Dataset Source",
                "date": "2025-01-01"
            } for doc in similar_docs
        ]
    })


if __name__ == '__main__':
    app.run(port=5000, debug=False)