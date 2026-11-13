"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { useDemoAuth } from "../../components/auth/DemoAuthContext";
import type { DemoWorkspace } from "../../lib/api";
import logo from "../../public/brand/logo-on-dark.png";
import styles from "./login.module.css";

const DEMO_CREDENTIALS = {
  APPLICANT: { email: "applicant@shakahive.demo", password: "Applicant123!" },
  GRANT_ADMINISTRATOR: { email: "admin@shakahive.demo", password: "Admin123!" },
} satisfies Record<DemoWorkspace, { email: string; password: string }>;

export default function LoginPage() {
  const router = useRouter();
  const { identity, login } = useDemoAuth();
  const [workspace, setWorkspace] = useState<DemoWorkspace>("APPLICANT");
  const [email, setEmail] = useState(DEMO_CREDENTIALS.APPLICANT.email);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (identity) {
      router.replace(identity.workspace === "APPLICANT" ? "/applicant/dashboard" : "/dashboard");
    }
  }, [identity, router]);

  const chooseWorkspace = (next: DemoWorkspace) => {
    setWorkspace(next);
    setEmail(DEMO_CREDENTIALS[next].email);
    setPassword("");
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const authenticated = await login({ email, password, workspace });
      router.replace(authenticated.workspace === "APPLICANT" ? "/applicant/dashboard" : "/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <Link href="/" className={styles.brand} aria-label="ShakaHive home">
          <Image src={logo} alt="ShakaHive" priority />
          <span>Research Intelligence</span>
        </Link>
        <p className={styles.eyebrow}>CONTROLLED PRODUCT DEMONSTRATION</p>
        <h1>Sign in to ShakaHive</h1>
        <p className={styles.intro}>Choose your workspace and enter its demonstration credentials.</p>

        <form onSubmit={submit} aria-label="ShakaHive login">
          <label htmlFor="workspace">Workspace</label>
          <select
            id="workspace"
            value={workspace}
            onChange={(event) => chooseWorkspace(
              event.currentTarget.value === "GRANT_ADMINISTRATOR"
                ? "GRANT_ADMINISTRATOR"
                : "APPLICANT",
            )}
          >
            <option value="APPLICANT">Applicant</option>
            <option value="GRANT_ADMINISTRATOR">Grant Administrator</option>
          </select>

          <label htmlFor="email">Demo email</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error && <p className={styles.error} role="alert">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <details className={styles.credentials}>
          <summary>Show demonstration credentials</summary>
          <dl>
            <dt>Applicant</dt>
            <dd>{DEMO_CREDENTIALS.APPLICANT.email} · {DEMO_CREDENTIALS.APPLICANT.password}</dd>
            <dt>Grant Administrator</dt>
            <dd>{DEMO_CREDENTIALS.GRANT_ADMINISTRATOR.email} · {DEMO_CREDENTIALS.GRANT_ADMINISTRATOR.password}</dd>
          </dl>
          <small>These public credentials work only when the synthetic demo authentication mode is enabled.</small>
        </details>

        <p className={styles.footer}>Synthetic demonstration only. Do not enter real applicant or institutional data.</p>
      </section>
    </main>
  );
}
