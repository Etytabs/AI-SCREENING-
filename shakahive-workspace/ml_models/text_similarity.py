"""
Text Similarity Module
Provides various methods for computing text similarity
"""

import numpy as np
from typing import List, Tuple, Dict, Any
from sentence_transformers import SentenceTransformer, util
from difflib import SequenceMatcher
from rapidfuzz import fuzz, ratio
import re


class TextSimilarity:
    """Computes various text similarity metrics"""
    
    def __init__(self, model: SentenceTransformer = None, device: str = "cpu"):
        self.model = model
        self.device = device
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for comparison"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Convert to lowercase
        text = text.lower()
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s\.,!?;:]', '', text)
        return text.strip()
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def cosine_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity using embeddings"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        embedding1 = self.model.encode(text1, convert_to_tensor=True)
        embedding2 = self.model.encode(text2, convert_to_tensor=True)
        
        similarity = util.cos_sim(embedding1, embedding2).item()
        return similarity
    
    def batch_cosine_similarity(
        self,
        texts1: List[str],
        texts2: List[str]
    ) -> np.ndarray:
        """Compute batch cosine similarity"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        embeddings1 = self.model.encode(texts1, convert_to_tensor=True)
        embeddings2 = self.model.encode(texts2, convert_to_tensor=True)
        
        similarity_matrix = util.cos_sim(embeddings1, embeddings2)
        return similarity_matrix.cpu().numpy()
    
    def sequence_similarity(self, text1: str, text2: str) -> float:
        """Compute sequence similarity (faster, less accurate)"""
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Compute fuzzy similarity using rapidfuzz"""
        return fuzz.ratio(text1, text2) / 100.0
    
    def token_similarity(self, text1: str, text2: str) -> float:
        """Compute token overlap similarity"""
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
    
    def jaccard_similarity(self, text1: str, text2: str, ngram_size: int = 3) -> float:
        """Compute Jaccard similarity using n-grams"""
        def get_ngrams(text, n):
            words = text.lower().split()
            ngrams = []
            for i in range(len(words) - n + 1):
                ngrams.append(' '.join(words[i:i+n]))
            return set(ngrams)
        
        ngrams1 = get_ngrams(text1, ngram_size)
        ngrams2 = get_ngrams(text2, ngram_size)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = ngrams1.intersection(ngrams2)
        union = ngrams1.union(ngrams2)
        
        return len(intersection) / len(union)
    
    def find_similar_sentences(
        self,
        text1: str,
        text2: str,
        threshold: float = 0.8
    ) -> List[Tuple[str, str, float]]:
        """Find similar sentence pairs between two texts"""
        sentences1 = self.split_into_sentences(text1)
        sentences2 = self.split_into_sentences(text2)
        
        similar_pairs = []
        
        if self.model is not None:
            # Use embedding-based similarity
            for i, sent1 in enumerate(sentences1):
                for j, sent2 in enumerate(sentences2):
                    similarity = self.cosine_similarity(sent1, sent2)
                    if similarity >= threshold:
                        similar_pairs.append((sent1, sent2, similarity))
        else:
            # Use sequence similarity as fallback
            for i, sent1 in enumerate(sentences1):
                for j, sent2 in enumerate(sentences2):
                    similarity = self.sequence_similarity(sent1, sent2)
                    if similarity >= threshold:
                        similar_pairs.append((sent1, sent2, similarity))
        
        # Sort by similarity (descending)
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs
    
    def compute_comprehensive_similarity(
        self,
        text1: str,
        text2: str,
        weights: Dict[str, float] = None
    ) -> Dict[str, float]:
        """Compute comprehensive similarity using multiple methods"""
        if weights is None:
            weights = {
                "cosine": 0.4,
                "sequence": 0.2,
                "fuzzy": 0.2,
                "token": 0.1,
                "jaccard": 0.1
            }
        
        similarities = {}
        
        if self.model is not None:
            similarities["cosine"] = self.cosine_similarity(text1, text2)
        
        similarities["sequence"] = self.sequence_similarity(text1, text2)
        similarities["fuzzy"] = self.fuzzy_similarity(text1, text2)
        similarities["token"] = self.token_similarity(text1, text2)
        similarities["jaccard"] = self.jaccard_similarity(text1, text2)
        
        # Compute weighted average
        weighted_sum = sum(similarities[key] * weights.get(key, 0) for key in similarities)
        total_weight = sum(weights.get(key, 0) for key in similarities)
        
        similarities["overall"] = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        return similarities


class PlagiarismDetector:
    """Detects potential plagiarism using multiple similarity methods"""
    
    def __init__(self, similarity_calculator: TextSimilarity):
        self.similarity = similarity_calculator
        self.threshold = 0.75
    
    def detect_plagiarism(
        self,
        text: str,
        reference_texts: List[str],
        threshold: float = None
    ) -> Dict[str, Any]:
        """Detect plagiarism against reference texts"""
        if threshold is None:
            threshold = self.threshold
        
        results = {
            "overall_similarity": 0.0,
            "is_plagiarized": False,
            "matches": [],
            "flagged_sections": []
        }
        
        for ref_text in reference_texts:
            # Compute comprehensive similarity
            similarities = self.similarity.compute_comprehensive_similarity(
                text,
                ref_text
            )
            
            # Update overall similarity
            results["overall_similarity"] = max(
                results["overall_similarity"],
                similarities["overall"]
            )
            
            # Find similar sentences
            similar_sentences = self.similarity.find_similar_sentences(
                text,
                ref_text,
                threshold=threshold
            )
            
            for sent1, sent2, sim in similar_sentences:
                results["matches"].append({
                    "source_text": sent2,
                    "matched_text": sent1,
                    "similarity": sim
                })
                results["flagged_sections"].append(sent1)
        
        results["is_plagiarized"] = results["overall_similarity"] >= threshold
        
        return results


if __name__ == "__main__":
    # Test text similarity
    from ml_models.gpu_accelerator import get_model_manager
    
    accelerator = get_model_manager().accelerator
    model = get_model_manager().load_sentence_transformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        "test"
    )
    
    similarity_calc = TextSimilarity(model, accelerator.get_device())
    
    text1 = "This is a test sentence about machine learning."
    text2 = "This is another sentence about machine learning."
    
    similarities = similarity_calc.compute_comprehensive_similarity(text1, text2)
    print(f"Similarities: {similarities}")
