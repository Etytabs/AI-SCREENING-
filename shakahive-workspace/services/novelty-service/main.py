from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shared.models import NoveltyResult, NoveltyScore

app = FastAPI(
    title="Novelty Assessment Service",
    description="GPU-accelerated novelty and innovation assessment",
    version="1.0.0"
)

# Global model variables
embedding_model = None
classifier_model = None
tokenizer = None
device = None

# Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class NoveltyRequest(BaseModel):
    """Request for novelty assessment"""
    application: Dict[str, Any]


def load_models():
    """Load ML models on GPU if available"""
    global embedding_model, classifier_model, tokenizer, device
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading models on device: {device}")
    
    # Load embedding model
    embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    print("Embedding model loaded")
    
    # Load a text classification model for novelty detection
    # Using a general-purpose model that can be fine-tuned
    try:
        model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        classifier_model = AutoModelForSequenceClassification.from_pretrained(model_name)
        classifier_model.to(device)
        print("Classifier model loaded")
    except Exception as e:
        print(f"Could not load classifier model: {e}")
        classifier_model = None


@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    load_models()


@app.get("/")
async def root():
    return {
        "service": "Novelty Assessment Service",
        "status": "operational",
        "device": device,
        "embedding_model": EMBEDDING_MODEL,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "device": device,
        "embedding_model_loaded": embedding_model is not None,
        "classifier_model_loaded": classifier_model is not None
    }


def generate_mock_similar_works() -> List[Dict[str, Any]]:
    """Generate mock similar works for demonstration"""
    return [
        {
            "title": "Machine Learning for Crop Disease Detection",
            "authors": ["Smith et al."],
            "year": 2022,
            "similarity": 0.75,
            "venue": "IEEE Transactions on Agriculture",
            "key_difference": "Our approach uses real-time sensor data integration"
        },
        {
            "title": "Deep Learning in Precision Agriculture",
            "authors": ["Johnson et al."],
            "year": 2023,
            "similarity": 0.68,
            "venue": "Nature Machine Intelligence",
            "key_difference": "Novel architecture for multi-modal data fusion"
        },
        {
            "title": "AI for Sustainable Farming in Africa",
            "authors": ["Kumar et al."],
            "year": 2021,
            "similarity": 0.62,
            "venue": "Agricultural Systems",
            "key_difference": "Focus on smallholder farmer accessibility"
        }
    ]


def assess_technical_novelty(text: str, similar_works: List[Dict]) -> float:
    """Assess technical novelty based on methodology and approach"""
    if embedding_model is None:
        return 0.5  # Default score if model not loaded
    
    # Keywords indicating technical novelty
    novelty_keywords = [
        "novel", "innovative", "breakthrough", "pioneering",
        "first-of-its-kind", "state-of-the-art", "cutting-edge",
        "new approach", "unique", "original", "groundbreaking"
    ]
    
    text_lower = text.lower()
    keyword_score = sum(1 for kw in novelty_keywords if kw in text_lower) / len(novelty_keywords)
    
    # Semantic diversity score
    sentences = text.split('.')
    if len(sentences) > 1:
        embeddings = embedding_model.encode(sentences[:10], convert_to_tensor=True)
        diversity = 1.0 - util.cos_sim(embeddings, embeddings).mean().item()
    else:
        diversity = 0.5
    
    # Combine scores
    technical_score = (keyword_score * 0.4) + (diversity * 0.6)
    return min(1.0, max(0.0, technical_score))


def assess_methodological_novelty(text: str) -> float:
    """Assess methodological novelty"""
    if embedding_model is None:
        return 0.5
    
    # Method keywords
    method_keywords = [
        "methodology", "approach", "framework", "algorithm",
        "technique", "procedure", "protocol", "strategy"
    ]
    
    text_lower = text.lower()
    method_mention = sum(1 for kw in method_keywords if kw in text_lower)
    
    # Check for specific method descriptions
    specific_indicators = [
        "we propose", "our method", "the approach involves",
        "we developed", "novel method", "unique approach"
    ]
    specific_score = sum(1 for ind in specific_indicators if ind in text_lower) / len(specific_indicators)
    
    method_score = (min(method_mention, 5) / 5) * 0.5 + specific_score * 0.5
    return min(1.0, max(0.0, method_score))


