"""
AI Modules for NOVARAai
Real AI capabilities for grant screening
"""

from .eligibility import EligibilityChecker
from .plagiarism import PlagiarismDetector
from .duplication import DuplicationChecker
from .novelty import NoveltyAssessor
from .document_extractor import DocumentExtractor

__all__ = [
    'EligibilityChecker',
    'PlagiarismDetector',
    'DuplicationChecker',
    'NoveltyAssessor',
    'DocumentExtractor'
]
