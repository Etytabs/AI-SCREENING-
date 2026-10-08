# Shared utilities and models for NOVARAai
# Enhanced with OpenAlex integration for research data validation and accuracy

from .models import (
    ApplicationStatus,
    ScreeningResult,
    EligibilityCriteria,
    EligibilityResult,
    PlagiarismMatch,
    PlagiarismResult,
    DuplicateProposal,
    DuplicationResult,
    NoveltyScore,
    NoveltyResult,
    ScreeningReport,
    GrantApplication,
    ScreeningRequest
)

from .database import (
    get_db,
    init_db,
    GrantApplicationDB,
    ScreeningReportDB,
    HistoricalProposalDB,
    ResearcherIdentityDB,
    TenantIdentityLinkDB,
    IdentityConflictDB
)

__all__ = [
    # Models
    'ApplicationStatus',
    'ScreeningResult',
    'EligibilityCriteria',
    'EligibilityResult',
    'PlagiarismMatch',
    'PlagiarismResult',
    'DuplicateProposal',
    'DuplicationResult',
    'NoveltyScore',
    'NoveltyResult',
    'ScreeningReport',
    'GrantApplication',
    'ScreeningRequest',
    # Database
    'get_db',
    'init_db',
    'GrantApplicationDB',
    'ScreeningReportDB',
    'HistoricalProposalDB',
    'ResearcherIdentityDB',
    'TenantIdentityLinkDB',
    'IdentityConflictDB'
]
