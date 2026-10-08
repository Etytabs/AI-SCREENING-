"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle, Play, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import api from "@/lib/api";
import { getLocalApplications } from "@/lib/local-workspace";

interface ApplicationDetails {
  id?: string;
  title?: string;
  applicant_name?: string;
  email?: string;
  institution?: string;
  status?: string;
  submitted_at?: string;
  abstract?: string;
  budget?: number | string;
}

export default function ApplicationDetailsPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const applicationId = params.id;
  const justSubmitted = searchParams.get("submitted") === "1";
  const [application, setApplication] = useState<ApplicationDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [screening, setScreening] = useState(false);
  const [error, setError] = useState("");
  const [localMode, setLocalMode] = useState(false);

  const loadApplication = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/applications/${encodeURIComponent(applicationId)}`);
      setApplication(response.data.application || response.data);
      setLocalMode(false);
      setError("");
    } catch {
      const localApplication = getLocalApplications().find((item) => item.id === applicationId);
      setApplication(localApplication || null);
      setLocalMode(Boolean(localApplication));
      setError(localApplication ? "" : "Application details could not be loaded. Check the connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplication();
  }, [applicationId]);

  const startScreening = async () => {
    if (localMode || applicationId.startsWith("LOCAL-")) {
      router.push(`/screening?application=${encodeURIComponent(applicationId)}`);
      return;
    }

    setScreening(true);
    try {
      await api.post(`/screen/${encodeURIComponent(applicationId)}`, {
        check_eligibility: true,
        check_plagiarism: true,
        check_duplication: true,
        check_novelty: true,
      });
      router.push("/screening");
    } catch {
      setError("Screening could not be started. Please try again.");
    } finally {
      setScreening(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link href="/applications" className="mb-3 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft size={16} /> Back to applications
          </Link>
          <h1 className="text-2xl font-semibold">Application details</h1>
          <p className="mt-1 text-sm text-muted-foreground">Record {applicationId}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadApplication} disabled={loading} aria-label="Refresh application details">
            <RefreshCw size={16} />
          </Button>
          <Button onClick={startScreening} disabled={screening || loading || !application}>
            <Play size={16} className="mr-2" /> {screening ? "Starting..." : "Start screening"}
          </Button>
        </div>
      </div>

      {justSubmitted && application && (
        <section role="status" aria-live="polite" className="border border-emerald-300 bg-emerald-50 px-5 py-5 text-emerald-950 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100">
          <div className="flex items-start gap-3">
            <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700 dark:text-emerald-300" />
            <div>
              <h2 className="text-lg font-semibold">Application accepted</h2>
              <p className="mt-1 text-sm">Your submission has been received. This confirms receipt for review, not a funding decision.</p>
              <p className="mt-2 text-xs">Reference: <span className="font-mono">{applicationId}</span></p>
              {localMode && <p className="mt-2 text-xs">Saved in this browser only. It has not been sent to the API.</p>}
              <Link href="/applications" className="mt-3 inline-block text-sm font-medium underline underline-offset-4">View applications</Link>
            </div>
          </div>
        </section>
      )}
      {error && <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">{error}</p>}
      {localMode && <p role="status" className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">This application is saved in this browser and has not been sent to the API.</p>}
      {loading ? (
        <p role="status" className="py-12 text-center text-sm text-muted-foreground">Loading application...</p>
      ) : application ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>{application.title || "Untitled application"}</CardTitle>
                <CardDescription className="mt-2">Submitted by {application.applicant_name || "Applicant not provided"}</CardDescription>
              </div>
              <Badge variant="outline">{application.status || "Status unavailable"}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
              <div><dt className="text-xs font-medium uppercase text-muted-foreground">Institution</dt><dd className="mt-1 text-sm">{application.institution || "Not provided"}</dd></div>
              <div><dt className="text-xs font-medium uppercase text-muted-foreground">Applicant email</dt><dd className="mt-1 break-all text-sm">{application.email || "Not provided"}</dd></div>
              <div><dt className="text-xs font-medium uppercase text-muted-foreground">Submitted</dt><dd className="mt-1 text-sm">{application.submitted_at ? new Date(application.submitted_at).toLocaleString() : "Not available"}</dd></div>
              <div><dt className="text-xs font-medium uppercase text-muted-foreground">Requested budget</dt><dd className="mt-1 text-sm">{application.budget != null ? Number(application.budget).toLocaleString() : "Not provided"}</dd></div>
            </dl>
            <section className="border-t border-border pt-5">
              <h2 className="text-sm font-semibold">Abstract</h2>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{application.abstract || "No abstract was included with this application."}</p>
            </section>
          </CardContent>
        </Card>
      ) : (
        <p className="py-12 text-center text-sm text-muted-foreground">Application not found.</p>
      )}
    </div>
  );
}
