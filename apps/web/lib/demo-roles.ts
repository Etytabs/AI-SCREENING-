import type { Role } from "./types";

export type DemoNavigationItem = { href: string; label: string };
export type DemoRoleStatus = "active" | "legacy" | "unsupported";

export interface DemoRoleDefinition {
  label: string;
  status: DemoRoleStatus;
  explanation: string;
  landingPath: string;
  navigation: readonly DemoNavigationItem[];
  routePrefixes: readonly string[];
  capabilities: {
    canManageGrantCalls: boolean;
    canUploadApplications: boolean;
    canRunScreening: boolean;
    canImportComparisonProjects: boolean;
    canReviewFindings: boolean;
  };
}

const GRANT_ADMIN_NAVIGATION = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/check", label: "Research Check" },
  { href: "/dashboard/calls", label: "Grant Calls" },
  { href: "/dashboard/applications", label: "Applications" },
  { href: "/dashboard/duplication", label: "Duplication" },
  { href: "/dashboard/screening", label: "Screening" },
  { href: "/dashboard/report", label: "Report" },
] as const satisfies readonly DemoNavigationItem[];

const GRANT_ADMIN_ROUTES = [
  "/dashboard",
  "/dashboard/check",
  "/dashboard/calls",
  "/dashboard/applications",
  "/dashboard/duplication",
  "/dashboard/screening",
  "/dashboard/report",
] as const;

const NO_CAPABILITIES: DemoRoleDefinition["capabilities"] = {
  canManageGrantCalls: false,
  canUploadApplications: false,
  canRunScreening: false,
  canImportComparisonProjects: false,
  canReviewFindings: false,
};

const INACTIVE_ROLE = {
  landingPath: "/dashboard",
  navigation: [],
  routePrefixes: [],
  capabilities: NO_CAPABILITIES,
} as const;

export const DEMO_ROLE_CONFIG: Record<Role, DemoRoleDefinition> = {
  NCST_GRANT_PERSONNEL: {
    ...INACTIVE_ROLE,
    label: "NCST Grant Personnel",
    status: "unsupported",
    explanation: "No approved mapping to the Grant Administrator role exists; the old UI mapped this label to the administrator API role.",
  },
  GRANT_INSTITUTION: {
    ...INACTIVE_ROLE,
    label: "Grant Institution",
    status: "unsupported",
    explanation: "No institution-owned submissions or institution-scoped views are implemented.",
  },
  RESEARCHER_APPLICANT: {
    ...INACTIVE_ROLE,
    label: "Researcher / Applicant",
    status: "unsupported",
    explanation: "No applicant-owned application or publication workspace is implemented.",
  },
  GRANT_ADMINISTRATOR: {
    label: "Grant Administrator (demo workflow)",
    status: "active",
    explanation: "Demonstrates the implemented grant-call, application, screening and review workflow using the existing Grant Administrator API role.",
    landingPath: "/dashboard",
    navigation: GRANT_ADMIN_NAVIGATION,
    routePrefixes: GRANT_ADMIN_ROUTES,
    capabilities: {
      canManageGrantCalls: true,
      canUploadApplications: true,
      canRunScreening: true,
      canImportComparisonProjects: true,
      canReviewFindings: true,
    },
  },
  REVIEWER: {
    ...INACTIVE_ROLE,
    label: "Reviewer (legacy)",
    status: "legacy",
    explanation: "Reviewer assignment scoping is not implemented, so a reviewer cannot be safely limited to assigned calls or applications.",
  },
  SYSTEM_ADMINISTRATOR: {
    ...INACTIVE_ROLE,
    label: "System Administrator (legacy)",
    status: "legacy",
    explanation: "No ShakaHive Team Admin account, invitation, suspension or role-management screens are implemented.",
  },
};

export const ACTIVE_DEMO_ROLES = ["GRANT_ADMINISTRATOR"] as const satisfies readonly Role[];

export function isActiveDemoRole(value: string): value is (typeof ACTIVE_DEMO_ROLES)[number] {
  return ACTIVE_DEMO_ROLES.some((role) => role === value);
}

export function normalizeDemoRole(value: string | null): Role {
  return value && isActiveDemoRole(value) ? value : ACTIVE_DEMO_ROLES[0];
}

export function isDemoRouteAvailable(role: Role, pathname: string): boolean {
  const normalizedPath = pathname.replace(/\/+$/, "") || "/";
  return DEMO_ROLE_CONFIG[role].routePrefixes.some(
    (prefix) =>
      normalizedPath === prefix ||
      (prefix !== "/dashboard" && normalizedPath.startsWith(`${prefix}/`)),
  );
}
