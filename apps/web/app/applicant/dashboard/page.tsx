"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useDemoAuth } from "../../../components/auth/DemoAuthContext";
import styles from "../../login/login.module.css";

export default function ApplicantDashboardPage() {
  const router = useRouter();
  const { accessToken, identity, logout } = useDemoAuth();
  const [logoutError, setLogoutError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) router.replace("/login");
    else if (identity?.workspace === "GRANT_ADMINISTRATOR") router.replace("/dashboard");
  }, [accessToken, identity?.workspace, router]);

  if (!accessToken || identity?.workspace !== "APPLICANT") {
    return <main className={styles.page}><p role="status">Opening the Applicant workspace…</p></main>;
  }

  const signOut = async () => {
    setLogoutError(null);
    try {
      await logout();
    } catch (error) {
      setLogoutError(error instanceof Error ? error.message : "The server session could not be revoked.");
    } finally {
      router.replace("/login");
    }
  };

  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="applicant-dashboard-title">
        <p className={styles.eyebrow}>APPLICANT WORKSPACE</p>
        <h1 id="applicant-dashboard-title">Applicant Dashboard</h1>
        <p className={styles.intro}>Signed in as {identity.email}.</p>
        <p>Applicant authentication is active. Application discovery and submission are planned for Phase 2.</p>
        <p className={styles.footer}>Synthetic demonstration only. No application data is available in this phase.</p>
        {logoutError && <p className={styles.error} role="alert">{logoutError}</p>}
        <button className="dark-button" type="button" onClick={() => void signOut()}>Sign out</button>
      </section>
    </main>
  );
}
