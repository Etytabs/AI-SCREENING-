"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CheckCircle, XCircle, AlertCircle, Clock, FileText, ExternalLink, AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useRouter } from "next/navigation";
import { getLocalApplications, LocalApplication, registerLocalResearcher, updateLocalApplication } from "@/lib/local-workspace";

type Recommendation = {
  decision: "approve" | "reject" | "review";
  reason: string;
};

interface ScreeningResult {
  application_id: string;
  title: string;
  eligibility: { passed: boolean; score: number; details: any; failures: string[]; warnings: string[] };
  plagiarism: { originality_score: number | null; matches: any[]; status: string };
  duplication: { is_duplicate: boolean; similarity_score: number; matches: any[]; status: string };
  novelty: { overall_score: number | null; technical: number; methodological: number; application: number; market: number; status: string };
  overall_score: number | null;
  status: string;
  processing_time_seconds: number;
}

const parseResponseValue = (value: any, fallback: any) => {
  if (typeof value !== "string") return value ?? fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
};

const getTokenSet = (text: string) => new Set((text.toLowerCase().match(/[a-z0-9]{3,}/g) || []));

const compareText = (left: string, right: string) => {
  const leftTokens = getTokenSet(left);
  const rightTokens = getTokenSet(right);
  if (!leftTokens.size || !rightTokens.size) return 0;
  const overlap = [...leftTokens].filter((token) => rightTokens.has(token)).length;
  return Math.round((overlap / new Set([...leftTokens, ...rightTokens]).size) * 100);
};

const screenLocalApplications = (applications: LocalApplication[]): ScreeningResult[] => applications.map((application) => {
  const checks = [
    [Boolean(application.title?.trim()), "Project title is missing"],
    [Boolean(application.applicant_name?.trim()), "Applicant name is missing"],
    [Boolean(application.institution?.trim()), "Institution is missing"],
    [Boolean(application.abstract?.trim()), "Project abstract is missing"],
    [Number(application.budget) > 0, "Requested budget must be greater than zero"],
  ] as const;
  const failures = checks.filter(([passed]) => !passed).map(([, failure]) => failure);
  const otherApplications = applications.filter((candidate) => candidate.id !== application.id);
  const matches = otherApplications
    .map((candidate) => ({
      application_id: candidate.id,
      title: candidate.title,
      similarity_score: compareText(application.abstract, candidate.abstract),
    }))
    .filter((match) => match.similarity_score >= 30)
    .sort((left, right) => right.similarity_score - left.similarity_score);
  const similarity = matches[0]?.similarity_score || 0;

  return {
    application_id: application.id,
    title: application.title,
    eligibility: {
      passed: failures.length === 0,
      score: Math.round(((checks.length - failures.length) / checks.length) * 100),
      details: { local_completeness_check: true },
      failures,
      warnings: ["Local completeness check only. Official grant eligibility criteria were not checked."],
    },
    plagiarism: { originality_score: null, matches: [], status: "not_checked" },
    duplication: {
      is_duplicate: similarity >= 70,
      similarity_score: similarity,
      matches,
      status: similarity >= 70 ? "duplicate_candidate" : similarity >= 40 ? "similar_candidate" : "no_match",
    },
    novelty: { overall_score: null, technical: 0, methodological: 0, application: 0, market: 0, status: "not_checked" },
    overall_score: null,
    status: "pending_review",
    processing_time_seconds: 0,
  };
});

