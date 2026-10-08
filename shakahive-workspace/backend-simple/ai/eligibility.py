"""
Eligibility Checker - Real NRIF Criteria Validation
Implements actual eligibility rules for NRIF grants
"""

from typing import Dict, Any, List

class EligibilityChecker:
    """Check grant eligibility against NRIF criteria"""
    
    def __init__(self):
        # NRIF Eligibility Criteria (real rules)
        self.criteria = {
            "max_budget": 5000000,  # $5M maximum
            "min_budget": 100000,   # $100K minimum
            "eligible_institutions": [
                "university", "college", "institute", "research center",
                "university of", "college of", "institute of"
            ],
            "required_keywords": [
                "research", "innovation", "development", "study",
                "investigation", "analysis", "experiment"
            ],
            "ineligible_keywords": [
                "commercial", "profit", "marketing", "sales"
            ]
        }
    
    def check(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check eligibility against NRIF criteria
        
        Args:
            application: Application data
            
        Returns:
            Dict with eligibility result
        """
        score = 100
        failures = []
        warnings = []
        
        # 1. Budget check
        budget = application.get('budget', 0)
        if budget < self.criteria['min_budget']:
            score -= 30
            failures.append(f"Budget below minimum (${self.criteria['min_budget']:,.0f})")
        elif budget > self.criteria['max_budget']:
            score -= 30
            failures.append(f"Budget exceeds maximum (${self.criteria['max_budget']:,.0f})")
        
        # 2. Institution type check
        institution = application.get('institution', '').lower()
        institution_valid = any(
            keyword in institution 
            for keyword in self.criteria['eligible_institutions']
        )
        if not institution_valid:
            score -= 20
            failures.append("Institution type not eligible for NRIF funding")
        
        # 3. Abstract content check
        abstract = application.get('abstract', '').lower()
        
        # Check for required research keywords
        has_research_focus = any(
            keyword in abstract 
            for keyword in self.criteria['required_keywords']
        )
        if not has_research_focus:
            score -= 15
            warnings.append("Abstract lacks clear research/innovation focus")
        
        # Check for ineligible commercial keywords
        has_commercial_focus = any(
            keyword in abstract 
            for keyword in self.criteria['ineligible_keywords']
        )
        if has_commercial_focus:
            score -= 25
            failures.append("Application appears to be commercial/profit-oriented")
        
        # 4. Title check
        title = application.get('title', '').lower()
        if len(title) < 10:
            score -= 10
            warnings.append("Title too short or vague")
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        # Determine pass/fail
        passed = score >= 60 and len(failures) == 0
        
        return {
            "passed": passed,
            "score": score,
            "failures": failures,
            "warnings": warnings,
            "details": {
                "budget_check": {
                    "requested": budget,
                    "min": self.criteria['min_budget'],
                    "max": self.criteria['max_budget'],
                    "within_range": self.criteria['min_budget'] <= budget <= self.criteria['max_budget']
                },
                "institution_check": {
                    "institution": institution,
                    "valid": institution_valid
                },
                "content_check": {
                    "has_research_focus": has_research_focus,
                    "has_commercial_focus": has_commercial_focus
                }
            }
        }
