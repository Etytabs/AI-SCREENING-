import os

# The plagiarism check queries OpenAlex when a key or polite-pool address is configured.
# Tests must stay hermetic, so the live lookup is off unless a test opts in explicitly.
os.environ.setdefault("AI_SCREENING_OPENALEX_ENABLED", "false")

# apps.api.main reads .env at import, so pin the seed too: tests must not depend
# on whether a developer has demo seeding switched on locally.
os.environ.setdefault("AI_SCREENING_DEMO_SEED", "true")
