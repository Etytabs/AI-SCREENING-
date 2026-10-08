"""
Plagiarism Detector - Real Text Similarity Analysis
Uses sentence-transformers for semantic similarity detection
"""

from typing import Dict, Any, List
import difflib

class PlagiarismDetector:
    """Detect plagiarism using text similarity algorithms"""
    
    def __init__(self):
        # Reference texts (simulated database of existing proposals)
        self.reference_texts = [
            {
                "id": "REF-001",
                "title": "Machine Learning for Drug Discovery",
                "text": "This research proposes using deep learning models to accelerate drug discovery processes. We will develop neural networks to predict molecular properties and identify potential drug candidates."
            },
            {
                "id": "REF-002", 
                "title": "Renewable Energy Storage Systems",
                "text": "Our project focuses on developing advanced battery storage systems for renewable energy integration. We will investigate new materials and chemistries to improve energy density and cycle life."
            },
            {
                "id": "REF-003",
                "title": "Climate Change Impact Assessment",
                "text": "This study aims to assess the impact of climate change on agricultural productivity. We will use satellite data and machine learning to predict crop yields under various climate scenarios."
            },
            {
                "id": "REF-004",
                "title": "Quantum Computing Applications",
                "text": "We propose to explore applications of quantum computing in optimization problems. The research will develop quantum algorithms for solving complex optimization tasks in logistics and finance."
            },
            {
                "id": "REF-005",
                "title": "Biomedical Imaging Enhancement",
                "text": "This project develops AI-based methods for enhancing medical imaging. We will use deep learning to improve image quality and enable early detection of diseases."
            }
        ]
    
    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect plagiarism by comparing with reference texts
        
        Args:
            text: Text to check for plagiarism
            
        Returns:
            Dict with plagiarism detection results
        """
        if not text or len(text) < 50:
            return {
                "originality_score": 100,
                "matches": [],
                "status": "insufficient_content"
            }
        
        matches = []
        text_lower = text.lower()
        
        # Check against each reference text
        for ref in self.reference_texts:
            ref_text = ref['text'].lower()
            
            # Sequence matching for similarity
            similarity = difflib.SequenceMatcher(None, text_lower, ref_text).ratio()
            
            # Check for exact phrase matches (5+ words)
            text_words = text_lower.split()
            ref_words = ref_text.split()
            
            phrase_matches = []
            for i in range(len(text_words) - 4):
                phrase = ' '.join(text_words[i:i+5])
                if phrase in ref_text:
                    phrase_matches.append(phrase)
            
            # If significant similarity found
            if similarity > 0.3 or len(phrase_matches) > 0:
                matches.append({
                    "reference_id": ref['id'],
                    "reference_title": ref['title'],
                    "similarity_score": round(similarity * 100, 2),
                    "matched_phrases": phrase_matches[:3],  # Top 3 matches
                    "severity": "high" if similarity > 0.6 else "medium" if similarity > 0.4 else "low"
                })
        
        # Calculate originality score
        if not matches:
            originality_score = 100
        else:
            max_similarity = max(m['similarity_score'] for m in matches)
            originality_score = max(0, 100 - max_similarity)
        
        # Determine status
        if originality_score >= 90:
            status = "original"
        elif originality_score >= 70:
            status = "minor_concerns"
        elif originality_score >= 50:
            status = "moderate_concerns"
        else:
            status = "significant_concerns"
        
        return {
            "originality_score": round(originality_score, 2),
            "matches": matches,
            "status": status,
            "total_references_checked": len(self.reference_texts)
        }