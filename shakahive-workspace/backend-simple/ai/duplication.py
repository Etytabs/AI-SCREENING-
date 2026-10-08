"""
Duplication Checker - Real Fuzzy Matching
Identifies duplicate or highly similar proposals
"""

from typing import Dict, Any, List
import difflib
from rapidfuzz import fuzz, process

class DuplicationChecker:
    """Check for duplicate proposals using fuzzy matching"""
    
    def __init__(self):
        self.similarity_threshold = 0.7  # 70% similarity threshold
    
    def check(self, text: str, existing_apps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for duplicates against existing applications
        
        Args:
            text: Abstract text to check
            existing_apps: List of existing applications
            
        Returns:
            Dict with duplication check results
        """
        if not text or len(text) < 50:
            return {
                "is_duplicate": False,
                "similarity_score": 0,
                "matches": [],
                "status": "insufficient_content"
            }
        
        matches = []
        text_lower = text.lower()
        
        for app in existing_apps:
            app_abstract = app.get('abstract', '').lower()
            app_title = app.get('title', '').lower()
            
            if not app_abstract:
                continue
            
            # Calculate similarity using multiple methods
            # 1. Sequence matcher (overall similarity)
            seq_similarity = difflib.SequenceMatcher(None, text_lower, app_abstract).ratio()
            
            # 2. Fuzzy string matching (token similarity)
            fuzzy_similarity = fuzz.ratio(text_lower, app_abstract) / 100
            
            # 3. Title similarity
            title_similarity = fuzz.ratio(text_lower, app_title) / 100 if app_title else 0
            
            # Combined similarity score
            combined_similarity = (seq_similarity * 0.5 + fuzzy_similarity * 0.3 + title_similarity * 0.2)
            
            if combined_similarity > 0.4:  # Only include if > 40% similar
                matches.append({
                    "application_id": app.get('id'),
                    "title": app.get('title'),
                    "similarity_score": round(combined_similarity * 100, 2),
                    "abstract_similarity": round(seq_similarity * 100, 2),
                    "title_similarity": round(title_similarity * 100, 2),
                    "is_likely_duplicate": combined_similarity > self.similarity_threshold
                })
        
        # Sort by similarity score
        matches.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Determine if duplicate
        is_duplicate = any(m['is_likely_duplicate'] for m in matches)
        max_similarity = matches[0]['similarity_score'] if matches else 0
        
        # Status
        if is_duplicate:
            status = "duplicate_detected"
        elif max_similarity > 0.5:
            status = "highly_similar"
        elif max_similarity > 0.3:
            status = "somewhat_similar"
        else:
            status = "unique"
        
        return {
            "is_duplicate": is_duplicate,
            "similarity_score": round(max_similarity, 2),
            "matches": matches[:5],  # Top 5 matches
            "status": status,
            "total_compared": len(existing_apps)
        }
