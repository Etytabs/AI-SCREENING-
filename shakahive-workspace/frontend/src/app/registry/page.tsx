"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, UserCheck, AlertTriangle, Plus, X } from "lucide-react";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import { getLocalResearchers, LocalResearcher, registerLocalResearcher } from "@/lib/local-workspace";

interface ResearcherIdentity {
  id?: string;
  researcher_id?: string;
  permanent_id?: string;
  full_name?: string;
  name?: string;
  email?: string;
  institution?: string;
  orcid?: string;
  status?: string;
}

export default function RegistryPage() {
  const [identities, setIdentities] = useState<ResearcherIdentity[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [error, setError] = useState("");
  const [localMode, setLocalMode] = useState(false);
  const [notice, setNotice] = useState("");
  const [selectedIdentity, setSelectedIdentity] = useState<ResearcherIdentity | null>(null);
  const [form, setForm] = useState({ full_name: "", email: "", institution: "", orcid: "" });

  const loadIdentities = async () => {
    setLoading(true);
    try {
      const response = await api.get("/identities");
      const data = response.data;
      const serverIdentities = Array.isArray(data) ? data : data.identities || data.researchers || [];
      setIdentities(mergeIdentities(serverIdentities, getLocalResearchers()));
      setLocalMode(false);
      setError("");
    } catch {
      setIdentities(getLocalResearchers());
      setLocalMode(true);
      setError("");
    } finally {
      setLoading(false);
    }
  };

  const mergeIdentities = (server: ResearcherIdentity[], local: LocalResearcher[]) => {
    const merged = new Map<string, ResearcherIdentity>();
    [...local, ...server].forEach((identity) => {
      const emailKey = identity.email?.trim().toLowerCase();
      const nameKey = (identity.full_name || identity.name || "").trim().toLowerCase();
      const institutionKey = (identity.institution || "").trim().toLowerCase();
      const key = emailKey ? `email:${emailKey}` : `name:${nameKey}|${institutionKey}`;
      if (nameKey || emailKey) merged.set(key, merged.has(key) ? { ...merged.get(key), ...identity } : identity);
    });
    return Array.from(merged.values());
  };

  useEffect(() => {
    loadIdentities();
  }, []);

  const createIdentity = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      registerLocalResearcher({ ...form, application_id: `MANUAL-${Date.now()}` });
      try {
        await api.post("/identities", form);
        setNotice(`${form.full_name} was added to the researcher registry.`);
      } catch {
        setNotice(`${form.full_name} was saved in this browser's researcher registry.`);
        setLocalMode(true);
      }
      setForm({ full_name: "", email: "", institution: "", orcid: "" });
      setFormOpen(false);
      if (localMode) setIdentities(getLocalResearchers());
      else await loadIdentities();
    } catch {
      setError("Researcher could not be added. Please check the details and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const showIdentity = async (identity: ResearcherIdentity) => {
    const id = identity.id || identity.researcher_id || identity.permanent_id;
    if (!id || id.startsWith("RID-")) {
      setSelectedIdentity(identity);
      return;
    }
    try {
      const response = await api.get(`/identities/${encodeURIComponent(id)}`);
      setSelectedIdentity(response.data.identity || response.data);
    } catch {
      setError("Researcher details could not be loaded.");
    }
  };

  const filteredIdentities = identities.filter((identity) =>
    [identity.full_name, identity.name, identity.email, identity.institution, identity.orcid, identity.permanent_id, identity.researcher_id]
      .some((value) => value?.toLowerCase().includes(search.toLowerCase()))
  );
  const verifiedCount = identities.filter((identity) => identity.status?.toLowerCase() === "verified").length;
  const conflictCount = identities.filter((identity) => identity.status?.toLowerCase().includes("conflict")).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Researcher Identity Registry</h1>
            <Button onClick={() => setFormOpen((open) => !open)}>
              {formOpen ? <X className="mr-2 h-4 w-4" /> : <Plus className="mr-2 h-4 w-4" />}
              {formOpen ? "Close" : "Add researcher"}
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {error && <div role="alert" className="mb-5 flex items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300"><span>{error}</span><Button variant="outline" size="sm" onClick={loadIdentities}>Try again</Button></div>}
        {notice && <p role="status" className="mb-5 text-sm text-muted-foreground">{notice}</p>}
        {localMode && <p role="status" className="mb-5 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">Showing identities saved in this browser. They are not synced to the API.</p>}

        {formOpen && (
          <Card className="mb-6">
            <CardHeader><CardTitle>Add researcher</CardTitle><CardDescription>Create a researcher identity in this workspace.</CardDescription></CardHeader>
            <CardContent>
              <form onSubmit={createIdentity} className="grid gap-4 sm:grid-cols-2">
                <Input aria-label="Full name" placeholder="Full name" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required />
                <Input aria-label="Email" type="email" placeholder="Email address" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
                <Input aria-label="Institution" placeholder="Institution" value={form.institution} onChange={(event) => setForm({ ...form, institution: event.target.value })} required />
                <Input aria-label="ORCID" placeholder="ORCID (optional)" value={form.orcid} onChange={(event) => setForm({ ...form, orcid: event.target.value })} />
                <div className="sm:col-span-2"><Button type="submit" disabled={submitting}>{submitting ? "Adding..." : "Create identity"}</Button></div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Search */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by name, email, ORCID, or institution..."
                className="w-full rounded-md border border-slate-200 pl-10 pr-4 py-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Total Researchers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900 dark:text-white">{loading ? "--" : identities.length.toLocaleString()}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Verified Identities
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-green-500" />
                <div className="text-3xl font-bold text-green-600">{loading ? "--" : verifiedCount.toLocaleString()}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                Pending Conflicts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                <div className="text-3xl font-bold text-yellow-600">{loading ? "--" : conflictCount.toLocaleString()}</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Researchers Table */}
        <Card>
          <CardHeader>
            <CardTitle>Registered Researchers</CardTitle>
            <CardDescription>Permanent researcher identities across all tenants</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Permanent ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Institution</TableHead>
                  <TableHead>ORCID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell colSpan={7} className="py-10 text-center text-muted-foreground">Loading identities...</TableCell></TableRow>
                ) : filteredIdentities.length ? filteredIdentities.map((identity, index) => {
                  const id = identity.id || identity.researcher_id || identity.permanent_id || `identity-${index}`;
                  const name = identity.full_name || identity.name || "Name unavailable";
                  const status = identity.status || "Pending";
                  return (
                    <TableRow key={id}>
                      <TableCell className="font-mono">{identity.permanent_id || identity.researcher_id || identity.id || "--"}</TableCell>
                      <TableCell>{name}</TableCell>
                      <TableCell>{identity.email || "--"}</TableCell>
                      <TableCell>{identity.institution || "--"}</TableCell>
                      <TableCell className="font-mono">{identity.orcid || "Not linked"}</TableCell>
                      <TableCell><Badge variant={status.toLowerCase() === "verified" ? "default" : "secondary"}>{status.replaceAll("_", " ")}</Badge></TableCell>
                      <TableCell><Button variant="ghost" size="sm" onClick={() => showIdentity(identity)}>View</Button></TableCell>
                    </TableRow>
                  );
                }) : (
                  <TableRow><TableCell colSpan={7} className="py-10 text-center text-muted-foreground">{search ? "No researchers match your search." : "No researcher identities have been registered."}</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
            </div>
          </CardContent>
        </Card>

        {selectedIdentity && (
          <Card className="mt-6">
            <CardHeader className="flex flex-row items-start justify-between">
              <div><CardTitle>{selectedIdentity.full_name || selectedIdentity.name || "Researcher details"}</CardTitle><CardDescription>{selectedIdentity.permanent_id || selectedIdentity.researcher_id || selectedIdentity.id || "Identity record"}</CardDescription></div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedIdentity(null)} aria-label="Close researcher details"><X className="h-4 w-4" /></Button>
            </CardHeader>
            <CardContent className="grid gap-4 text-sm sm:grid-cols-2">
              <p><span className="text-muted-foreground">Email: </span>{selectedIdentity.email || "Not provided"}</p>
              <p><span className="text-muted-foreground">Institution: </span>{selectedIdentity.institution || "Not provided"}</p>
              <p><span className="text-muted-foreground">ORCID: </span>{selectedIdentity.orcid || "Not linked"}</p>
              <p><span className="text-muted-foreground">Status: </span>{selectedIdentity.status || "Unknown"}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
