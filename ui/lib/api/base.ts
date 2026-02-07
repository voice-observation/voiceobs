/**
 * Base API client with shared utilities and HTTP methods.
 */

import { createClient } from "@/lib/supabase/client";

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

// Track if we're already redirecting to prevent loops
let isRedirecting = false;

export class BaseApiClient {
  protected maxRetries: number = 3;
  protected retryDelay: number = 1000;

  protected getBaseUrl(): string {
    return getApiBaseUrl();
  }

  /**
   * Get authentication headers from Supabase session.
   * Only adds auth headers on client-side.
   */
  protected async getAuthHeaders(): Promise<Record<string, string>> {
    // Only add auth headers on client-side
    if (typeof window === "undefined") {
      return {};
    }

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token) {
        return {
          Authorization: `Bearer ${session.access_token}`,
        };
      }
    } catch (error) {
      console.error("Failed to get auth session:", error);
    }

    return {};
  }

  protected async fetchWithRetry(
    endpoint: string,
    options: RequestInit & { skipRedirectOn401?: boolean } = {},
    retries: number = this.maxRetries
  ): Promise<Response> {
    // Don't make requests if we're already redirecting to login
    if (isRedirecting) {
      throw new Error("Redirecting to login");
    }

    const { skipRedirectOn401, ...fetchOptions } = options;

    const baseUrl = this.getBaseUrl();
    // If endpoint already starts with /api, don't prepend base URL on client-side
    const url =
      endpoint.startsWith("/api") && typeof window !== "undefined"
        ? endpoint
        : `${baseUrl}${endpoint}`;

    try {
      const authHeaders = await this.getAuthHeaders();

      const response = await fetch(url, {
        ...fetchOptions,
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
          ...fetchOptions.headers,
        },
      });

      // Handle 401 by redirecting to login (but only once, unless skipRedirectOn401 is set)
      if (response.status === 401 && typeof window !== "undefined") {
        if (!skipRedirectOn401 && !isRedirecting) {
          isRedirecting = true;
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
        }
        // Throw without retry - auth errors should not be retried
        throw new Error("Unauthorized");
      }

      // Don't retry on client errors (4xx) - only server errors (5xx)
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
      // Only retry on network errors (TypeError), not on other errors
      if (retries > 0 && error instanceof TypeError) {
        await new Promise((resolve) => setTimeout(resolve, this.retryDelay));
        return this.fetchWithRetry(endpoint, options, retries - 1);
      }
      throw error;
    }
  }

  protected async get<T>(endpoint: string, options?: { skipRedirectOn401?: boolean }): Promise<T> {
    const response = await this.fetchWithRetry(endpoint, { method: "GET", ...options });
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

// Reset redirect flag (useful for testing or after successful login)
export function resetRedirectFlag(): void {
  isRedirecting = false;
}
