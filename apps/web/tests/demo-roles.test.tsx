import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { DemoAuthContext, type DemoAuthValue } from "../components/auth/DemoAuthContext";
import WorkspaceShell from "../components/workflow/WorkspaceShell";
import {
  ACTIVE_DEMO_ROLES,
  DEMO_ROLE_CONFIG,
  isActiveDemoRole,
  isDemoRouteAvailable,
  normalizeDemoRole,
} from "../lib/demo-roles";
import type { Role } from "../lib/types";

const navigation = vi.hoisted(() => ({
  pathname: "/dashboard",
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
  useRouter: () => ({ replace: navigation.replace }),
}));

afterEach(() => {
  vi.unstubAllGlobals();
  navigation.pathname = "/dashboard";
  navigation.replace.mockReset();
});

const grantAdminAuth: DemoAuthValue = {
  accessToken: "server-issued-admin-token",
  identity: {
    user_id: "demo-grant-administrator",
    email: "admin@shakahive.demo",
    workspace: "GRANT_ADMINISTRATOR",
  },
  login: vi.fn(),
  logout: vi.fn(),
};

function renderWorkspace(
  pathname = "/dashboard",
  auth: DemoAuthValue = grantAdminAuth,
) {
  navigation.pathname = pathname;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("[]", { status: 200 })));
  return render(
    <DemoAuthContext.Provider value={auth}>
      <WorkspaceShell><div data-testid="page-content">Current page</div></WorkspaceShell>
    </DemoAuthContext.Provider>,
  );
}

describe("demo role configuration", () => {
  it("defines only the implemented Grant Administrator workflow as selectable", () => {
    expect(ACTIVE_DEMO_ROLES).toEqual(["GRANT_ADMINISTRATOR"]);
    expect(DEMO_ROLE_CONFIG.GRANT_ADMINISTRATOR.navigation.map(({ label }) => label)).toEqual([
      "Overview",
      "Research Check",
      "Grant Calls",
      "Applications",
      "Duplication",
      "Screening",
      "Report",
    ]);

    const availableRoutes = [
      "/dashboard",
      "/dashboard/check",
      "/dashboard/calls",
      "/dashboard/calls?id=call-1",
      "/dashboard/applications",
      "/dashboard/applications/view",
      "/dashboard/duplication",
      "/dashboard/screening",
      "/dashboard/report",
    ];
    for (const route of availableRoutes) {
      expect(isDemoRouteAvailable("GRANT_ADMINISTRATOR", route.split("?")[0])).toBe(true);
    }
    expect(isDemoRouteAvailable("GRANT_ADMINISTRATOR", "/dashboard/publications")).toBe(false);
  });

  it.each([
    ["NCST_GRANT_PERSONNEL", "unsupported"],
    ["GRANT_INSTITUTION", "unsupported"],
    ["RESEARCHER_APPLICANT", "unsupported"],
    ["REVIEWER", "legacy"],
    ["SYSTEM_ADMINISTRATOR", "legacy"],
  ] as const)("keeps %s inactive because it has no safe implemented workspace", (role, status) => {
    const definition = DEMO_ROLE_CONFIG[role];
    expect(definition.status).toBe(status);
    expect(definition.navigation).toEqual([]);
    expect(definition.routePrefixes).toEqual([]);
    expect(Object.values(definition.capabilities).every((capability) => !capability)).toBe(true);
    expect(isDemoRouteAvailable(role, "/dashboard")).toBe(false);
  });

  it("normalizes old persisted and unsupported roles to the active demo role", () => {
    const allRoles: Role[] = [
      "NCST_GRANT_PERSONNEL",
      "GRANT_INSTITUTION",
      "RESEARCHER_APPLICANT",
      "GRANT_ADMINISTRATOR",
      "REVIEWER",
      "SYSTEM_ADMINISTRATOR",
    ];
    for (const role of allRoles) {
      expect(normalizeDemoRole(role)).toBe("GRANT_ADMINISTRATOR");
      expect(isActiveDemoRole(role)).toBe(role === "GRANT_ADMINISTRATOR");
    }
    expect(normalizeDemoRole(null)).toBe("GRANT_ADMINISTRATOR");
  });
});

describe("demo workspace navigation", () => {
  it("shows the authenticated workspace and its active navigation", async () => {
    renderWorkspace();

    const roleDisplay = screen.getByRole("group", { name: "AUTHENTICATED DEMO WORKSPACE" });
    expect(roleDisplay.textContent).toContain("Grant Administrator (demo workflow)");
    expect(roleDisplay.textContent).toContain("admin@shakahive.demo");
    expect(screen.queryByText(/role is sent as a header/i)).toBeNull();
    expect(screen.getByLabelText("Current demo role: Grant Administrator (demo workflow)")).toBeTruthy();
    const navigationLinks = [...screen.getByRole("navigation", { name: "Grant screening" }).querySelectorAll("a")];
    expect(navigationLinks.map((link) => link.textContent?.trim())).toEqual([
      "Overview",
      "Research Check",
      "Grant Calls",
      "Applications",
      "Duplication",
      "Screening",
      "Report",
    ]);
    expect(screen.getByRole("link", { name: "Overview" }).getAttribute("aria-current")).toBe("page");
    expect(screen.queryByLabelText("DEMO ROLE")).toBeNull();
    expect(screen.queryByRole("link", { name: /Publications/ })).toBeNull();
  });

  it("hides unavailable page content and redirects direct navigation to the role landing page", async () => {
    renderWorkspace("/dashboard/publications");

    expect(screen.getByText("Screen unavailable for this demo role")).toBeTruthy();
    expect(screen.queryByTestId("page-content")).toBeNull();
    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/dashboard"));
  });

  it("redirects an Applicant away from the Grant Administrator workspace", async () => {
    renderWorkspace("/dashboard/report", {
      ...grantAdminAuth,
      identity: {
        user_id: "demo-applicant",
        email: "applicant@shakahive.demo",
        workspace: "APPLICANT",
      },
    });

    expect(screen.queryByTestId("page-content")).toBeNull();
    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/applicant/dashboard"));
  });

  it("redirects unauthenticated navigation to login without mounting protected content", async () => {
    renderWorkspace("/dashboard/team-admin", { ...grantAdminAuth, accessToken: null, identity: null });

    expect(screen.queryByTestId("page-content")).toBeNull();
    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/login"));
  });
});
