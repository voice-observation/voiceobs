/**
 * Base API client with shared utilities and HTTP methods.
 */

export interface ApiError {
  error: string;
  message: string;
  detail?: string;
}

// Get API URL - use proxy on client-side, direct URL on server-side
export const getApiBaseUrl = (): string => {
  // Client-side: use Next.js proxy
  if (typeof window !== "undefined") {
    return "/api";
  }
  // Server-side: use direct URL
  // Next.js provides process.env in server-side context
  return (
    (process.env as { NEXT_PUBLIC_API_URL?: string }).NEXT_PUBLIC_API_URL || "http://localhost:8765"
  );
};

// Simulate network delay (optional, for realism)
export const simulateDelay = (ms: number = 300): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

export class BaseApiClient {
  protected maxRetries: number = 3;
  protected retryDelay: number = 1000;

  protected getBaseUrl(): string {
    return getApiBaseUrl();
  }

  protected async fetchWithRetry(
    endpoint: string,
    options: RequestInit = {},
    retries: number = this.maxRetries
  ): Promise<Response> {
    const baseUrl = this.getBaseUrl();
    // If endpoint already starts with /api, don't prepend base URL on client-side
    const url =
      endpoint.startsWith("/api") && typeof window !== "undefined"
        ? endpoint
        : `${baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      if (!response.ok) {
        if (response.status >= 500 && retries > 0) {
          // Retry on server errors
          await new Promise((resolve) => setTimeout(resolve, this.retryDelay));
          return this.fetchWithRetry(endpoint, options, retries - 1);
        }

        let error: ApiError;
        try {
          error = await response.json();
        } catch {
          error = {
            error: "unknown",
            message: `HTTP ${response.status}: ${response.statusText}`,
          };
        }
        throw new Error(error.message || `API request failed: ${response.statusText}`);
      }

      return response;
    } catch (error) {
      if (retries > 0 && error instanceof TypeError) {
        // Network error, retry
        await new Promise((resolve) => setTimeout(resolve, this.retryDelay));
        return this.fetchWithRetry(endpoint, options, retries - 1);
      }
      throw error;
    }
  }

  protected async get<T>(endpoint: string): Promise<T> {
    const response = await this.fetchWithRetry(endpoint, { method: "GET" });
    return response.json();
  }

  protected async post<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await this.fetchWithRetry(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    });
    return response.json();
  }

  protected async put<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await this.fetchWithRetry(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    return response.json();
  }

  protected async patch<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await this.fetchWithRetry(endpoint, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    return response.json();
  }

  protected async delete(endpoint: string): Promise<void> {
    await this.fetchWithRetry(endpoint, { method: "DELETE" });
  }
}
