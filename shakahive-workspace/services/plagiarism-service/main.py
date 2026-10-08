from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util
from difflib import SequenceMatcher
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import PlagiarismResult, PlagiarismMatch

app = FastAPI(
    title="Plagiarism Detection Service",
    description="GPU-accelerated plagiarism detection using transformers",
    version="1.0.0"
)

# Global model variable
model = None
device = None

# Configuration
PLAGIARISM_THRESHOLD = float(os.getenv("PLAGIARISM_THRESHOLD", "0.75"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


class PlagiarismRequest(BaseModel):
    """Request for plagiarism detection"""
    application: Dict[str, Any]
    threshold: Optional[float] = PLAGIARISM_THRESHOLD


def load_model():
    """Load the sentence transformer model on GPU if available"""
    global model, device
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading model on device: {device}")
    
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    print("Model loaded successfully")


@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    load_model()


@app.get("/")
async def root():
    return {
        "service": "Plagiarism Detection Service",
        "status": "operational",
        "device": device,
        "model": EMBEDDING_MODEL,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "device": device,
        "model_loaded": model is not None
    }


def preprocess_text(text: str) -> str:
    """Preprocess text for comparison"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Convert to lowercase
    text = text.lower()
    # Remove special characters but keep sentence structure
    text = re.sub(r'[^\w\s\.,!?;:]', '', text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def detect_plagiarism_with_embeddings(
    text1: str,
    text2: str,
    threshold: float
) -> tuple[float, List[PlagiarismMatch]]:
    """Detect plagiarism using sentence embeddings"""
    
    # Split into sentences
    sentences1 = split_into_sentences(text1)
    sentences2 = split_into_sentences(text2)
    
    if not sentences1 or not sentences2:
        return 0.0, []
    
    # Encode sentences
    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)
    
    # Compute cosine similarity
    similarity_matrix = util.cos_sim(embeddings1, embeddings2)
    
    matches = []
    total_similarity = 0.0
    match_count = 0
    
    for i, sent1 in enumerate(sentences1):
        for j, sent2 in enumerate(sentences2):
            similarity = similarity_matrix[i][j].item()
            
            if similarity >= threshold:
                matches.append(PlagiarismMatch(
                    source_text=sent2,
                    matched_text=sent1,
                    similarity_score=similarity,
                    source_document="reference_database",
                    start_position=i,
                    end_position=i
                ))
                total_similarity += similarity
                match_count += 1
    
    overall_similarity = total_similarity / match_count if match_count > 0 else 0.0
    
    return overall_similarity, matches


def detect_plagiarism_sequence_matcher(
    text1: str,
    text2: str,
    threshold: float
) -> tuple[float, List[PlagiarismMatch]]:
    """Detect plagiarism using sequence matching (faster, less accurate)"""
    
    matcher = SequenceMatcher(None, text1, text2)
    similarity = matcher.ratio()
    
    matches = []
    if similarity >= threshold:
        # Find matching blocks
        for block in matcher.get_matching_blocks():
            if block.size > 20:  # Only consider substantial matches
                matched_text = text1[block.a:block.a + block.size]
                source_text = text2[block.b:block.b + block.size]
                
                matches.append(PlagiarismMatch(
                    source_text=source_text[:200],  # Truncate for display
                    matched_text=matched_text[:200],
                    similarity_score=similarity,
                    source_document="reference_database",
                    start_position=block.a,
                    end_position=block.a + block.size
                ))
    
    return similarity, matches


def generate_mock_reference_texts() -> List[str]:
    """Generate mock reference texts for demonstration"""
    # In production, this would query a database of published papers
    return [
        "This research aims to develop innovative solutions for sustainable agriculture in Rwanda.",
        "The proposed methodology includes machine learning algorithms for crop disease detection.",
        "Our approach leverages deep learning techniques to analyze satellite imagery for precision farming.",
        "The project focuses on improving food security through technological interventions.",
        "We propose a novel framework for integrating IoT sensors in agricultural monitoring systems."
    ]


@app.post("/detect", response_model=PlagiarismResult)
async def detect_plagiarism(request: PlagiarismRequest):
    """Detect plagiarism in a grant application"""
    try:
        application = request.application
        threshold = request.threshold or PLAGIARISM_THRESHOLD
        
        # Extract text from application
        abstract = application.get("abstract", "")
        full_proposal = application.get("full_proposal", "")
        combined_text = f"{abstract} {full_proposal}"
        
        # Preprocess
        combined_text = preprocess_text(combined_text)
        
        if len(combined_text) < 50:
            return PlagiarismResult(
                service_name="plagiarism",
                status="completed",
                overall_similarity=0.0,
                is_plagiarized=False,
                matches=[],
                flagged_sections=[],
                originality_score=100.0,
                timestamp=datetime.utcnow()
            )
        
        # Get reference texts (in production, query database)
        reference_texts = generate_mock_reference_texts()
        
        # Detect plagiarism using embeddings (GPU-accelerated)
        all_matches = []
        total_similarity = 0.0
        flagged_sections = []
        
        for ref_text in reference_texts:
            ref_text = preprocess_text(ref_text)
            similarity, matches = detect_plagiarism_with_embeddings(
                combined_text,
                ref_text,
                threshold
            )
            
            if similarity > 0:
                total_similarity = max(total_similarity, similarity)
                all_matches.extend(matches)
        
        # If no GPU or model not loaded, use sequence matcher as fallback
        if model is None or total_similarity == 0.0:
            for ref_text in reference_texts:
                ref_text = preprocess_text(ref_text)
                similarity, matches = detect_plagiarism_sequence_matcher(
                    combined_text,
                    ref_text,
                    threshold
                )
                total_similarity = max(total_similarity, similarity)
                all_matches.extend(matches)
        
        # Determine if plagiarized
        is_plagiarized = total_similarity >= threshold
        
        # Extract flagged sections
        flagged_sections = [match.matched_text for match in all_matches[:10]]
        
        # Calculate originality score
        originality_score = max(0.0, 100.0 - (total_similarity * 100))
        
        return PlagiarismResult(
            service_name="plagiarism",
            status="completed",
            overall_similarity=total_similarity,
            is_plagiarized=is_plagiarized,
            matches=all_matches[:20],  # Limit to top 20 matches
            flagged_sections=flagged_sections,
            originality_score=originality_score,
            details={
                "threshold_used": threshold,
                "reference_texts_checked": len(reference_texts),
                "device_used": device,
                "total_matches": len(all_matches)
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-detect")
async def batch_detect_plagiarism(requests: List[PlagiarismRequest]):
    """Batch plagiarism detection for multiple applications"""
    results = []
    for req in requests:
        result = await detect_plagiarism(req)
        results.append(result)
    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
