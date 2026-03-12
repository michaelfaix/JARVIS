// =============================================================================
// Integration Tests: Backend health check + CSS loading
// =============================================================================

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

import { getHealth } from "@/lib/api";

describe("Backend Health Check", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("calls /api/v1/health endpoint", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: "ok" }),
    });

    const result = await getHealth();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/health"),
      expect.objectContaining({
        headers: { "Content-Type": "application/json" },
      })
    );
    expect(result.status).toBe("ok");
  });

  it("throws on non-200 response", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
    });

    await expect(getHealth()).rejects.toThrow("API Error 503");
  });

  it("throws on network error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    await expect(getHealth()).rejects.toThrow("Network error");
  });

  it("returns correct health status structure", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: "healthy" }),
    });

    const result = await getHealth();
    expect(result).toHaveProperty("status");
    expect(typeof result.status).toBe("string");
  });
});

describe("API Client", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("uses correct API base URL", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: "ok" }),
    });

    await getHealth();

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toMatch(/\/api\/v1\/health$/);
  });

  it("sends JSON content-type header", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: "ok" }),
    });

    await getHealth();

    const options = mockFetch.mock.calls[0][1];
    expect(options.headers["Content-Type"]).toBe("application/json");
  });
});
