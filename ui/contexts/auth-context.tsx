"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
  ReactNode,
} from "react";
import { api, AuthMeResponse, UserResponse, OrgSummary, ActiveOrgResponse } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

interface AuthContextType {
  user: UserResponse | null;
  activeOrg: ActiveOrgResponse | null;
  orgs: OrgSummary[];
  isLoading: boolean;
  error: string | null;
  refreshAuth: () => Promise<void>;
  switchOrg: (orgId: string) => void;
  createOrg: (name: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ORG_STORAGE_KEY = "voiceobs_active_org_id";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [activeOrg, setActiveOrg] = useState<ActiveOrgResponse | null>(null);
  const [orgs, setOrgs] = useState<OrgSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refs to prevent concurrent fetches and track mount state
  const isFetchingRef = useRef(false);
  const hasFetchedRef = useRef(false);
  const isMountedRef = useRef(true);

  const fetchAuthMe = useCallback(async (force = false) => {
    // Prevent concurrent fetches
    if (isFetchingRef.current) {
      return;
    }

    // Don't refetch if we already have data (unless forced)
    if (hasFetchedRef.current && !force) {
      return;
    }

    isFetchingRef.current = true;

    try {
      setIsLoading(true);
      setError(null);

      // Check if we have a session first
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        // No session, clear state
        if (isMountedRef.current) {
          setUser(null);
          setActiveOrg(null);
          setOrgs([]);
          hasFetchedRef.current = true;
        }
        return;
      }

      // Fetch user data from backend (this triggers user upsert and org creation)
      const response = await api.auth.getMe();

      if (!isMountedRef.current) return;

      // If response is null, the backend rejected our token - clear session
      if (!response) {
        setUser(null);
        setActiveOrg(null);
        setOrgs([]);
        hasFetchedRef.current = true;
        return;
      }

      setUser(response.user);
      setOrgs(response.orgs);
      hasFetchedRef.current = true;

      // Determine active org: use localStorage override, or fall back to server's active_org
      const storedOrgId = localStorage.getItem(ORG_STORAGE_KEY);
      if (storedOrgId) {
        const storedOrg = response.orgs.find((o) => o.id === storedOrgId);
        if (storedOrg) {
          setActiveOrg({ id: storedOrg.id, name: storedOrg.name });
        } else {
          // Stored org no longer valid, fall back to server's active org
          localStorage.removeItem(ORG_STORAGE_KEY);
          setActiveOrg(response.active_org);
        }
      } else {
        setActiveOrg(response.active_org);
      }
    } catch (err) {
      // Don't log "Unauthorized" errors - those are handled by redirect
      if (err instanceof Error && err.message !== "Unauthorized") {
        console.error("Failed to fetch auth data:", err);
        if (isMountedRef.current) {
          setError(err.message);
        }
      }
      hasFetchedRef.current = true; // Mark as fetched even on error to prevent loops
    } finally {
      isFetchingRef.current = false;
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  const switchOrg = useCallback(
    (orgId: string) => {
      const org = orgs.find((o) => o.id === orgId);
      if (org) {
        setActiveOrg({ id: org.id, name: org.name });
        localStorage.setItem(ORG_STORAGE_KEY, orgId);
        // Persist to backend (fire and forget - don't block UI)
        api.auth.updateMe({ last_active_org_id: orgId }).catch((err) => {
          console.error("Failed to persist org switch:", err);
        });
      }
    },
    [orgs]
  );

  const createOrg = useCallback(async (name: string) => {
    const newOrg = await api.auth.createOrg(name);
    // Add the new org to the list
    setOrgs((prev) => [...prev, newOrg]);
    // Auto-switch to the new org
    setActiveOrg({ id: newOrg.id, name: newOrg.name });
    localStorage.setItem(ORG_STORAGE_KEY, newOrg.id);
    // Persist to backend (fire and forget - don't block UI)
    api.auth.updateMe({ last_active_org_id: newOrg.id }).catch((err) => {
      console.error("Failed to persist org switch:", err);
    });
  }, []);

  useEffect(() => {
    isMountedRef.current = true;

    // Initial fetch
    fetchAuthMe();

    // Listen for auth state changes
    const supabase = createClient();
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event) => {
      // Only handle explicit sign-in/sign-out events
      if (event === "SIGNED_IN") {
        // Reset fetch state and refetch
        hasFetchedRef.current = false;
        fetchAuthMe(true);
      } else if (event === "SIGNED_OUT") {
        setUser(null);
        setActiveOrg(null);
        setOrgs([]);
        setError(null);
        hasFetchedRef.current = false;
        localStorage.removeItem(ORG_STORAGE_KEY);
      }
      // Ignore other events like TOKEN_REFRESHED, INITIAL_SESSION, etc.
    });

    return () => {
      isMountedRef.current = false;
      subscription.unsubscribe();
    };
  }, [fetchAuthMe]);

  return (
    <AuthContext.Provider
      value={{
        user,
        activeOrg,
        orgs,
        isLoading,
        error,
        refreshAuth: () => fetchAuthMe(true),
        switchOrg,
        createOrg,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
