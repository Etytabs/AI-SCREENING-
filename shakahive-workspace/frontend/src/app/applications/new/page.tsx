"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, ArrowRight, Upload, FileText, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import api from "@/lib/api";
import { cacheApplicationForApproval, createLocalApplication, saveLocalAttachment } from "@/lib/local-workspace";

export default function NewApplicationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileUploaded, setFileUploaded] = useState(false);
  const [uploadedFileInfo, setUploadedFileInfo] = useState<any>(null);
  const [error, setError] = useState("");
  const [localModeMessage, setLocalModeMessage] = useState("");
  const [step, setStep] = useState<1 | 2>(1);
  const [formData, setFormData] = useState({
    title: "",
    applicant_name: "",
    email: "",
    institution: "",
    budget: "",
    abstract: "",
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError("");
    const uploadData = new FormData();
    uploadData.append('file', file);

    try {
      const response = await api.post('/upload-document', uploadData);

      setUploadedFileInfo(response.data);
      setFileUploaded(true);
      setFormData({
        ...formData,
        abstract: response.data.extracted_text || formData.abstract,
      });
    } catch {
      try {
        const documentId = await saveLocalAttachment(file);
        const extractedText = file.type === "text/plain" || file.name.toLowerCase().endsWith(".txt")
          ? await file.text()
          : "";
        setUploadedFileInfo({
          filename: file.name,
          character_count: extractedText.length,
          extracted_text: extractedText,
          local_document_id: documentId,
        });
        setFileUploaded(true);
        setLocalModeMessage(extractedText
          ? "API unavailable. The text file is saved in this browser and its contents were added to the abstract."
          : "API unavailable. The file is saved in this browser, but PDF/DOCX text extraction requires the API. Add the abstract manually.");
        if (extractedText) {
          setFormData((current) => ({ ...current, abstract: extractedText }));
        }
      } catch {
        setError("Upload failed and this browser could not store the file. Please reconnect to the API and retry.");
      }
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (step === 1) {
      setStep(2);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await api.post('/applications', {
        title: formData.title,
        abstract: formData.abstract,
        applicant_name: formData.applicant_name,
        email: formData.email || undefined,
        institution: formData.institution,
        budget: parseFloat(formData.budget),
        tenant_id: "nrif",
        file_path: uploadedFileInfo?.file_path,
        extracted_text: uploadedFileInfo?.extracted_text,
      });
      const applicationId = response.data.application_id || response.data.id || response.data.application?.id;
      if (!applicationId) throw new Error("Submission response did not include an application ID.");
      cacheApplicationForApproval({
        id: applicationId,
        title: formData.title,
        abstract: formData.abstract,
        applicant_name: formData.applicant_name,
        email: formData.email || undefined,
        institution: formData.institution,
        budget: Number(formData.budget),
        status: "pending",
        submitted_at: new Date().toISOString(),
        document_name: uploadedFileInfo?.filename,
      });
      router.push(`/applications/${encodeURIComponent(applicationId)}?submitted=1`);
    } catch {
      const localApplication = createLocalApplication({
        title: formData.title,
        abstract: formData.abstract,
        applicant_name: formData.applicant_name,
        email: formData.email || undefined,
        institution: formData.institution,
        budget: Number(formData.budget),
        document_name: uploadedFileInfo?.filename,
        document_id: uploadedFileInfo?.local_document_id,
      });
      router.push(`/applications/${encodeURIComponent(localApplication.id)}?submitted=1`);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/applications">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">New Grant Application</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl">
          <Card>
            <CardHeader>
              <CardTitle>Submit New Application</CardTitle>
              <CardDescription>{step === 1 ? "Enter the project and applicant details to begin." : "Review the details before submitting your application."}</CardDescription>
            </CardHeader>
            <CardContent>
              <ol aria-label="Application steps" className="mb-6 grid grid-cols-2 gap-3">
                <li aria-current={step === 1 ? "step" : undefined} className={`border-b-2 pb-3 text-sm ${step === 1 ? "border-primary font-semibold text-foreground" : "border-border text-muted-foreground"}`}>
                  <span className="mr-2 font-mono text-xs">01</span>Details
                </li>
                <li aria-current={step === 2 ? "step" : undefined} className={`border-b-2 pb-3 text-sm ${step === 2 ? "border-primary font-semibold text-foreground" : "border-border text-muted-foreground"}`}>
                  <span className="mr-2 font-mono text-xs">02</span>Review &amp; submit
                </li>
              </ol>
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">{error}</p>}
                {localModeMessage && <p role="status" className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">{localModeMessage}</p>}
                {step === 1 ? <>
                {/* File Upload Section */}
                <div className="space-y-2">
                  <Label htmlFor="file">Upload Research Document (PDF, DOCX)</Label>
                  <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-slate-400 transition-colors">
                    <input
                      id="file"
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={handleFileUpload}
                      className="hidden"
                      disabled={uploading}
                    />
                    <label htmlFor="file" className="cursor-pointer">
                      {uploading ? (
                        <div className="flex flex-col items-center gap-2">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                          <p className="text-sm text-slate-600">Extracting text from document...</p>
                        </div>
                      ) : fileUploaded ? (
                        <div className="flex flex-col items-center gap-2">
                          <CheckCircle className="h-8 w-8 text-green-500" />
                          <p className="text-sm text-slate-600">
                            {uploadedFileInfo?.filename}{uploadedFileInfo?.character_count ? ` (${uploadedFileInfo.character_count.toLocaleString()} characters)` : ""}
                          </p>
                          <p className="text-xs text-slate-500">Click to upload a different file</p>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-2">
                          <Upload className="h-8 w-8 text-slate-400" />
                          <p className="text-sm text-slate-600">
                            Click to upload or drag and drop
                          </p>
                          <p className="text-xs text-slate-500">PDF, DOCX, or TXT (Max 10MB)</p>
                        </div>
                      )}
                    </label>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="title">Project Title</Label>
                  <Input
                    id="title"
                    name="title"
                    placeholder="Enter project title"
                    value={formData.title}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="applicant_name">Applicant Name</Label>
                  <Input
                    id="applicant_name"
                    name="applicant_name"
                    placeholder="Enter applicant name"
                    value={formData.applicant_name}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Applicant Email (optional)</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="researcher@institution.edu"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="institution">Institution</Label>
                  <Input
                    id="institution"
                    name="institution"
                    placeholder="Enter institution name"
                    value={formData.institution}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="budget">Budget Requested ($)</Label>
                  <Input
                    id="budget"
                    name="budget"
                    type="number"
                    placeholder="500000"
                    min="0"
                    step="any"
                    value={formData.budget}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="abstract">
                    Abstract
                    {fileUploaded && (
                      <span className="ml-2 text-xs text-green-600">(Auto-filled from document)</span>
                    )}
                  </Label>
                  <Textarea
                    id="abstract"
                    name="abstract"
                    placeholder="Provide a detailed abstract of your project including objectives, methodology, and expected outcomes..."
                    rows={8}
                    value={formData.abstract}
                    onChange={handleChange}
                    required
                  />
                  {fileUploaded && (
                    <p className="text-xs text-slate-500">
                      <FileText className="h-3 w-3 inline mr-1" />
                      Document text extracted automatically. You can edit if needed.
                    </p>
                  )}
                </div>
                </> : (
                  <section aria-label="Application review" className="space-y-5">
                    <dl className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
                      <div><dt className="text-xs font-medium uppercase text-muted-foreground">Project title</dt><dd className="mt-1 text-sm">{formData.title}</dd></div>
                      <div><dt className="text-xs font-medium uppercase text-muted-foreground">Applicant</dt><dd className="mt-1 text-sm">{formData.applicant_name}</dd></div>
                      <div><dt className="text-xs font-medium uppercase text-muted-foreground">Applicant email</dt><dd className="mt-1 text-sm">{formData.email || "Not provided"}</dd></div>
                      <div><dt className="text-xs font-medium uppercase text-muted-foreground">Institution</dt><dd className="mt-1 text-sm">{formData.institution}</dd></div>
                      <div><dt className="text-xs font-medium uppercase text-muted-foreground">Requested budget</dt><dd className="mt-1 text-sm">{Number(formData.budget).toLocaleString()}</dd></div>
                      <div className="sm:col-span-2"><dt className="text-xs font-medium uppercase text-muted-foreground">Document</dt><dd className="mt-1 text-sm">{uploadedFileInfo?.filename || "No document attached"}</dd></div>
                      <div className="sm:col-span-2"><dt className="text-xs font-medium uppercase text-muted-foreground">Abstract</dt><dd className="mt-1 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{formData.abstract}</dd></div>
                    </dl>
                    <p className="border-t border-border pt-4 text-xs text-muted-foreground">Submitting confirms these details are ready for review. This is not a funding decision.</p>
                  </section>
                )}

                <div className="flex gap-4">
                  {step === 1 ? <>
                    <Button type="submit" className="flex-1" disabled={uploading || loading}>Continue to review <ArrowRight className="ml-2 h-4 w-4" /></Button>
                    <Link href="/applications" className="flex-1"><Button type="button" variant="outline" className="w-full">Cancel</Button></Link>
                  </> : <>
                    <Button type="button" variant="outline" className="flex-1" onClick={() => setStep(1)} disabled={loading}>Back to edit</Button>
                    <Button type="submit" className="flex-1" disabled={loading}>{loading ? "Submitting..." : "Accept and submit"}</Button>
                  </>}
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
