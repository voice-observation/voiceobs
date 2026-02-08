"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/primitives/button";
import { Input } from "@/components/primitives/input";
import { Label } from "@/components/primitives/label";
import { toast } from "sonner";
import { Mail, Loader2, ArrowLeft, CheckCircle2, Mic2 } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const supabase = createClient();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });

    if (error) {
      toast.error("Error", {
        description: error.message,
      });
      setLoading(false);
      return;
    }

    setSent(true);
    setLoading(false);
  };

  if (sent) {
    return (
      <div className="space-y-6">
        {/* Mobile logo - only visible on small screens */}
        <div className="mb-4 flex items-center justify-center gap-2 lg:hidden">
          <div className="rounded-lg bg-slate-100 p-2">
            <Mic2 className="h-6 w-6 text-slate-700" />
          </div>
          <span className="text-xl font-bold">voiceobs</span>
        </div>

        <div className="space-y-6 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-6 w-6 text-green-600" />
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-bold">Check your email</h1>
            <p className="text-muted-foreground">
              We&apos;ve sent a password reset link to{" "}
              <span className="font-medium text-foreground">{email}</span>
            </p>
          </div>
          <Link href="/login">
            <Button variant="outline" className="mt-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to login
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Mobile logo - only visible on small screens */}
      <div className="mb-4 flex items-center justify-center gap-2 lg:hidden">
        <div className="rounded-lg bg-slate-100 p-2">
          <Mic2 className="h-6 w-6 text-slate-700" />
        </div>
        <span className="text-xl font-bold">voiceobs</span>
      </div>

      <div className="space-y-2 text-center">
        <h1 className="text-2xl font-bold">Forgot password?</h1>
        <p className="text-muted-foreground">
          Enter your email and we&apos;ll send you a reset link
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              className="pl-10"
            />
          </div>
        </div>

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Sending...
            </>
          ) : (
            "Send reset link"
          )}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        <Link href="/login" className="inline-flex items-center font-medium hover:underline">
          <ArrowLeft className="mr-1 h-3 w-3" />
          Back to login
        </Link>
      </p>
    </div>
  );
}
