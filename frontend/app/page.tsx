import Link from "next/link";
import Script from "next/script";
import { Globe, Radio, TriangleAlert } from "lucide-react";

import type { NewsAlert } from "@/lib/types";

const REFRESH_INTERVAL_MS = 15_000;
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const PAGE_SIZE = 20;

function formatSourceLabel(source: string): string {
    if (!source.startsWith("http")) {
        return source;
    }

    try {
        const parsed = new URL(source);
        const host = parsed.hostname.replace(/^www\./, "");
        return host.split(".")[0]?.toUpperCase() ?? "Source";
    } catch {
        return "Source";
    }
}

function makeExcerpt(description: string | null): string | null {
    if (!description) {
        return null;
    }

    if (description.length <= 280) {
        return description;
    }

    return `${description.slice(0, 277)}...`;
}

async function getAlerts(): Promise<NewsAlert[]> {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

    try {
        const response = await fetch(`${apiBaseUrl}/api/alerts`, { cache: "no-store" });
        if (!response.ok) {
            return [];
        }

        const payload: unknown = await response.json();
        if (!Array.isArray(payload)) {
            return [];
        }

        return payload as NewsAlert[];
    } catch {
        return [];
    }
}

export default async function HomePage({
    searchParams,
}: {
    searchParams?: { limit?: string };
}) {
    const alerts = await getAlerts();
    const updatedText = new Date().toLocaleTimeString();
    const breakingCount = alerts.filter((item) => item.is_breaking).length;
    const sourcesCount = new Set(alerts.map((item) => formatSourceLabel(item.source))).size;
    const parsedLimit = Number.parseInt(searchParams?.limit ?? `${PAGE_SIZE}`, 10);
    const visibleCount = Number.isNaN(parsedLimit) ? PAGE_SIZE : Math.min(Math.max(parsedLimit, PAGE_SIZE), 100);
    const visibleAlerts = alerts.slice(0, visibleCount);
    const canLoadMore = visibleCount < alerts.length;
    const nextLimit = Math.min(visibleCount + PAGE_SIZE, 100);

    return (
        <main className="mx-auto min-h-screen max-w-6xl px-4 py-8 md:px-8">
            <header className="mb-6 rounded-xl border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-5 shadow-[0_0_40px_rgba(15,23,42,0.35)]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-semibold tracking-tight text-emerald-400">Crisis Feed</h1>
                        <p className="mt-1 text-sm text-slate-400">
                            Live conflict alert stream · auto-refresh every 15s · last update {updatedText}
                        </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                        <span className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-900/80 px-2.5 py-1 text-slate-300">
                            <Radio className="h-3.5 w-3.5 text-emerald-400" /> {alerts.length} alerts
                        </span>
                        <span className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-900/80 px-2.5 py-1 text-slate-300">
                            <Globe className="h-3.5 w-3.5 text-cyan-400" /> {sourcesCount} sources
                        </span>
                        <span className="inline-flex items-center gap-1 rounded-md border border-red-700/70 bg-red-950/40 px-2.5 py-1 text-red-200">
                            <TriangleAlert className="h-3.5 w-3.5" /> {breakingCount} breaking
                        </span>
                    </div>
                </div>
            </header>

            <Script id="feed-auto-refresh" strategy="afterInteractive">
                {`window.setTimeout(() => window.location.reload(), ${REFRESH_INTERVAL_MS});`}
            </Script>

            <section className="space-y-3">
                {alerts.length === 0 ? (
                    <p className="rounded-md border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">No matching alerts yet.</p>
                ) : (
                    visibleAlerts.map((alert) => (
                        <article
                            key={alert.id}
                            className={`rounded-lg border p-4 transition-colors hover:border-slate-600 ${alert.is_breaking ? "border-red-600/90 bg-red-950/20" : "border-slate-800 bg-slate-900/40"}`}
                        >
                            <div className="mb-2 flex items-center justify-between gap-2">
                                <span className="text-xs uppercase tracking-[0.16em] text-slate-400">{formatSourceLabel(alert.source)}</span>
                                <time className="text-xs text-slate-500">{new Date(alert.published_at).toLocaleString()}</time>
                            </div>
                            <h2 className="text-base font-semibold leading-snug text-slate-100">{alert.headline}</h2>
                            {makeExcerpt(alert.description) ? (
                                <p className="mt-2 text-sm leading-relaxed text-slate-300">{makeExcerpt(alert.description)}</p>
                            ) : null}
                            <div className="mt-3 flex items-center gap-3">
                                {alert.is_breaking ? (
                                    <span className="rounded border border-red-500/80 bg-red-950/40 px-2 py-0.5 text-xs font-semibold text-red-300">BREAKING</span>
                                ) : null}
                                <a
                                    className="text-xs text-emerald-400 underline-offset-2 hover:underline"
                                    href={alert.url}
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    Open source
                                </a>
                            </div>
                        </article>
                    ))
                )}
            </section>

            {alerts.length > 0 ? (
                <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
                    <p className="text-slate-400">Showing {Math.min(visibleCount, alerts.length)} of {alerts.length} alerts</p>
                    {canLoadMore ? (
                        <Link
                            href={`/?limit=${nextLimit}`}
                            className="rounded-md border border-slate-700 bg-slate-900/80 px-3 py-1.5 text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-800"
                        >
                            Load more
                        </Link>
                    ) : null}
                </div>
            ) : null}
        </main>
    );
}
