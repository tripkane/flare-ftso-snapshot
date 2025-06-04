import glob
import json

from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI()

# Load a lightweight generation model
text_gen = pipeline("text-generation", model="gpt2")

# Gather snapshot data
snapshots = []
for path in sorted(glob.glob("docs/daily_snapshots/*.json")):
    with open(path) as f:
        snapshots.append(json.load(f))

# Keep context short to ensure fast inference
CONTEXT = json.dumps(snapshots)[:2000]

class Question(BaseModel):
    question: str

@app.post("/query")
def query(q: Question):
    prompt = (
        "Answer this question about the dataset:\n" + CONTEXT +
        f"\nQuestion: {q.question}\nAnswer:"
    )
    result = text_gen(prompt, max_length=len(prompt.split()) + 50, num_return_sequences=1)
    generated = result[0]["generated_text"]
    answer = generated[len(prompt):].strip()
    return {"answer": answer}
