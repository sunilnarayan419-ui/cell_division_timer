/**
 * Typed API client for the Cell Division Timer FastAPI backend.
 *
 * The backend is the single source of truth for biological calculations,
 * statistics, and the NCBI/PubMed literature integration — this client only
 * fetches and shapes data for display. It never talks to NCBI directly and
 * never touches any API key: the NCBI_API_KEY lives exclusively in the
 * backend's environment configuration.
 */

// Configurable at build time via `VITE_API_BASE_URL`; defaults to the local
// FastAPI dev server started with `uvicorn app.main:app`.
export const API_BASE_URL: string =
  (import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json", ...(init?.headers || {}) },
    ...init,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // Response was not JSON; fall back to the generic message above.
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export interface LiteratureArticle {
  pmid: string;
  title: string | null;
  authors: string[];
  journal: string | null;
  publication_date: string | null;
  doi: string | null;
  abstract: string | null;
  pubmed_url: string | null;
}

export interface LiteratureSearchResponse {
  query: string;
  count: number;
  total_available: number;
  articles: LiteratureArticle[];
  source: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  database: Record<string, unknown>;
}

export interface AnalyticsSummary {
  total_observations: number;
  outlier_count: number;
  clean_observation_count: number;
  unique_cells_count: number;
  unique_batches_count: number;
  division_duration_minutes: Record<string, number | null>;
  cell_cycle_duration_hours: Record<string, number | null>;
  growth_rate_per_hour: Record<string, number | null>;
}

/** GET /health */
export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

/** GET /api/v1/analytics/summary */
export function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  return request<AnalyticsSummary>("/api/v1/analytics/summary");
}

/**
 * GET /api/v1/literature/search
 *
 * Searches PubMed via the backend's NCBI E-utilities integration. Requires
 * the backend to have NCBI_API_KEY configured; if it isn't, the backend
 * returns HTTP 503 with a clear, safe error message (surfaced via ApiError).
 */
export function searchLiterature(
  query: string,
  options?: { retmax?: number; includeAbstracts?: boolean }
): Promise<LiteratureSearchResponse> {
  const params = new URLSearchParams({ query });
  if (options?.retmax) params.set("retmax", String(options.retmax));
  if (options?.includeAbstracts) params.set("include_abstracts", "true");
  return request<LiteratureSearchResponse>(`/api/v1/literature/search?${params.toString()}`);
}
