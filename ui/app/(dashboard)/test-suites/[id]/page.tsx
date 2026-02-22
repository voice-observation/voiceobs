"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";

/**
 * Redirects /test-suites/[id] to /orgs/[orgId]/test-suites/[id].
 * Test suites are now org-scoped.
 */
export default function TestSuiteDetailRedirectPage() {
  const router = useRouter();
  const params = useParams();
  const suiteId = params.id as string;
  const { activeOrg, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (activeOrg?.id) {
      router.replace(`/orgs/${activeOrg.id}/test-suites/${suiteId}`);
    } else {
      router.replace("/");
    }
  }, [activeOrg?.id, suiteId, isLoading, router]);

  return null;
}
