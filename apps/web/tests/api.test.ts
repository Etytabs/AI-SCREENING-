import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createClient } from "../lib/api";

const client = createClient({ role: "REVIEWER", userId: "demo-reviewer" }, "http://api.test");

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("uploads historical project metadata and a file as multipart data with identity headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "project-1" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["Research objectives"], "previous.txt", { type: "text/plain" });
    await client.importDuplicationProject({ file, title: "Previous project", source_type: "funded_project", year: 2024, reference: "FUND-17", organization: "Research Council" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/duplication/projects");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ "X-User-Role": "REVIEWER", "X-User-Id": "demo-reviewer" });
    expect(init.headers["Content-Type"]).toBeUndefined();
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.body.get("file")).toBe(file);
    expect(init.body.get("source_type")).toBe("funded_project");
    expect(init.body.get("title")).toBe("Previous project");
    expect(init.body.get("year")).toBe("2024");
    expect(init.body.get("reference")).toBe("FUND-17");
    expect(init.body.get("organization")).toBe("Research Council");
  });

  it("loads stakeholder context with the demo identity headers", async () => {
    const payload = { stakeholders: [], primary_user_order: [], human_review_required: true };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(client.stakeholders()).resolves.toEqual(payload);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/ncst/stakeholders");
    expect(init.method).toBe("GET");
    expect(init.headers).toMatchObject({ "X-User-Role": "REVIEWER", "X-User-Id": "demo-reviewer" });
  });

  it("sends the demo identity headers and JSON body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "d-1" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    await client.decide("f-1", "CONFIRM", "Checked the budget annex");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/findings/f-1/decision");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ "X-User-Role": "REVIEWER", "X-User-Id": "demo-reviewer", "Content-Type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({ action: "CONFIRM", note: "Checked the budget annex" });
  });

  it("surfaces the API detail message and status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Reviewer cannot launch screening" }), { status: 403 })));
    const error = await client.screenCall("call-1").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(403);
    expect(error.message).toBe("Reviewer cannot launch screening");
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
