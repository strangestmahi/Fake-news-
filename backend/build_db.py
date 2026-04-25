import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd

print("Building vector database")

client = chromadb.PersistentClient(path="db")

collection = client.get_or_create_collection("news")
model = SentenceTransformer('all-MiniLM-L6-v2')

fake_df = pd.read_csv("Fake.csv")
true_df = pd.read_csv("True.csv")

print(fake_df.columns)
print(true_df.columns)

fake_df["label"] = "FAKE"
true_df["label"] = "TRUE"

df = pd.concat([fake_df, true_df]).sample(2000)

docs = df["text"].tolist()
labels = df["label"].tolist()

print("Generating embeddings...")

embeddings = model.encode(docs).tolist()

collection.add(
    documents=docs,
    embeddings=embeddings,
    ids=[str(i) for i in range(len(docs))],
    metadatas=[{"label": label} for label in labels]
)


print("Vector DB built and saved successfully!")