const getRecommendation = (screening: ScreeningResult): Recommendation => {
  if (!screening.eligibility.passed) {
    return {
      decision: "reject",
      reason: `Eligibility checklist failed: ${screening.eligibility.failures.join(", ") || "criteria not met"}.`,
    };
  }
  if (screening.plagiarism.originality_score == null) {
    return { decision: "review", reason: "Plagiarism was not checked. A reviewer must verify originality before deciding." };
  }
  if (screening.duplication.similarity_score >= 70) {
    return { decision: "review", reason: "Similarity is at least 70%. Compare the flagged proposal before deciding; similarity alone is not proof of duplication." };
  }
  if (screening.plagiarism.originality_score < 50) {
    return { decision: "review", reason: "Originality is below 50%. Inspect the matched sources; this score is a review signal, not proof of plagiarism." };
  }
  if (screening.plagiarism.originality_score >= 90 && screening.duplication.similarity_score < 40) {
    return { decision: "approve", reason: "Eligibility passed, originality is at least 90%, and duplicate similarity is below 40%." };
  }
  return { decision: "review", reason: "The screening signals are mixed or below the approval recommendation thresholds." };
};

export default function ScreeningPage() {
  const router = useRouter();
  const [focusedApplicationId, setFocusedApplicationId] = useState<string | null>(null);
  const [screenings, setScreenings] = useState<ScreeningResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedScreening, setSelectedScreening] = useState<ScreeningResult | null>(null);
  const [stats, setStats] = useState({ total: 0, approved: 0, rejected: 0, pending: 0 });
  const [error, setError] = useState("");
  const [localMode, setLocalMode] = useState(false);
  const [actionMessage, setActionMessage] = useState("");

  const registerApprovedApplicant = async (applicationId: string) => {
    let application: any = getLocalApplications().find((item) => item.id === applicationId);
    if (!application?.applicant_name) {
      try {
        const response = await api.get(`/applications/${encodeURIComponent(applicationId)}`);
        application = response.data.application || response.data;
      } catch {
        application = null;
      }
    }

    const fullName = application?.applicant_name || application?.full_name || application?.name;
    if (!fullName) return "Application approved, but applicant details were unavailable for researcher registration.";

    const registration = registerLocalResearcher({
      full_name: fullName,
      email: application.email,
      institution: application.institution,
      application_id: applicationId,
    });
    let remoteCreated = false;
    if (registration.created && !localMode && !applicationId.startsWith("LOCAL-")) {
      try {
        await api.post("/identities", {
          full_name: fullName,
          email: application.email,
          institution: application.institution,
          source_application_id: applicationId,
        });
        remoteCreated = true;
      } catch {
        remoteCreated = false;
      }
    }

    if (!registration.created) return `${fullName} is already registered and was linked to this approved application.`;
    return remoteCreated
      ? `${fullName} was automatically added to the researcher registry.`
      : `${fullName} was automatically saved in this browser's researcher registry.`;
  };

  useEffect(() => {
    const applicationId = new URLSearchParams(window.location.search).get("application");
    setFocusedApplicationId(applicationId);
    fetchScreenings(applicationId);
  }, []);

  const fetchScreenings = async (focusedId = focusedApplicationId) => {
    try {
      const response = await api.get('/screenings');
      const screeningsData = Array.isArray(response.data.screenings) ? response.data.screenings : [];
      setError("");
      setLocalMode(false);
      
      // Transform data to match frontend interface
      const transformedScreenings = screeningsData.map((s: any) => {
        const eligibilityDetails = parseResponseValue(s.eligibility_details, {});
        const plagiarismMatches = parseResponseValue(s.plagiarism_matches, []);
        const duplicationMatches = parseResponseValue(s.duplication_matches, []);
        const noveltyDetails = parseResponseValue(s.novelty_details, {});
        
        return {
          application_id: s.application_id,
          title: s.title,
          eligibility: {
            passed: s.eligibility_passed,
            score: s.eligibility_score,
            details: eligibilityDetails.details || {},
            failures: eligibilityDetails.failures || [],
            warnings: eligibilityDetails.warnings || []
          },
          plagiarism: {
            originality_score: s.plagiarism_score == null ? null : Number(s.plagiarism_score),
            matches: plagiarismMatches,
            status: plagiarismMatches.status || "unknown"
          },
          duplication: {
            is_duplicate: Number(s.duplication_score) >= 70,
            similarity_score: Number(s.duplication_score) || 0,
            matches: duplicationMatches,
            status: duplicationMatches.status || "unknown"
          },
          novelty: {
            overall_score: s.novelty_score == null ? null : Number(s.novelty_score),
            technical: noveltyDetails.technical || 0,
            methodological: noveltyDetails.methodological || 0,
            application: noveltyDetails.application || 0,
            market: noveltyDetails.market || 0,
            status: noveltyDetails.status || "unknown"
          },
          overall_score: s.overall_score == null ? null : Number(s.overall_score),
          status: s.status,
          processing_time_seconds: s.processing_time_seconds || 0
        };
      });

      const localApplications = getLocalApplications();
      const focusedLocalApplication = localApplications.find((application) => application.id === focusedId);
      const focusedLocalScreenings = focusedLocalApplication ? screenLocalApplications([focusedLocalApplication]) : [];
      const combinedScreenings = [
        ...focusedLocalScreenings,
        ...transformedScreenings.filter((screening: ScreeningResult) => screening.application_id !== focusedId),
      ];
      setScreenings(combinedScreenings);
      if (focusedLocalScreenings.length) {
        setLocalMode(true);
        setSelectedScreening(focusedLocalScreenings[0]);
      }
      
      // Calculate stats
      setStats({
        total: combinedScreenings.length,
        approved: combinedScreenings.filter((s: ScreeningResult) => s.status === 'approved').length,
        rejected: combinedScreenings.filter((s: ScreeningResult) => s.status === 'rejected').length,
        pending: combinedScreenings.filter((s: ScreeningResult) => s.status === 'pending_review').length,
      });
    } catch (error) {
      console.error("Failed to fetch screenings:", error);
      const localScreenings = screenLocalApplications(getLocalApplications());
      setScreenings(localScreenings);
      setLocalMode(true);
      setSelectedScreening(localScreenings.find((screening) => screening.application_id === focusedId) || null);
      setError("");
      setStats({
        total: localScreenings.length,
        approved: localScreenings.filter((screening) => screening.status === "approved").length,
        rejected: localScreenings.filter((screening) => screening.status === "rejected").length,
        pending: localScreenings.filter((screening) => screening.status === "pending_review").length,
      });
    } finally {
      setLoading(false);
    }
  };

  const getEligibilityBadge = (result: any) => {
    if (result?.passed) {
      return <Badge variant="default" className="bg-green-500">Pass</Badge>;
    }
    return <Badge variant="destructive">Fail</Badge>;
  };

  const getPlagiarismBadge = (score: number | null) => {
    if (score == null) return <Badge variant="outline">Not checked</Badge>;
    if (score >= 90) return <Badge variant="default" className="bg-green-500">{score}%</Badge>;
    if (score >= 70) return <Badge variant="secondary">{score}%</Badge>;
    return <Badge variant="destructive">{score}%</Badge>;
  };

  const getDuplicationBadge = (result: any) => {
    if (result?.is_duplicate) {
      return <Badge variant="destructive">Duplicate</Badge>;
    }
    return <Badge variant="default" className="bg-green-500">Unique</Badge>;
  };

  const getNoveltyBadge = (score: number | null) => {
    if (score == null) return <Badge variant="outline">Not assessed</Badge>;
    if (score >= 80) return <Badge variant="default" className="bg-green-500">High</Badge>;
    if (score >= 60) return <Badge variant="secondary">Medium</Badge>;
    return <Badge variant="outline">Low</Badge>;
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "approved":
        return <Badge variant="default" className="bg-green-500">Approved</Badge>;
      case "rejected":
        return <Badge variant="destructive">Rejected</Badge>;
      case "pending":
      case "pending_review":
      case "screening":
        return <Badge variant="secondary">Pending</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleHumanReview = async (appId: string, decision: string) => {
    setActionMessage("");
    if (localMode || appId.startsWith("LOCAL-")) {
      updateLocalApplication(appId, { status: decision });
      const updatedScreenings = screenings.map((screening) =>
        screening.application_id === appId ? { ...screening, status: decision } : screening
      );
      setScreenings(updatedScreenings);
      setSelectedScreening((current) => current?.application_id === appId ? { ...current, status: decision } : current);
      setStats({
        total: updatedScreenings.length,
        approved: updatedScreenings.filter((screening) => screening.status === "approved").length,
        rejected: updatedScreenings.filter((screening) => screening.status === "rejected").length,
        pending: updatedScreenings.filter((screening) => ["pending", "pending_review"].includes(screening.status)).length,
      });
      const registrationMessage = decision === "approved" ? ` ${await registerApprovedApplicant(appId)}` : "";
      setActionMessage(`Application ${decision.replaceAll("_", " ")} in this browser.${registrationMessage}`);
      return;
    }

    try {
      await api.put(`/applications/${encodeURIComponent(appId)}/status?status=${encodeURIComponent(decision)}`);
      const registrationMessage = decision === "approved" ? ` ${await registerApprovedApplicant(appId)}` : "";
      setActionMessage(`Application ${decision.replaceAll("_", " ")} successfully.${registrationMessage}`);
      fetchScreenings(focusedApplicationId);
    } catch {
      setActionMessage("The decision could not be saved. Check the API connection and try again.");
    }
  };

  const selectedRecommendation = selectedScreening ? getRecommendation(selectedScreening) : null;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-600">Loading screening results...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {error && <div role="alert" className="container mx-auto px-4 pt-5 text-sm text-red-600">{error}</div>}
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">AI Screening Dashboard</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">{localMode ? "Frontend checks for required fields and saved-proposal similarity; plagiarism and AI analysis require the screening API." : "Real-time AI-powered eligibility, plagiarism, duplication, and novelty analysis"}</p>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {localMode && (
          <div role="status" className="mb-6 border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
            Frontend screening mode: eligibility checks only required-field completeness, duplication compares saved browser applications, and plagiarism is not checked. Connect the screening API for actual AI analysis.
          </div>
        )}
        {/* Stats */}
        <div className="grid gap-6 md:grid-cols-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Total Screened
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">{stats.total}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Approved
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div className="text-3xl font-bold text-green-600">{stats.approved}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Rejected
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-500" />
                <div className="text-3xl font-bold text-red-600">{stats.rejected}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Pending Review
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-yellow-500" />
                <div className="text-3xl font-bold text-yellow-600">{stats.pending}</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Report View */}
        {selectedScreening && (
          <Card className="mb-8 border-2 border-blue-200">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Detailed Screening Report</CardTitle>
                  <CardDescription>Application: {selectedScreening.title} ({selectedScreening.application_id})</CardDescription>
                </div>
                <Button variant="outline" onClick={() => setSelectedScreening(null)}>
                  Close Report
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {selectedRecommendation && (
                <section className={`border px-4 py-4 ${selectedRecommendation.decision === "approve" ? "border-emerald-300 bg-emerald-50 text-emerald-950 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100" : selectedRecommendation.decision === "reject" ? "border-red-300 bg-red-50 text-red-950 dark:border-red-800 dark:bg-red-950/30 dark:text-red-100" : "border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100"}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="font-semibold">Frontend recommendation: {selectedRecommendation.decision === "review" ? "Human review" : selectedRecommendation.decision}</h2>
                    <Badge variant={selectedRecommendation.decision === "approve" ? "default" : selectedRecommendation.decision === "reject" ? "destructive" : "secondary"}>{selectedRecommendation.decision === "review" ? "Review required" : `Recommend ${selectedRecommendation.decision}`}</Badge>
                  </div>
                  <p className="mt-2 text-sm">{selectedRecommendation.reason}</p>
                  <p className="mt-2 text-xs opacity-80">This is a screening recommendation, not a final funding decision. Similarity signals are not proof of plagiarism or duplication.</p>
                </section>
              )}
              {actionMessage && <p role="status" className="text-sm text-muted-foreground">{actionMessage}</p>}
              {/* Overall Assessment */}
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Overall Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-4xl font-bold text-blue-600">{selectedScreening.overall_score == null ? "--" : `${selectedScreening.overall_score}/100`}</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Processing Time</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-4xl font-bold text-green-600">{selectedScreening.processing_time_seconds}s</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">AI Recommendation</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{getStatusBadge(selectedScreening.status)}</div>
                  </CardContent>
                </Card>
              </div>

              {/* Eligibility Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5" />
                    Eligibility Check
                  </CardTitle>
                  <CardDescription>
                    {localMode ? "Frontend completeness check only; official grant criteria and institution verification were not run." : "NRIF grant criteria validation with OpenAlex institution verification"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Score:</span>
                      <Badge variant={selectedScreening.eligibility.passed ? "default" : "destructive"}>
                        {selectedScreening.eligibility.score}/100
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Status:</span>
                      {getEligibilityBadge(selectedScreening.eligibility)}
                    </div>
                    {selectedScreening.eligibility.details?.institution_check?.verified_by_openalex && (
                      <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400">
                          <CheckCircle className="h-4 w-4" />
                          <span>Institution verified via OpenAlex</span>
                        </div>
                        {selectedScreening.eligibility.details.institution_check.openalex_data?.institution && (
                          <div className="mt-2 text-xs text-slate-600 dark:text-slate-400">
                            <p>{selectedScreening.eligibility.details.institution_check.openalex_data.institution.display_name}</p>
                            <p>Works: {selectedScreening.eligibility.details.institution_check.openalex_data.institution.works_count?.toLocaleString()}</p>
                            <p>Citations: {selectedScreening.eligibility.details.institution_check.openalex_data.institution.cited_by_count?.toLocaleString()}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Plagiarism Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Plagiarism Detection
                  </CardTitle>
                  <CardDescription>
                    {localMode ? "Not checked in frontend screening mode; plagiarism analysis requires the screening API." : "Checked against local database and OpenAlex publications"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Originality Score:</span>
                      {getPlagiarismBadge(selectedScreening.plagiarism.originality_score)}
                    </div>
                    {selectedScreening.plagiarism.matches.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-2">Potential Matches:</p>
                        <div className="space-y-2">
                          {selectedScreening.plagiarism.matches.map((match: any, idx: number) => (
                            <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                              <div className="flex justify-between items-center mb-1">
                                <span className="font-medium">{match.reference_title}</span>
                                <Badge variant={match.severity === 'high' ? 'destructive' : 'secondary'}>
                                  {match.similarity_score}% similarity
                                </Badge>
                              </div>
                              <div className="flex items-center gap-2 text-xs text-slate-500">
                                <span>Source: {match.source}</span>
                                {match.source === 'OpenAlex' && match.journal && (
                                  <>
                                    <span>•</span>
                                    <span>{match.journal}</span>
                                  </>
                                )}
                                {match.source === 'OpenAlex' && match.publication_year && (
                                  <>
                                    <span>•</span>
                                    <span>{match.publication_year}</span>
                                  </>
                                )}
                                {match.source === 'OpenAlex' && match.citation_count && (
                                  <>
                                    <span>•</span>
                                    <span>{match.citation_count} citations</span>
                                  </>
                                )}
                              </div>
                              {match.source === 'OpenAlex' && match.doi && (
                                <a 
                                  href={match.doi} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-xs text-blue-600 hover:underline"
                                >
                                  View on OpenAlex →
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Duplication Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Duplication Check
                  </CardTitle>
                  {localMode && <CardDescription>Compared with proposals saved in this browser only.</CardDescription>}
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Similarity Score:</span>
                      <Badge variant={selectedScreening.duplication.is_duplicate ? 'destructive' : 'default'}>
                        {selectedScreening.duplication.similarity_score}%
                      </Badge>
                    </div>
                    {getDuplicationBadge(selectedScreening.duplication)}
                    {selectedScreening.duplication.matches.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-2">Similar Proposals:</p>
                        <div className="space-y-2">
                          {selectedScreening.duplication.matches.map((match: any, idx: number) => (
                            <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                              <div className="flex justify-between items-center mb-1">
                                <span className="font-medium">{match.title}</span>
                                <Badge variant={match.is_likely_duplicate ? 'destructive' : 'secondary'}>
                                  {match.similarity_score}% similar
                                </Badge>
                              </div>
                              <p className="text-xs text-slate-500">ID: {match.application_id}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Novelty Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertCircle className="h-5 w-5" />
                    Novelty Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span>Overall Novelty:</span>
                      {getNoveltyBadge(selectedScreening.novelty.overall_score)}
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-600">Technical: {selectedScreening.novelty.technical}/100</p>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${selectedScreening.novelty.technical}%` }}></div>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Methodological: {selectedScreening.novelty.methodological}/100</p>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div className="bg-green-600 h-2 rounded-full" style={{ width: `${selectedScreening.novelty.methodological}%` }}></div>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Application: {selectedScreening.novelty.application}/100</p>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div className="bg-purple-600 h-2 rounded-full" style={{ width: `${selectedScreening.novelty.application}%` }}></div>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-slate-600">Market: {selectedScreening.novelty.market}/100</p>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div className="bg-orange-600 h-2 rounded-full" style={{ width: `${selectedScreening.novelty.market}%` }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Human Review Actions */}
              <Card className="border-2 border-yellow-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Human Review Required
                  </CardTitle>
                  <CardDescription>{localMode ? "Apply a reviewer decision to this browser-saved application" : "Review the screening evidence above and record a human decision"}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
                    <Button 
                      className="flex-1 bg-green-600 hover:bg-green-700"
                      onClick={() => handleHumanReview(selectedScreening.application_id, 'approved')}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Approve Application
                    </Button>
                    <Button 
                      className="flex-1 bg-red-600 hover:bg-red-700"
                      onClick={() => handleHumanReview(selectedScreening.application_id, 'rejected')}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject Application
                    </Button>
                    <Button 
                      variant="outline"
                      className="flex-1"
                      onClick={() => handleHumanReview(selectedScreening.application_id, 'pending_review')}
                    >
                      <Clock className="h-4 w-4 mr-2" />
                      Request More Info
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        )}

        {/* Recent Screenings */}
        <Card>
          <CardHeader>
            <CardTitle>AI Screening Results</CardTitle>
            <CardDescription>Latest AI-powered screening results from eligibility, plagiarism, duplication, and novelty services</CardDescription>
          </CardHeader>
          <CardContent>
            {screenings.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                No screening results yet. Start screening applications to see AI analysis.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Application ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Eligibility</TableHead>
                    <TableHead>Plagiarism</TableHead>
                    <TableHead>Duplication</TableHead>
                    <TableHead>Novelty</TableHead>
                    <TableHead>Overall</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {screenings.map((screening) => (
                    <TableRow key={screening.application_id}>
                      <TableCell className="font-mono">{screening.application_id}</TableCell>
                      <TableCell>{screening.title}</TableCell>
                      <TableCell>{getEligibilityBadge(screening.eligibility)}</TableCell>
                      <TableCell>{getPlagiarismBadge(screening.plagiarism?.originality_score ?? null)}</TableCell>
                      <TableCell>{getDuplicationBadge(screening.duplication)}</TableCell>
                      <TableCell>{getNoveltyBadge(screening.novelty?.overall_score ?? null)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{screening.overall_score == null ? "Not assessed" : `${screening.overall_score}/100`}</Badge>
                      </TableCell>
                      <TableCell>{getStatusBadge(screening.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => setSelectedScreening(screening)}
                          >
                            <FileText className="h-4 w-4 mr-1" />
                            Report
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => router.push(`/applications/${screening.application_id}`)}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
