import type { Finding, SimilarityMatch } from "./types";

/**
 * Splits the matches the screening already produced into the two questions a reviewer
 * asks: is this the same as another submission (duplication), or is it taken from
 * something already published (plagiarism)?
 *
 * The text-similarity check compares against both, so its matches carry either kind.
 * This is a presentation split only - no score is recomputed and no match is dropped.
 */

export const INTERNAL_SOURCE_TYPES = new Set([
  "same_call_application",
  "historical_application",
  "funded_project",
]);

export const PUBLISHED_SOURCE_TYPE = "published_work";

export function isInternalMatch(match: SimilarityMatch): boolean {
  return INTERNAL_SOURCE_TYPES.has(match.source_type);
}

export function isPublishedMatch(match: SimilarityMatch): boolean {
  return match.source_type === PUBLISHED_SOURCE_TYPE;
}

function dedupe(matches: SimilarityMatch[]): SimilarityMatch[] {
  const seen = new Set<string>();
  const unique: SimilarityMatch[] = [];
  for (const match of matches) {
    // The same application can be matched by both checks; count it once.
    const key = match.application_id ?? match.record_id ?? match.match_id;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(match);
  }
  return unique;
}

/** Every duplication match, including those the text-similarity check found. */
export function duplicationMatches(findings: Finding[]): SimilarityMatch[] {
  const fromDuplication = findings.filter((f) => f.type === "duplication").flatMap((f) => f.matches);
  const fromTextSimilarity = findings
    .filter((f) => f.type === "plagiarism")
    .flatMap((f) => f.matches)
    .filter(isInternalMatch);
  return dedupe([...fromDuplication, ...fromTextSimilarity]);
}

/** Matches against published literature only. */
export function publishedMatches(findings: Finding[]): SimilarityMatch[] {
  return dedupe(
    findings.filter((f) => f.type === "plagiarism").flatMap((f) => f.matches).filter(isPublishedMatch),
  );
}

/** The strongest published-work overlap, as a percentage of this proposal. */
export function publishedSimilarity(findings: Finding[]): number | null {
  const scores = publishedMatches(findings).map((m) => m.similarity_score);
  return scores.length ? Math.max(...scores) * 100 : null;
}

/**
 * Duplication matches a duplication finding does not already carry, so the duplication
 * view can show the ones the text-similarity check contributed.
 */
export function extraDuplicationMatches(
  finding: Finding,
  siblings: Finding[] | undefined,
): SimilarityMatch[] {
  if (!siblings?.length) return [];
  const own = new Set(finding.matches.map((m) => m.application_id ?? m.record_id ?? m.match_id));
  return duplicationMatches(siblings).filter(
    (m) => !own.has(m.application_id ?? m.record_id ?? m.match_id),
  );
}
