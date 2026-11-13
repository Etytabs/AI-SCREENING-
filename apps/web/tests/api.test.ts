import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  createClient,
  DEMO_SESSION_EXPIRED_EVENT,
  loginDemo,
} from "../lib/api";

const client = createClient("demo-access-token", "http://api.test");

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("sends only the server-issued bearer token, never client-supplied identity headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("[]", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await client.listCalls();
    expect(fetchMock.mock.calls[0][1].headers).toMatchObject({
      Authorization: "Bearer demo-access-token",
    });
    expect(fetchMock.mock.calls[0][1].headers["X-User-Role"]).toBeUndefined();
    expect(fetchMock.mock.calls[0][1].headers["X-User-Id"]).toBeUndefined();
    expect(fetchMock.mock.calls[0][1].cache).toBe("no-store");
    expect(fetchMock.mock.calls[0][1].credentials).toBe("omit");
  });

  it("uploads historical project metadata and a file as multipart data with the authenticated session", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "project-1" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["Research objectives"], "previous.txt", { type: "text/plain" });
    await client.importDuplicationProject({ file, title: "Previous project", source_type: "funded_project", year: 2024, reference: "FUND-17", organization: "Research Council" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/duplication/projects");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ Authorization: "Bearer demo-access-token" });
    expect(init.headers["Content-Type"]).toBeUndefined();
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.body.get("file")).toBe(file);
    expect(init.body.get("source_type")).toBe("funded_project");
    expect(init.body.get("title")).toBe("Previous project");
    expect(init.body.get("year")).toBe("2024");
    expect(init.body.get("reference")).toBe("FUND-17");
    expect(init.body.get("organization")).toBe("Research Council");
  });

  it("loads stakeholder context with the authenticated session", async () => {
    const payload = { stakeholders: [], primary_user_order: [], human_review_required: true };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(client.stakeholders()).resolves.toEqual(payload);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/ncst/stakeholders");
    expect(init.method).toBe("GET");
    expect(init.headers).toMatchObject({ Authorization: "Bearer demo-access-token" });
  });

  it("sends the demo identity headers and JSON body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "d-1" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    await client.decide("f-1", "CONFIRM", "Checked the budget annex");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/findings/f-1/decision");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ Authorization: "Bearer demo-access-token", "Content-Type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({ action: "CONFIRM", note: "Checked the budget annex" });
  });

  it("surfaces the API detail message and status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Reviewer cannot launch screening" }), { status: 403 })));
    const error = await client.screenCall("call-1").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(403);
    expect(error.message).toBe("Reviewer cannot launch screening");
  });

  it("announces an expired authenticated session when the API returns 401", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: "Authentication required" }),
      { status: 401 },
    ));
    const expired = vi.fn();
    window.addEventListener(DEMO_SESSION_EXPIRED_EVENT, expired);
    vi.stubGlobal("fetch", fetchMock);
    try {
      await expect(client.listCalls()).rejects.toMatchObject({ status: 401 });
      expect(expired).toHaveBeenCalledOnce();
    } finally {
      window.removeEventListener(DEMO_SESSION_EXPIRED_EVENT, expired);
    }
  });

  it("submits the selected workspace and credentials without an existing session", async () => {
    const identity = {
      user_id: "demo-applicant",
      email: "applicant@shakahive.demo",
      workspace: "APPLICANT",
    };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      access_token: "issued-token",
      token_type: "Bearer",
      expires_in: 900,
      identity,
    }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(loginDemo({
      email: "applicant@shakahive.demo",
      password: "Applicant123!",
      workspace: "APPLICANT",
    }, "http://api.test")).resolves.toMatchObject({ identity, access_token: "issued-token" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/auth/login");
    expect(init.headers.Authorization).toBeUndefined();
    expect(init.cache).toBe("no-store");
    expect(init.credentials).toBe("omit");
    expect(JSON.parse(init.body)).toEqual({
      email: "applicant@shakahive.demo",
      password: "Applicant123!",
      workspace: "APPLICANT",
    });
  });

  it("reports an unreachable API instead of showing stale data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const error = await client.listCalls().catch((e) => e);
    expect(error.status).toBe(0);
    expect(error.message).toContain("unreachable");
  });

  it("encodes result filters as query parameters and skips empty ones", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("[]", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await client.listApplications("call-1", { eligibility: "FAIL", q: undefined, flagged: "true" });
    expect(fetchMock.mock.calls[0][0]).toBe("http://api.test/api/v1/grants/call-1/applications?eligibility=FAIL&flagged=true");
  });
});
