"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Users, FileText, TrendingUp, AlertCircle } from "lucide-react";
import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

interface DashboardApplication {
  id: string;
  title: string;
  applicant_name?: string;
  status: string;
  submitted_at?: string;
}

export default function DashboardPage() {
  const [applications, setApplications] = useState<DashboardApplication[] | null>(null);
  const [screeningCount, setScreeningCount] = useState<number | null>(null);
  const [researcherCount, setResearcherCount] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadOverview = async () => {
    setRefreshing(true);
    const [applicationResult, screeningResult, identityResult] = await Promise.allSettled([
      api.get("/applications"),
      api.get("/screenings"),
      api.get("/identities"),
    ]);

    if (applicationResult.status === "fulfilled") {
      setApplications(applicationResult.value.data.applications || []);
    } else {
      setApplications(null);
    }
    if (screeningResult.status === "fulfilled") {
      setScreeningCount((screeningResult.value.data.screenings || []).length);
    } else {
      setScreeningCount(null);
    }
    if (identityResult.status === "fulfilled") {
      setResearcherCount((identityResult.value.data.identities || identityResult.value.data.researchers || []).length);
    } else {
      setResearcherCount(null);
    }
    setRefreshing(false);
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const approvedCount = applications?.filter((application) => application.status?.toLowerCase() === "approved").length ?? null;
  const approvalRate = applications?.length ? Math.round(((approvedCount || 0) / applications.length) * 100) : null;
  const recentApplications = [...(applications || [])]
    .sort((left, right) => new Date(right.submitted_at || 0).getTime() - new Date(left.submitted_at || 0).getTime())
    .slice(0, 4);
  const pendingApplications = applications?.filter((application) =>
    ["pending", "pending_review", "in_review", "screening"].includes(application.status?.toLowerCase())
  ) ?? [];

  const displayCount = (value: number | null | undefined) => value == null ? "--" : value.toLocaleString();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Overview Stats */}
        <div className="grid gap-6 md:grid-cols-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Total Applications
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-500" />
                <div className="text-3xl font-bold text-slate-900 dark:text-white">{displayCount(applications?.length)}</div>
              </div>
              <p className="text-xs text-slate-500 mt-1">Current workspace</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Active Researchers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-green-500" />
                <div className="text-3xl font-bold text-slate-900 dark:text-white">{displayCount(researcherCount)}</div>
              </div>
              <p className="text-xs text-slate-500 mt-1">Registered identities</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Screening Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-purple-500" />
                <div className="text-3xl font-bold text-slate-900 dark:text-white">{displayCount(screeningCount)}</div>
              </div>
              <p className="text-xs text-slate-500 mt-1">Completed screenings</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Approval Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-orange-500" />
                <div className="text-3xl font-bold text-slate-900 dark:text-white">{approvalRate == null ? "--" : `${approvalRate}%`}</div>
              </div>
              <p className="text-xs text-slate-500 mt-1">Of submitted applications</p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity & Alerts */}
        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <div><CardTitle>Recent applications</CardTitle><CardDescription>Latest submissions in this workspace</CardDescription></div>
              <button type="button" onClick={loadOverview} disabled={refreshing} className="text-sm text-primary hover:underline">{refreshing ? "Refreshing..." : "Refresh"}</button>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentApplications.length ? recentApplications.map((application) => (
                <Link key={application.id} href={`/applications/${encodeURIComponent(application.id)}`} className="flex items-start justify-between gap-3 border-b border-border pb-3 last:border-0 last:pb-0">
                  <div className="flex min-w-0 items-start gap-3"><FileText className="mt-0.5 h-5 w-5 shrink-0 text-primary" /><div className="min-w-0"><p className="truncate text-sm font-medium">{application.title}</p><p className="mt-1 text-xs text-muted-foreground">{application.applicant_name || "Applicant not provided"}</p></div></div>
                  <Badge variant="outline">{application.status}</Badge>
                </Link>
              )) : <p className="text-sm text-muted-foreground">{applications === null ? "Application data is unavailable." : "No applications have been submitted yet."}</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Awaiting review</CardTitle>
              <CardDescription>Applications that may need a decision</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {pendingApplications.length ? pendingApplications.slice(0, 4).map((application) => (
                <Link key={application.id} href={`/applications/${encodeURIComponent(application.id)}`} className="flex items-start gap-3">
                  <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
                  <div><p className="text-sm font-medium">{application.title}</p><p className="mt-1 text-xs text-muted-foreground">{application.status.replaceAll("_", " ")}</p></div>
                </Link>
              )) : <p className="text-sm text-muted-foreground">{applications === null ? "Review data is unavailable." : "No applications are currently awaiting review."}</p>}
            </CardContent>
          </Card>
        </div>

        {/* System Health */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border pt-5 text-sm text-muted-foreground">
          <span><Activity className="mr-2 inline h-4 w-4" />Overview reflects live workspace requests</span>
          <Link href="/applications" className="text-primary hover:underline">Browse all applications</Link>
        </div>
      </div>
    </div>
  );
}
