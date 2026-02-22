import type { DebugInfo, Source } from "../types";

const BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

export interface QueryResponse {
  request_id: string;
  answer: string;
  sources: Source[];
  debug: DebugInfo;
}

export interface QueryStreamDonePayload {
  request_id: string;
  sources: Source[];
  debug: DebugInfo;
}

export interface IngestResponse {
  status: "success" | "error";
  filename: string;
  chunks_created: number;
  total_pages: number;
  processing_time_ms: number;
}

export interface DebugEntry {
  request_id: string;
  timestamp: string;
  query: string;
  classification: string;
  model_used: string;
  tokens_input: number;
  tokens_output: number;
  latency_ms: number;
  retrieval_count: number;
  evaluator_flags: string[];
  error: string | null;
}

export interface DebugResponse {
  entries: DebugEntry[];
  total_count: number;
}

export interface LogEntry {
  request_id: string;
  timestamp: string;
  query: string;
  classification: string;
  model_used: string;
  tokens_input: number;
  tokens_output: number;
  latency_ms: number;
  retrieval_count: number;
  retrieval_scores: number[];
  evaluator_flags: string[];
  error: string | null;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  offset: number;
  limit: number;
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  faiss_index_loaded: boolean;
  total_chunks: number;
  groq_api_reachable: boolean;
  uptime_seconds: number;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function withTimeout(signal: AbortSignal, ms: number): AbortSignal {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ms);
  signal.addEventListener("abort", () => {
    clearTimeout(timeout);
    controller.abort();
  });
  return controller.signal;
}

async function handleErrorResponse(response: Response): Promise<never> {
  let message = `Request failed with status ${response.status}`;
  let requestId: string | undefined;
  try {
    const body = (await response.json()) as {
      error?: string;
      request_id?: string;
    };
    if (body.error) message = body.error;
    requestId = body.request_id;
  } catch {
    // ignore JSON parse failure
  }
  throw new ApiError(response.status, message, requestId);
}

/**
 * POST /api/query (non-streaming). Returns the full parsed response.
 */
export async function postQuery(
  query: string,
  stream: false,
): Promise<QueryResponse>;

/**
 * POST /api/query (streaming). Returns a ReadableStream reader for SSE parsing.
 */
export async function postQuery(
  query: string,
  stream: true,
): Promise<ReadableStreamDefaultReader<Uint8Array>>;

export async function postQuery(
  query: string,
  stream: boolean,
): Promise<QueryResponse | ReadableStreamDefaultReader<Uint8Array>> {
  const outerController = new AbortController();
  const signal = withTimeout(outerController.signal, 30_000);

  const response = await fetch(`${BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, stream }),
    signal,
  });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  if (stream) {
    if (!response.body) {
      throw new ApiError(500, "Response body is null for streaming request");
    }
    return response.body.getReader();
  }

  return (await response.json()) as QueryResponse;
}

/**
 * POST /api/ingest — multipart file upload.
 */
export async function postIngest(file: File): Promise<IngestResponse> {
  const outerController = new AbortController();
  const signal = withTimeout(outerController.signal, 120_000);

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/api/ingest`, {
    method: "POST",
    body: formData,
    signal,
  });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  return (await response.json()) as IngestResponse;
}

/**
 * GET /api/debug?n=N — retrieve debug info for last N queries.
 */
export async function getDebug(n: number = 10): Promise<DebugResponse> {
  const outerController = new AbortController();
  const signal = withTimeout(outerController.signal, 30_000);

  const response = await fetch(`${BASE_URL}/api/debug?n=${n}`, { signal });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  return (await response.json()) as DebugResponse;
}

/**
 * GET /api/logs?offset=O&limit=L — retrieve paginated raw logs.
 */
export async function getLogs(
  offset: number = 0,
  limit: number = 50,
): Promise<LogsResponse> {
  const outerController = new AbortController();
  const signal = withTimeout(outerController.signal, 30_000);

  const response = await fetch(
    `${BASE_URL}/api/logs?offset=${offset}&limit=${limit}`,
    { signal },
  );

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  return (await response.json()) as LogsResponse;
}

/**
 * GET /api/health — health check.
 */
export async function getHealth(): Promise<HealthResponse> {
  const outerController = new AbortController();
  const signal = withTimeout(outerController.signal, 30_000);

  const response = await fetch(`${BASE_URL}/api/health`, { signal });

  if (!response.ok) {
    await handleErrorResponse(response);
  }

  return (await response.json()) as HealthResponse;
}
