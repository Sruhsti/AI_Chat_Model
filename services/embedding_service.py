from sentence_transformers import SentenceTransformer
import numpy as np
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str) -> list[float]:
    return model.encode(text).tolist()

def get_embeddings(texts: list[str]) -> list[list[float]]:
    return model.encode(texts).tolist()

def embeddings_to_str(embeddings: list[float]) -> str:
    return json.dumps(embeddings)


def str_to_embeddings(embedding_str: str) -> np.ndarray:
    return np.array(json.loads(embedding_str))

def cossine_similarity(a,b):
    return np.dot(a,b)/(np.linalg.norm(a) * np.linalg.norm(b))

def find_similar_chunks(
    query: str, 
    chunks_with_embeddings: list[tuple], 
    top_k: int = 3
) -> list[str]:
    
    query_embeddings = model.encode(query)
    scores = []
    for chunk, emb in chunks_with_embeddings:
        emb_array = str_to_embeddings(emb)
        score = cossine_similarity(query_embeddings,emb_array)
        scores.append((chunk,score))

    scores.sort(key=lambda x:x[1], reverse=True)
    return [ chunk for chunk, _ in scores[:top_k]]