def assess_application_novelty(text: str) -> float:
    """Assess application/use-case novelty"""
    if embedding_model is None:
        return 0.5
    
    # Application keywords
    app_keywords = [
        "application", "use case", "implementation", "deployment",
        "real-world", "practical", "industry", "sector"
    ]
    
    text_lower = text.lower()
    app_mention = sum(1 for kw in app_keywords if kw in text_lower)
    
    # Check for specific application domains
    domain_keywords = [
        "healthcare", "agriculture", "education", "finance",
        "manufacturing", "transportation", "energy", "environment"
    ]
    domain_score = sum(1 for kw in domain_keywords if kw in text_lower) / len(domain_keywords)
    
    app_score = (min(app_mention, 5) / 5) * 0.5 + domain_score * 0.5
    return min(1.0, max(0.0, app_score))


def assess_market_novelty(text: str) -> float:
    """Assess market/commercial novelty"""
    if embedding_model is None:
        return 0.5
    
    # Market keywords
    market_keywords = [
        "market", "commercial", "business", "industry",
        "startup", "enterprise", "customer", "competitive"
    ]
    
    text_lower = text.lower()
    market_mention = sum(1 for kw in market_keywords if kw in text_lower)
    
    # Check for competitive analysis
    competitive_indicators = [
        "competitive advantage", "market gap", "unmet need",
        "market opportunity", "commercial potential"
    ]
    competitive_score = sum(1 for ind in competitive_indicators if ind in text_lower) / len(competitive_indicators)
    
    market_score = (min(market_mention, 5) / 5) * 0.5 + competitive_score * 0.5
    return min(1.0, max(0.0, market_score))


def identify_ip_considerations(text: str) -> List[str]:
    """Identify potential IP considerations"""
    considerations = []
    
    ip_keywords = {
        "patent": "Potential patentable invention",
        "copyright": "Copyrightable software or content",
        "trademark": "Potential trademark for brand/product",
        "trade secret": "Proprietary algorithms or processes",
        "license": "Open source or licensing considerations",
        "data": "Data ownership and privacy considerations"
    }
    
    text_lower = text.lower()
    for keyword, consideration in ip_keywords.items():
        if keyword in text_lower:
            considerations.append(consideration)
    
    return considerations


@app.post("/assess", response_model=NoveltyResult)
async def assess_novelty(request: NoveltyRequest):
    """Assess novelty and innovation of a proposal"""
    try:
        application = request.application
        
        # Extract text from application
        abstract = application.get("abstract", "")
        full_proposal = application.get("full_proposal", "")
        combined_text = f"{abstract} {full_proposal}"
        
        # Get similar works
        similar_works = generate_mock_similar_works()
        
        # Assess different novelty dimensions
        technical_novelty = assess_technical_novelty(combined_text, similar_works)
        methodological_novelty = assess_methodological_novelty(combined_text)
        application_novelty = assess_application_novelty(combined_text)
        market_novelty = assess_market_novelty(combined_text)
        
        # Calculate overall novelty score
        novelty_breakdown = NoveltyScore(
            technical_novelty=technical_novelty,
            methodological_novelty=methodological_novelty,
            application_novelty=application_novelty,
            market_novelty=market_novelty
        )
        
        overall_novelty_score = (
            technical_novelty * 0.3 +
            methodological_novelty * 0.3 +
            application_novelty * 0.2 +
            market_novelty * 0.2
        )
        
        # Determine if novel
        is_novel = overall_novelty_score >= 0.6
        
        # Determine innovation potential
        if overall_novelty_score >= 0.8:
            innovation_potential = "High - Breakthrough innovation"
        elif overall_novelty_score >= 0.6:
            innovation_potential = "Medium - Significant innovation"
        elif overall_novelty_score >= 0.4:
            innovation_potential = "Low - Incremental innovation"
        else:
            innovation_potential = "Minimal - Limited novelty"
        
        # Identify IP considerations
        ip_considerations = identify_ip_considerations(combined_text)
        
        return NoveltyResult(
            service_name="novelty",
            status="completed",
            score=overall_novelty_score,
            overall_novelty_score=overall_novelty_score,
            is_novel=is_novel,
            novelty_breakdown=novelty_breakdown,
            similar_works=similar_works,
            innovation_potential=innovation_potential,
            ip_considerations=ip_considerations,
            details={
                "device_used": device,
                "text_length": len(combined_text),
                "similar_works_analyzed": len(similar_works)
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-assess")
async def batch_assess_novelty(requests: List[NoveltyRequest]):
    """Batch novelty assessment for multiple applications"""
    results = []
    for req in requests:
        result = await assess_novelty(req)
        results.append(result)
    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
