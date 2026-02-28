import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight text-slate-50">GeoRisk Monitor</h1>
      <p className="mt-4 max-w-2xl text-slate-300">
        Real-time geopolitical crisis monitoring for enterprise operations and supply chain resilience.
      </p>
      <div className="mt-8 flex items-center gap-3">
        <Link
          href="/login"
          className="inline-flex h-10 items-center justify-center rounded-md bg-slate-100 px-4 text-sm font-medium text-slate-900 hover:bg-slate-200"
        >
          Sign in
        </Link>
        <Link
          href="/dashboard"
          className="inline-flex h-10 items-center justify-center rounded-md bg-slate-800 px-4 text-sm font-medium text-slate-100 hover:bg-slate-700"
        >
          View dashboard
        </Link>
      </div>
    </main>
  );
}
