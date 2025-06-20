import glob
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()

# Load a lightweight generation model
try:
    text_gen = pipeline("text-generation", model="gpt2")
except Exception as e:
    print(f"Error loading text-generation model: {e}")
    text_gen = None

# Gather snapshot data
snapshots = []
for path in sorted(glob.glob("docs/daily_snapshots/*.json")):
    if os.path.basename(path) == "manifest.json":
        continue
    try:
        with open(path) as f:
            snapshots.append(json.load(f))
    except Exception as e:
        print(f"Error loading snapshot file {path}: {e}")

# Keep context short to ensure fast inference
CONTEXT = json.dumps(snapshots)[:2000]

class Question(BaseModel):
    question: str

@app.post("/query")
def query(q: Question):
    if not text_gen:
        raise HTTPException(status_code=500, detail="Text generation model not loaded")

    prompt = (
        "Answer this question about the dataset:\n" + CONTEXT +
        f"\nQuestion: {q.question}\nAnswer:"
    )

    result = text_gen(prompt, max_length=len(prompt.split()) + 50, num_return_sequences=1)
    generated = result[0]["generated_text"]
    answer = generated[len(prompt):].strip()
    return {"answer": answer}

app.mount("/", StaticFiles(directory="docs", html=True), name="docs")


