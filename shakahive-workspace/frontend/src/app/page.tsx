"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Brain, 
  ShieldCheck, 
  FileText, 
  Users, 
  BarChart3, 
  Database,
  CheckCircle2,
  Zap,
  Globe,
  LogIn
} from "lucide-react";
import { useEffect, useState } from "react";

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">ShakaHive</h1>
              <Badge variant="secondary">NRIF Edition</Badge>
            </div>
            <nav className="flex gap-4">
              {isAuthenticated ? (
                <>
                  <Link href="/applications">
                    <Button variant="ghost">Applications</Button>
                  </Link>
                  <Link href="/screening">
                    <Button variant="ghost">Screening</Button>
                  </Link>
                  <Link href="/registry">
                    <Button variant="ghost">Registry</Button>
                  </Link>
                  <Link href="/dashboard">
                    <Button variant="ghost">Dashboard</Button>
                  </Link>
                </>
              ) : (
                <div className="flex gap-2">
                  <Link href="/login">
                    <Button>
                      <LogIn className="h-4 w-4 mr-2" />
                      Login
                    </Button>
                  </Link>
                  <Link href="/register">
                    <Button variant="outline">
                      Register
                    </Button>
                  </Link>
                </div>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-3xl">
          <Badge className="mb-4" variant="secondary">AI-Powered Grant Screening for NRIF</Badge>
          <h2 className="text-5xl font-bold text-slate-900 dark:text-white mb-6">
            Transform NRIF Grant Screening with AI
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 mb-8">
            ShakaHive uses advanced AI to automate eligibility checks, plagiarism detection,
            duplication analysis, and novelty assessment specifically for National Research & Innovation Fund grant applications.
          </p>
          <div className="flex gap-4">
            {isAuthenticated ? (
              <>
                <Link href="/applications/new">
                  <Button size="lg">
                    Submit Application
                  </Button>
                </Link>
                <Link href="/dashboard">
                  <Button size="lg" variant="outline">
                    View Dashboard
                  </Button>
                </Link>
              </>
            ) : (
              <Link href="/login">
                <Button size="lg">
                  <LogIn className="h-4 w-4 mr-2" />
                  Login to Get Started
                </Button>
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Platform Features */}
      <section className="container mx-auto px-4 py-16">
        <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-8 text-center">
          AI-Powered Screening Capabilities
        </h3>
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader>
              <ShieldCheck className="h-10 w-10 text-blue-600 mb-2" />
              <CardTitle>Eligibility Check</CardTitle>
              <CardDescription>
                Automated verification against NRIF grant eligibility criteria including institution type, budget limits, and team requirements
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <FileText className="h-10 w-10 text-green-600 mb-2" />
              <CardTitle>Plagiarism Detection</CardTitle>
              <CardDescription>
                GPU-accelerated AI using sentence transformers for semantic similarity analysis against reference databases
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Database className="h-10 w-10 text-purple-600 mb-2" />
              <CardTitle>Duplication Check</CardTitle>
              <CardDescription>
                Fuzzy matching and semantic search to identify duplicate proposals across RIGMS historical database
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Brain className="h-10 w-10 text-orange-600 mb-2" />
              <CardTitle>Novelty Assessment</CardTitle>
              <CardDescription>
                ML-based evaluation of technical, methodological, application, and market novelty using GPU acceleration
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <Users className="h-10 w-10 text-pink-600 mb-2" />
              <CardTitle>Identity Registry</CardTitle>
              <CardDescription>
                Permanent researcher identity management with ORCID integration and cross-tenant linking
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <BarChart3 className="h-10 w-10 text-cyan-600 mb-2" />
              <CardTitle>Analytics Dashboard</CardTitle>
              <CardDescription>
                Real-time insights on screening results, approval rates, and system performance metrics
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* System Status */}
      <section className="container mx-auto px-4 py-16">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              System Status
            </CardTitle>
            <CardDescription>Platform services operational status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="font-medium text-slate-700 dark:text-slate-300">API Gateway</span>
                <Badge variant="default" className="bg-green-500">Operational</Badge>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="font-medium text-slate-700 dark:text-slate-300">Eligibility Service</span>
                <Badge variant="default" className="bg-green-500">Operational</Badge>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="font-medium text-slate-700 dark:text-slate-300">Plagiarism Service</span>
                <Badge variant="default" className="bg-green-500">Operational</Badge>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="font-medium text-slate-700 dark:text-slate-300">Duplication Service</span>
                <Badge variant="default" className="bg-green-500">Operational</Badge>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="font-medium text-slate-700 dark:text-slate-300">Novelty Service</span>
                <Badge variant="default" className="bg-green-500">Operational</Badge>
              </div>
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="font-medium text-slate-700 dark:text-slate-300">Database</span>
                <Badge variant="default" className="bg-green-500">Operational</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm dark:bg-slate-900/80 mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-blue-600" />
              <span className="font-semibold text-slate-900 dark:text-white">ShakaHive</span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              AI-Powered Grant Screening Platform for National Research & Innovation Fund (NRIF)
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
