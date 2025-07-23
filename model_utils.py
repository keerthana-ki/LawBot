from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import torch
import ast
import re

# Zero-shot classification model
classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
)

# Sentence transformer model
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Summarization model
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=0 if torch.cuda.is_available() else -1
)

# Case labels
case_labels = ["criminal", "civil", "corporate", "family", "labor", "property", "constitutional"]

# Load and preprocess IPC dataset
ipc_df = pd.read_csv("ipc_offenses_with_keywords_tfidf.csv")
ipc_df = ipc_df[["Section", "Offense", "Top Keywords"]]
ipc_df["Top Keywords"] = ipc_df["Top Keywords"].apply(ast.literal_eval)
ipc_df["combined_text"] = ipc_df.apply(
    lambda row: f"{row['Offense']}. Keywords: {', '.join(row['Top Keywords'])}", axis=1
)
ipc_embeddings = embedding_model.encode(ipc_df["combined_text"].tolist(), convert_to_tensor=True)

def preprocess_text(text: str) -> str:
    """Clean legal text before processing"""
    text = ' '.join(text.split())
    text = re.sub(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', 'DATE', text)
    text = re.sub(r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b', 'DATE', text)
    text = re.sub(r'\b(\d{1,2} \w+ \d{4})\b', 'DATE', text)
    text = re.sub(r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b', 'DATE', text)
    text = re.sub(r'\b(?:Case Number|Date|Time|Location)\b.*?[\n.]', '', text)
    return text

def generate_summary(text: str, max_chunk: int = 800) -> str:
    """Generate legal case summary"""
    clean_text = preprocess_text(text)
    chunks = [clean_text[i:i+max_chunk] for i in range(0, len(clean_text), max_chunk)]
    summary = ""
    for chunk in chunks:
        result = summarizer(chunk, do_sample=False)
        summary += result[0]['summary_text'] + " "
    return summary.strip()

def classify_case(text: str):
    """Classify case type"""
    result = classifier(text, candidate_labels=case_labels, multi_label=True)
    top_label = result["labels"][0]
    scores = dict(zip(result["labels"], result["scores"]))
    return top_label, scores

def get_similar_ipc_sections(text: str, top_k: int = 5):
    """Find relevant IPC sections"""
    query_embedding = embedding_model.encode(text, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(query_embedding, ipc_embeddings)[0]
    top_results = torch.topk(cosine_scores, k=top_k)

    results = []
    for idx in top_results.indices:
        section = ipc_df.iloc[idx.item()]["Section"]
        desc = ipc_df.iloc[idx.item()]["combined_text"]
        results.append(f"{section}: {desc}")

    return results