import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
    postQuery,
    postIngest,
    getHealth,
    getDebug,
    getLogs,
    ApiError,
} from "../../src/services/apiClient";

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

function makeMockResponse(body: unknown, status = 200, ok = true): Response {
    return {
        ok,
        status,
        json: () => Promise.resolve(body),
        text: () => Promise.resolve(JSON.stringify(body)),
        headers: new Headers({ "x-request-id": "test-uuid" }),
        body: null,
    } as unknown as Response;
}

describe("apiClient", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    // ---------------------------------------------------------------------------
    // postQuery — non-streaming
    // ---------------------------------------------------------------------------

    describe("postQuery (non-streaming)", () => {
        it("should POST to /api/query and return parsed JSON", async () => {
            const mockBody = {
                request_id: "uuid-1",
                answer: "Clearpath is great.",
                sources: [],
                debug: {
                    classification: "simple",
                    model_used: "llama-3.1-8b-instant",
                    tokens_input: 100,
                    tokens_output: 20,
                    latency_ms: 450,
                    retrieval_count: 1,
                    evaluator_flags: [],
                },
            };
            mockFetch.mockResolvedValue(makeMockResponse(mockBody));

            const result = await postQuery("What is Clearpath?", false);

            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining("/api/query"),
                expect.objectContaining({ method: "POST" })
            );
            expect(result).toMatchObject({ answer: "Clearpath is great." });
        });

        it("should throw ApiError on non-OK response", async () => {
            mockFetch.mockResolvedValue(
                makeMockResponse({ error: "Query too long" }, 400, false)
            );

            await expect(postQuery("x".repeat(2001), false)).rejects.toBeInstanceOf(ApiError);
        });
    });

    // ---------------------------------------------------------------------------
    // postIngest
    // ---------------------------------------------------------------------------

    describe("postIngest", () => {
        it("should POST multipart form to /api/ingest", async () => {
            const mockBody = {
                status: "success",
                filename: "doc.pdf",
                chunks_created: 5,
                total_pages: 2,
                processing_time_ms: 1200,
            };
            mockFetch.mockResolvedValue(makeMockResponse(mockBody));

            const file = new File(["%PDF-1.4"], "doc.pdf", { type: "application/pdf" });
            const result = await postIngest(file);

            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining("/api/ingest"),
                expect.objectContaining({ method: "POST" })
            );
            expect(result.status).toBe("success");
            expect(result.chunks_created).toBe(5);
        });

        it("should throw ApiError on 400 response", async () => {
            mockFetch.mockResolvedValue(
                makeMockResponse({ error: "Not a PDF" }, 400, false)
            );
            const file = new File(["text"], "doc.txt", { type: "text/plain" });
            await expect(postIngest(file)).rejects.toBeInstanceOf(ApiError);
        });
    });

    // ---------------------------------------------------------------------------
    // getHealth
    // ---------------------------------------------------------------------------

    describe("getHealth", () => {
        it("should GET /api/health and return health response", async () => {
            const mockBody = {
                status: "healthy",
                faiss_index_loaded: true,
                total_chunks: 100,
                groq_api_reachable: true,
                uptime_seconds: 3600,
            };
            mockFetch.mockResolvedValue(makeMockResponse(mockBody));

            const result = await getHealth();
            expect(result.status).toBe("healthy");
            expect(result.faiss_index_loaded).toBe(true);
        });
    });

    // ---------------------------------------------------------------------------
    // getDebug
    // ---------------------------------------------------------------------------

    describe("getDebug", () => {
        it("should GET /api/debug with default n=10", async () => {
            const mockBody = { entries: [], total_count: 0 };
            mockFetch.mockResolvedValue(makeMockResponse(mockBody));

            await getDebug();
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining("/api/debug?n=10"),
                expect.anything()
            );
        });

        it("should accept custom n parameter", async () => {
            const mockBody = { entries: [], total_count: 0 };
            mockFetch.mockResolvedValue(makeMockResponse(mockBody));

            await getDebug(25);
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining("n=25"),
                expect.anything()
            );
        });
    });

    // ---------------------------------------------------------------------------
    // getLogs
    // ---------------------------------------------------------------------------

    describe("getLogs", () => {
        it("should GET /api/logs with default offset and limit", async () => {
            const mockBody = { logs: [], total: 0, offset: 0, limit: 50 };
            mockFetch.mockResolvedValue(makeMockResponse(mockBody));

            await getLogs();
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining("offset=0"),
                expect.anything()
            );
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining("limit=50"),
                expect.anything()
            );
        });
    });

    // ---------------------------------------------------------------------------
    // ApiError
    // ---------------------------------------------------------------------------

    describe("ApiError", () => {
        it("should be an instance of Error", () => {
            const err = new ApiError(404, "Not found");
            expect(err).toBeInstanceOf(Error);
            expect(err).toBeInstanceOf(ApiError);
        });

        it("should carry status code and message", () => {
            const err = new ApiError(503, "Service unavailable", "req-123");
            expect(err.status).toBe(503);
            expect(err.message).toBe("Service unavailable");
            expect(err.requestId).toBe("req-123");
        });
    });
});
