import { Mic2 } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Left side - Branding */}
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 lg:flex lg:w-1/2">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-700/20 via-transparent to-transparent" />
        <div className="relative z-10 flex flex-col justify-center px-12 text-white">
          <div className="mb-8 flex items-center gap-3">
            <div className="rounded-xl bg-white/10 p-3 backdrop-blur-sm">
              <Mic2 className="h-8 w-8" />
            </div>
            <span className="text-3xl font-bold">voiceobs</span>
          </div>
          <h1 className="mb-4 text-4xl font-bold">Voice AI Observability</h1>
          <p className="max-w-md text-lg text-slate-300">
            Monitor, analyze, and optimize your voice AI conversations with powerful insights and
            real-time metrics.
          </p>
          <div className="mt-12 space-y-4">
            <div className="flex items-center gap-3 text-slate-300">
              <div className="h-2 w-2 rounded-full bg-slate-500" />
              <span>Real-time conversation monitoring</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300">
              <div className="h-2 w-2 rounded-full bg-slate-500" />
              <span>Automated quality testing</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300">
              <div className="h-2 w-2 rounded-full bg-slate-500" />
              <span>Performance analytics & insights</span>
            </div>
          </div>
        </div>
        {/* Decorative elements */}
        <div className="absolute -bottom-32 -left-32 h-64 w-64 rounded-full bg-slate-700/30 blur-3xl" />
        <div className="absolute -right-32 -top-32 h-64 w-64 rounded-full bg-slate-700/30 blur-3xl" />
      </div>

      {/* Right side - Auth form */}
      <div className="flex w-full items-center justify-center bg-background p-8 lg:w-1/2">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
