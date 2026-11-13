import { useEffect } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DemoAuthProvider, useDemoAuth } from "../components/auth/DemoAuthContext";
import { useWorkspace } from "../components/workflow/WorkspaceContext";
import WorkspaceShell from "../components/workflow/WorkspaceShell";
import LoginPage from "../app/login/page";
import { DEMO_SESSION_EXPIRED_EVENT } from "../lib/api";

const navigation = vi.hoisted(() => ({ replace: vi.fn() }));

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({ replace: navigation.replace }),
}));

vi.mock("next/image", () => ({
  default: ({ priority: _priority, ...props }: { src: string; alt: string; priority?: boolean }) => (
    <img {...props} />
  ),
}));

afterEach(() => {
  vi.unstubAllGlobals();
  navigation.replace.mockReset();
});

function renderLogin() {
  return render(<DemoAuthProvider><LoginPage /></DemoAuthProvider>);
}

describe("unified demo login", () => {
  it("authenticates the selected Applicant workspace and routes to its dashboard", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      access_token: "applicant-session",
      token_type: "Bearer",
      expires_in: 900,
      identity: {
        user_id: "demo-applicant",
        email: "applicant@shakahive.demo",
        workspace: "APPLICANT",
      },
    }), { status: 200 })));
    renderLogin();

    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Applicant123!" } });
    fireEvent.submit(screen.getByRole("form", { name: "ShakaHive login" }));

    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/applicant/dashboard"));
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/login"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "applicant@shakahive.demo",
          password: "Applicant123!",
          workspace: "APPLICANT",
        }),
      }),
    );
  });

  it("routes a successfully authenticated Grant Administrator to the admin dashboard", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      access_token: "admin-session",
      token_type: "Bearer",
      expires_in: 900,
      identity: {
        user_id: "demo-grant-administrator",
        email: "admin@shakahive.demo",
        workspace: "GRANT_ADMINISTRATOR",
      },
    }), { status: 200 })));
    renderLogin();

    fireEvent.change(screen.getByLabelText("Workspace"), { target: { value: "GRANT_ADMINISTRATOR" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Admin123!" } });
    fireEvent.submit(screen.getByRole("form", { name: "ShakaHive login" }));

    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/dashboard"));
  });

  it("shows a clear error and does not redirect when credentials are invalid", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: "Invalid email, password, or workspace" }),
      { status: 401 },
    )));
    renderLogin();

    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } });
    fireEvent.submit(screen.getByRole("form", { name: "ShakaHive login" }));

    expect((await screen.findByRole("alert")).textContent).toContain("Invalid email, password, or workspace");
    expect(navigation.replace).not.toHaveBeenCalled();
  });

  it("clears the in-memory identity when the API reports an expired session", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      access_token: "applicant-session",
      token_type: "Bearer",
      expires_in: 900,
      identity: {
        user_id: "demo-applicant",
        email: "applicant@shakahive.demo",
        workspace: "APPLICANT",
      },
    }), { status: 200 })));

    function SessionProbe() {
      const { identity, login } = useDemoAuth();
      return (
        <>
          <span>{identity?.workspace ?? "signed out"}</span>
          <button onClick={() => void login({
            email: "applicant@shakahive.demo",
            password: "Applicant123!",
            workspace: "APPLICANT",
          })}>Authenticate</button>
        </>
      );
    }

    render(<DemoAuthProvider><SessionProbe /></DemoAuthProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Authenticate" }));
    await waitFor(() => expect(screen.getByText("APPLICANT")).toBeTruthy());

    window.dispatchEvent(new Event(DEMO_SESSION_EXPIRED_EVENT));
    await waitFor(() => expect(screen.getByText("signed out")).toBeTruthy());
  });

  it("expires an active workspace, clears its state, redirects, and permits re-login", async () => {
    let loginCount = 0;
    let workspaceMounted = false;
    let workspaceUnmounted = false;
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      if (String(input).endsWith("/api/v1/auth/login")) {
        loginCount += 1;
        return Promise.resolve(new Response(JSON.stringify({
          access_token: `session-${loginCount}`,
          token_type: "Bearer",
          expires_in: loginCount === 1 ? 2 : 900,
          identity: {
            user_id: "demo-grant-administrator",
            email: "admin@shakahive.demo",
            workspace: "GRANT_ADMINISTRATOR",
          },
        }), { status: 200 }));
      }
      return Promise.resolve(new Response("[]", { status: 200 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    function ProtectedPage() {
      const { calls } = useWorkspace();
      useEffect(() => {
        workspaceMounted = true;
        return () => {
          workspaceMounted = false;
          workspaceUnmounted = true;
        };
      }, []);
      return <div data-testid="protected-content">Calls: {calls.length}</div>;
    }

    function SessionHarness() {
      const { accessToken, identity, login } = useDemoAuth();
      return (
        <>
          <span data-testid="session-state">{identity ? `${identity.email}:${accessToken}` : "signed out"}</span>
          <button onClick={() => void login({
            email: "admin@shakahive.demo",
            password: "Admin123!",
            workspace: "GRANT_ADMINISTRATOR",
          })}>Sign in</button>
          <WorkspaceShell><ProtectedPage /></WorkspaceShell>
        </>
      );
    }

    render(<DemoAuthProvider><SessionHarness /></DemoAuthProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await screen.findByTestId("protected-content");
    await waitFor(() => expect(workspaceMounted).toBe(true));
    expect(screen.getByTestId("session-state").textContent).toContain("session-1");
    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
    navigation.replace.mockClear();

    await waitFor(() => expect(screen.getByTestId("session-state").textContent).toBe("signed out"), {
      timeout: 4000,
      interval: 20,
    });
    expect(screen.queryByTestId("protected-content")).toBeNull();
    expect(workspaceUnmounted).toBe(true);
    expect(navigation.replace).toHaveBeenCalledWith("/login");
    const oldTokenRequests = fetchMock.mock.calls.filter(([, init]) => {
      const headers = init?.headers as Record<string, string> | undefined;
      return headers?.Authorization === "Bearer session-1";
    }).length;

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(screen.getByTestId("session-state").textContent).toContain("session-2"));
    await screen.findByTestId("protected-content");
    expect(loginCount).toBe(2);
    expect(fetchMock.mock.calls.filter(([, init]) => {
      const headers = init?.headers as Record<string, string> | undefined;
      return headers?.Authorization === "Bearer session-1";
    })).toHaveLength(oldTokenRequests);
  });
});
