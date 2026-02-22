import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useChat } from "../../src/hooks/useChat";
import * as apiClient from "../../src/services/apiClient";

vi.mock("../../src/services/apiClient");

const DONE_PAYLOAD = {
    request_id: "uuid-test-1",
    sources: [{ source_file: "test.pdf", page_number: 1, score: 0.9 }],
    debug: {
        classification: "simple" as const,
        model_used: "llama-3.1-8b-instant",
        tokens_input: 100,
        tokens_output: 20,
        latency_ms: 450,
        retrieval_count: 1,
        evaluator_flags: [],
    },
};

/**
 * Create a mock ReadableStreamDefaultReader that yields SSE chunks then closes.
 */
function makeStreamReader(chunks: string[]): ReadableStreamDefaultReader<Uint8Array> {
    const encoder = new TextEncoder();
    let i = 0;
    return {
        read: vi.fn(() => {
            if (i < chunks.length) {
                return Promise.resolve({ done: false, value: encoder.encode(chunks[i++]) });
            }
            return Promise.resolve({ done: true, value: undefined });
        }),
        cancel: vi.fn(),
        releaseLock: vi.fn(),
        closed: Promise.resolve(undefined),
    } as unknown as ReadableStreamDefaultReader<Uint8Array>;
}

describe("useChat", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should start with empty messages and no loading", () => {
        const { result } = renderHook(() => useChat());
        expect(result.current.messages).toHaveLength(0);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBeNull();
    });

    it("should add user message immediately when sendMessage is called", async () => {
        const chunks = [
            `event: token\ndata: {"token": "Hello"}\n\n`,
            `event: done\ndata: ${JSON.stringify(DONE_PAYLOAD)}\n\n`,
        ];
        vi.mocked(apiClient.postQuery).mockResolvedValue(makeStreamReader(chunks));

        const { result } = renderHook(() => useChat());
        act(() => {
            result.current.sendMessage("What is Clearpath?");
        });

        expect(result.current.messages[0].role).toBe("user");
        expect(result.current.messages[0].content).toBe("What is Clearpath?");
    });

    it("should set isLoading to true while fetching", async () => {
        const chunks = [
            `event: token\ndata: {"token": "Hello"}\n\n`,
            `event: done\ndata: ${JSON.stringify(DONE_PAYLOAD)}\n\n`,
        ];
        vi.mocked(apiClient.postQuery).mockResolvedValue(makeStreamReader(chunks));

        const { result } = renderHook(() => useChat());
        act(() => {
            result.current.sendMessage("What is Clearpath?");
        });
        expect(result.current.isLoading).toBe(true);
    });

    it("should accumulate tokens in assistant message", async () => {
        const chunks = [
            `event: token\ndata: {"token": "Hello "}\n\n`,
            `event: token\ndata: {"token": "world!"}\n\n`,
            `event: done\ndata: ${JSON.stringify(DONE_PAYLOAD)}\n\n`,
        ];
        vi.mocked(apiClient.postQuery).mockResolvedValue(makeStreamReader(chunks));

        const { result } = renderHook(() => useChat());
        await act(async () => {
            await result.current.sendMessage("What is Clearpath?");
        });

        const assistantMsg = result.current.messages.find((m) => m.role === "assistant");
        expect(assistantMsg?.content).toBe("Hello world!");
    });

    it("should populate debugInfo after done event", async () => {
        const chunks = [
            `event: token\ndata: {"token": "Answer"}\n\n`,
            `event: done\ndata: ${JSON.stringify(DONE_PAYLOAD)}\n\n`,
        ];
        vi.mocked(apiClient.postQuery).mockResolvedValue(makeStreamReader(chunks));

        const { result } = renderHook(() => useChat());
        await act(async () => {
            await result.current.sendMessage("What is Clearpath?");
        });

        expect(result.current.debugInfo).not.toBeNull();
        expect(result.current.debugInfo?.classification).toBe("simple");
        expect(result.current.debugInfo?.model_used).toBe("llama-3.1-8b-instant");
    });

    it("should set isLoading to false after completion", async () => {
        const chunks = [
            `event: done\ndata: ${JSON.stringify(DONE_PAYLOAD)}\n\n`,
        ];
        vi.mocked(apiClient.postQuery).mockResolvedValue(makeStreamReader(chunks));

        const { result } = renderHook(() => useChat());
        await act(async () => {
            await result.current.sendMessage("What is Clearpath?");
        });

        expect(result.current.isLoading).toBe(false);
    });

    it("should set error on network failure", async () => {
        vi.mocked(apiClient.postQuery).mockRejectedValue(new Error("Network error"));

        const { result } = renderHook(() => useChat());
        await act(async () => {
            await result.current.sendMessage("What is Clearpath?");
        });

        expect(result.current.error).toBeTruthy();
        expect(result.current.isLoading).toBe(false);
    });

    it("should toggle isDebugOpen when toggleDebug called", () => {
        const { result } = renderHook(() => useChat());
        expect(result.current.isDebugOpen).toBe(false);
        act(() => {
            result.current.toggleDebug();
        });
        expect(result.current.isDebugOpen).toBe(true);
        act(() => {
            result.current.toggleDebug();
        });
        expect(result.current.isDebugOpen).toBe(false);
    });

    it("should clear error when clearError is called", async () => {
        vi.mocked(apiClient.postQuery).mockRejectedValue(new Error("Fail"));

        const { result } = renderHook(() => useChat());
        await act(async () => {
            await result.current.sendMessage("What is Clearpath?");
        });
        expect(result.current.error).toBeTruthy();

        act(() => {
            result.current.clearError();
        });
        expect(result.current.error).toBeNull();
    });
});
