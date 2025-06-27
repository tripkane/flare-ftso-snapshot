import glob
import json
import os
import logging
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from transformers import pipeline
from pydantic import ValidationError

from schemas import QueryRequest, sanitize_file_path
from exceptions import ConfigurationError, FileOperationError, WebScrapingError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Load a lightweight generation model
try:
    text_gen = pipeline("text-generation", model="gpt2")
    logger.info("Text generation model loaded successfully")
except Exception as e:
    logger.error(f"Error loading text-generation model: {e}")
    text_gen = None


def load_snapshots_safely() -> List[Dict[str, Any]]:
    """Load snapshot data with proper error handling and path validation."""
    snapshots = []
    
    try:
        # Use path validation to prevent directory traversal
        docs_path = sanitize_file_path("docs/daily_snapshots")
        pattern = os.path.join(docs_path, "*.json")
        
        for path in sorted(glob.glob(pattern)):
            filename = os.path.basename(path)
            
            # Skip manifest files
            if filename == "manifest.json":
                continue
                
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    snapshots.append(data)
                    
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Error loading snapshot file {path}: {e}")
                raise FileOperationError(f"Failed to load snapshot file", file_path=path)
            except Exception as e:
                logger.error(f"Unexpected error loading {path}: {e}")
                
    except Exception as e:
        logger.error(f"Error loading snapshots: {e}")
        raise FileOperationError("Failed to load snapshot data")
    
    logger.info(f"Loaded {len(snapshots)} snapshot files")
    return snapshots


# Load snapshots on startup
try:
    snapshots = load_snapshots_safely()
    # Keep context short to ensure fast inference
    CONTEXT = json.dumps(snapshots)[:2000]
    logger.info(f"Context prepared with {len(CONTEXT)} characters")
except Exception as e:
    logger.error(f"Failed to load snapshots on startup: {e}")
    CONTEXT = "No snapshot data available"
    snapshots = []


@app.post("/query")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def query(request: Request, q: QueryRequest):
    """
    Process LLM query with rate limiting and input validation.
    
    Args:
        request: FastAPI request object (for rate limiting)
        q: Validated query request
        
    Returns:
        Dict with generated answer
        
    Raises:
        HTTPException: For various error conditions
    """
    if not text_gen:
        logger.error("Query attempted but text generation model not available")
        raise HTTPException(
            status_code=503, 
            detail="Text generation service unavailable"
        )

    try:
        # Construct prompt with sanitized input
        prompt = (
            "Answer this question about the FTSO dataset:\n" + 
            CONTEXT[:q.context_limit] +
            f"\nQuestion: {q.query}\nAnswer:"
        )
        
        # Generate response with limits
        result = text_gen(
            prompt, 
            max_length=len(prompt.split()) + 50, 
            num_return_sequences=1,
            do_sample=True,
            temperature=0.7,
            pad_token_id=text_gen.tokenizer.eos_token_id
        )
        
        generated = result[0]["generated_text"]
        answer = generated[len(prompt):].strip()
        
        # Log successful query (without sensitive data)
        logger.info(f"Query processed successfully, response length: {len(answer)}")
        
        return {"answer": answer}
        
    except ValidationError as e:
        logger.warning(f"Validation error in query: {e}")
        raise HTTPException(status_code=400, detail="Invalid query format")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error processing query"
        )

app.mount("/", StaticFiles(directory="docs", html=True), name="docs")


