"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Play, Eye, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import { deleteLocalApplication, getLocalApplications, registerLocalResearcher, updateLocalApplication } from "@/lib/local-workspace";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Application {
  id: string;
  title: string;
  applicant_name: string;
  email?: string;
  institution: string;
  status: string;
  submitted_at: string;
  screening_result?: any;
}

export default function ApplicationsPage() {
  const router = useRouter();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [screening, setScreening] = useState<{ [key: string]: boolean }>({});
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState("");
  const [localMode, setLocalMode] = useState(false);
  const [actionMessage, setActionMessage] = useState("");

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await api.get('/applications');
      const data = response.data;
      setApplications(Array.isArray(data) ? data : data.applications || []);
      setLocalMode(false);
      setError("");
    } catch (error) {
      console.error("Failed to fetch applications:", error);
      setApplications(getLocalApplications());
      setLocalMode(true);
      setError("");
    } finally {
      setLoading(false);
    }
  };

  const startScreening = async (appId: string) => {
    setScreening((current) => ({ ...current, [appId]: true }));
    try {
      await api.post(`/screen/${appId}`, {
        check_eligibility: true,
        check_plagiarism: true,
        check_duplication: true,
        check_novelty: true,
      });
      alert("Screening started successfully!");
      fetchApplications();
    } catch (error) {
      alert("Failed to start screening");
    } finally {
      setScreening((current) => ({ ...current, [appId]: false }));
    }
  };

  const updateStatus = async (appId: string, newStatus: string) => {
    setActionMessage("");
    const application = applications.find((item) => item.id === appId);
    if (localMode) {
      setApplications(updateLocalApplication(appId, { status: newStatus }));
      if (newStatus === "approved" && application?.applicant_name) {
        const result = registerLocalResearcher({
          full_name: application.applicant_name,
          email: application.email,
          institution: application.institution,
          application_id: appId,
        });
        setActionMessage(result.created
          ? `${application.applicant_name} was added to the researcher registry after approval.`
          : `${application.applicant_name} is already registered; this application was linked to their record.`);
      }
      return;
    }
    try {
      await api.put(`/applications/${encodeURIComponent(appId)}/status?status=${encodeURIComponent(newStatus)}`);
      if (newStatus === "approved" && application?.applicant_name) {
        const result = registerLocalResearcher({
          full_name: application.applicant_name,
          email: application.email,
          institution: application.institution,
          application_id: appId,
        });
        let remoteCreated = false;
        if (result.created) {
          try {
            await api.post("/identities", {
              full_name: application.applicant_name,
              email: application.email,
              institution: application.institution,
              source_application_id: appId,
            });
            remoteCreated = true;
          } catch {
            remoteCreated = false;
          }
        }
        setActionMessage(result.created
          ? remoteCreated
            ? `${application.applicant_name} was added to the researcher registry after approval.`
            : `${application.applicant_name} was approved and saved in this browser's researcher registry.`
          : `${application.applicant_name} is already registered; this application was linked to their record.`);
      } else {
        setActionMessage(`Application ${newStatus.replaceAll("_", " ")}.`);
      }
      fetchApplications();
    } catch (error) {
      setActionMessage("Application status could not be updated. Check the connection and try again.");
    }
  };

  const deleteApplication = async (appId: string) => {
    if (!confirm("Are you sure you want to delete this application?")) return;
    if (localMode) {
      setApplications(deleteLocalApplication(appId));
      return;
    }
    try {
      await api.delete(`/applications/${appId}`);
      fetchApplications();
    } catch (error) {
      alert("Failed to delete application");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return <Badge variant="default">Pending</Badge>;
      case "in_review":
      case "screening":
        return <Badge variant="secondary">In Review</Badge>;
      case "approved":
        return <Badge variant="default" className="bg-green-500">Approved</Badge>;
      case "rejected":
        return <Badge variant="destructive">Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const filteredApplications = applications.filter((application) =>
    [application.id, application.title, application.applicant_name, application.institution, application.status]
      .some((value) => value?.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-600">Loading applications...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Grant Applications</h1>
            <Link href="/applications/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Application
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder="Search applications..."
                    className="w-full rounded-md border border-slate-200 pl-10 pr-4 py-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>
              <Button variant="outline" onClick={fetchApplications} disabled={loading} aria-label="Refresh applications">
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>

        {localMode && (
          <div role="status" className="mb-6 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
            API unavailable. Showing applications saved in this browser; new submissions will stay on this device until the API reconnects.
          </div>
        )}
        {actionMessage && <p role="status" className="mb-5 text-sm text-muted-foreground">{actionMessage}</p>}

        {/* Applications Table */}
        <Card>
          <CardHeader>
            <CardTitle>All Applications</CardTitle>
            <CardDescription>View and manage grant applications</CardDescription>
          </CardHeader>
          <CardContent>
            {error ? (
              <div className="flex flex-col items-center gap-3 py-10 text-center">
                <p role="alert" className="text-sm text-red-600">{error}</p>
                <Button variant="outline" onClick={fetchApplications}>Try again</Button>
              </div>
            ) : filteredApplications.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                {searchTerm ? "No applications match your search." : "No applications found. Submit your first application."}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Applicant</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Screening</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredApplications.map((app) => (
                    <TableRow key={app.id}>
                      <TableCell className="font-mono">{app.id}</TableCell>
                      <TableCell>{app.title}</TableCell>
                      <TableCell>{app.applicant_name}</TableCell>
                      <TableCell>{getStatusBadge(app.status)}</TableCell>
                      <TableCell>{new Date(app.submitted_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startScreening(app.id)}
                          disabled={screening[app.id]}
                        >
                          <Play className="h-4 w-4 mr-1" />
                          {screening[app.id] ? "Running..." : "Screen"}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm" aria-label={`View ${app.title}`} onClick={() => router.push(`/applications/${encodeURIComponent(app.id)}`)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateStatus(app.id, "approved")}
                          >
                            Approve
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateStatus(app.id, "rejected")}
                          >
                            Reject
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteApplication(app.id)}
                          >
                            Delete
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
