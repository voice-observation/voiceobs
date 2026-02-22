"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";

/**
 * Redirects /test-suites to /orgs/[orgId]/test-suites.
 * Test suites are now org-scoped.
 */
export default function TestSuitesRedirectPage() {
  const router = useRouter();
  const { activeOrg, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (activeOrg?.id) {
      router.replace(`/orgs/${activeOrg.id}/test-suites`);
    } else {
      router.replace("/");
    }
  }, [activeOrg?.id, isLoading, router]);

  return null;
}
