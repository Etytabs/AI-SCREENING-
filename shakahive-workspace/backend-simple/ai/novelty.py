"""
Novelty Assessor - Real Innovation Scoring
Evaluates technical and methodological novelty using keyword analysis
"""

from typing import Dict, Any, List
import re

class NoveltyAssessor:
    """Assess novelty and innovation of research proposals"""
    
    def __init__(self):
        # Novelty indicators (keywords suggesting innovation)
        self.innovation_keywords = {
            "technical": [
                "novel", "innovative", "breakthrough", "pioneering", "cutting-edge",
                "state-of-the-art", "advanced", "new method", "new approach",
                "first", "original", "unique", "revolutionary", "paradigm shift",
                "groundbreaking", "unprecedented", "inventive", "creative"
            ],
            "methodological": [
                "new methodology", "novel approach", "innovative method",
                "unique framework", "new algorithm", "new technique",
                "experimental", "prototype", "pilot", "proof of concept",
                "new protocol", "new procedure", "new process"
            ],
            "application": [
                "new application", "novel use", "innovative application",
                "practical implementation", "real-world", "applied research",
                "deployment", "implementation", "commercialization potential",
                "scalable", "transferable", "adaptable"
            ],
            "market": [
                "market potential", "commercial potential", "economic impact",
                "industry impact", "societal impact", "user adoption",
                "competitive advantage", "market gap", "unmet need",
                "disruptive", "transformative", "game-changing"
            ]
        }
        
        # Common research areas (to assess domain novelty)
        self.research_domains = [
            "machine learning", "artificial intelligence", "deep learning",
            "quantum computing", "nanotechnology", "biotechnology",
            "renewable energy", "climate change", "genomics",
            "robotics", "blockchain", "internet of things", "5g",
            "neuroscience", "materials science", "synthetic biology"
        ]
    
    def assess(self, text: str) -> Dict[str, Any]:
        """
        Assess novelty of research proposal
        
        Args:
            text: Abstract text to assess
            
        Returns:
            Dict with novelty assessment
        """
        if not text or len(text) < 50:
            return {
                "overall_score": 0,
                "technical": 0,
                "methodological": 0,
                "application": 0,
                "market": 0,
                "status": "insufficient_content"
            }
        
        text_lower = text.lower()
        
        # Score each dimension
        scores = {}
        keyword_matches = {}
        
        for dimension, keywords in self.innovation_keywords.items():
            matches = []
            for keyword in keywords:
                if keyword in text_lower:
                    matches.append(keyword)
            
            # Score based on number of matches
            score = min(100, len(matches) * 15)
            scores[dimension] = score
            keyword_matches[dimension] = matches
        
        # Detect research domain
        detected_domains = []
        for domain in self.research_domains:
            if domain in text_lower:
                detected_domains.append(domain)
        
        # Bonus for domain novelty (emerging fields)
        domain_bonus = min(20, len(detected_domains) * 5)
        
        # Calculate overall score (weighted average)
        weights = {
            "technical": 0.35,
            "methodological": 0.25,
            "application": 0.25,
            "market": 0.15
        }
        
        overall_score = sum(
            scores[dim] * weights[dim] 
            for dim in scores
        ) + domain_bonus
        
        overall_score = min(100, overall_score)
        
        # Determine status
        if overall_score >= 80:
            status = "highly_novel"
        elif overall_score >= 60:
            status = "moderately_novel"
        elif overall_score >= 40:
            status = "somewhat_novel"
        else:
            status = "low_novelty"
        
        return {
            "overall_score": round(overall_score, 2),
            "technical": round(scores.get('technical', 0), 2),
            "methodological": round(scores.get('methodological', 0), 2),
            "application": round(scores.get('application', 0), 2),
            "market": round(scores.get('market', 0), 2),
            "status": status,
            "innovation_keywords_found": keyword_matches,
            "research_domains": detected_domains,
            "domain_bonus": domain_bonus
        }
