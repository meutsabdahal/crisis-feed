import Link from "next/link";
import Script from "next/script";
import { Clock, ExternalLink, Globe, Radio, Siren, TriangleAlert } from "lucide-react";

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

function timeAgo(dateString: string): string {
    const now = Date.now();
    const then = new Date(dateString).getTime();
    const diffMs = now - then;

    if (diffMs < 0) return "just now";

    const minutes = Math.floor(diffMs / 60_000);
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;

    const days = Math.floor(hours / 24);
    return `${days}d ago`;
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
    const breakingCount = alerts.filter((item) => item.is_breaking).length;
    const sourcesCount = new Set(alerts.map((item) => formatSourceLabel(item.source))).size;
    const parsedLimit = Number.parseInt(searchParams?.limit ?? `${PAGE_SIZE}`, 10);
    const visibleCount = Number.isNaN(parsedLimit) ? PAGE_SIZE : Math.min(Math.max(parsedLimit, PAGE_SIZE), 100);
    const visibleAlerts = alerts.slice(0, visibleCount);
    const canLoadMore = visibleCount < alerts.length;
    const nextLimit = Math.min(visibleCount + PAGE_SIZE, 100);

    return (
        <main className="mx-auto min-h-screen max-w-4xl px-4 py-6 sm:py-10 md:px-6">
            {/* ---------- Header ---------- */}
            <header className="mb-8">
                <div className="flex items-center gap-2.5">
                    <Siren className="h-6 w-6 text-emerald-400" aria-hidden />
                    <h1 className="text-xl font-bold tracking-tight text-slate-50 sm:text-2xl">
                        Crisis Feed
                    </h1>
                    <span className="ml-1 inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wider text-emerald-400">
                        <span className="animate-pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
                        Live
                    </span>
                </div>
                <p className="mt-1.5 text-sm text-slate-500">
                    Real-time conflict alert stream from {sourcesCount} sources
                </p>

                {/* Stats row */}
                <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-800/50 px-3 py-1 text-slate-400">
                        <Radio className="h-3 w-3 text-emerald-400" aria-hidden />
                        {alerts.length} alerts
                    </span>
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-800/50 px-3 py-1 text-slate-400">
                        <Globe className="h-3 w-3 text-sky-400" aria-hidden />
                        {sourcesCount} sources
                    </span>
                    {breakingCount > 0 ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 font-medium text-red-400">
                            <TriangleAlert className="h-3 w-3" aria-hidden />
                            {breakingCount} breaking
                        </span>
                    ) : null}
                </div>
            </header>

            {/* Auto-refresh */}
            <Script id="feed-auto-refresh" strategy="afterInteractive">
                {`window.setTimeout(() => window.location.reload(), ${REFRESH_INTERVAL_MS});`}
            </Script>

            {/* ---------- Feed ---------- */}
            <section>
                {alerts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700/60 py-20 text-center">
                        <Radio className="mb-3 h-8 w-8 text-slate-600" aria-hidden />
                        <p className="text-sm font-medium text-slate-400">No matching alerts yet</p>
                        <p className="mt-1 text-xs text-slate-600">Feeds are polled every 3 minutes. Check back shortly.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-800/70">
                        {visibleAlerts.map((alert) => {
                            const excerpt = makeExcerpt(alert.description);
                            return (
                                <article
                                    key={alert.id}
                                    className={`group relative py-5 first:pt-0 ${alert.is_breaking ? "pl-4 before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:rounded-full before:bg-red-500" : ""}`}
                                >
                                    {/* Meta row */}
                                    <div className="mb-1.5 flex items-center gap-2 text-xs">
                                        <span className="font-medium uppercase tracking-wide text-slate-500">
                                            {formatSourceLabel(alert.source)}
                                        </span>
                                        <span className="text-slate-700" aria-hidden>&middot;</span>
                                        <span className="inline-flex items-center gap-1 text-slate-600">
                                            <Clock className="h-3 w-3" aria-hidden />
                                            {timeAgo(alert.published_at)}
                                        </span>
                                        {alert.is_breaking ? (
                                            <>
                                                <span className="text-slate-700" aria-hidden>&middot;</span>
                                                <span className="rounded bg-red-500/15 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-400">
                                                    Breaking
                                                </span>
                                            </>
                                        ) : null}
                                    </div>

                                    {/* Headline */}
                                    <h2 className="text-[15px] font-semibold leading-snug text-slate-100 group-hover:text-white">
                                        {alert.headline}
                                    </h2>

                                    {/* Description */}
                                    {excerpt ? (
                                        <p className="mt-1.5 text-sm leading-relaxed text-slate-400">
                                            {excerpt}
                                        </p>
                                    ) : null}

                                    {/* Link */}
                                    <a
                                        className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-emerald-500 transition-colors hover:text-emerald-400"
                                        href={alert.url}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        Read full article
                                        <ExternalLink className="h-3 w-3" aria-hidden />
                                    </a>
                                </article>
                            );
                        })}
                    </div>
                )}
            </section>

            {/* ---------- Footer / Pagination ---------- */}
            {alerts.length > 0 ? (
                <footer className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800/70 pt-5 text-xs text-slate-500">
                    <p>
                        Showing {Math.min(visibleCount, alerts.length)} of {alerts.length} alerts
                    </p>
                    {canLoadMore ? (
                        <Link
                            href={`/?limit=${nextLimit}`}
                            className="rounded-full border border-slate-700 bg-slate-800/60 px-4 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-white"
                        >
                            Load more
                        </Link>
                    ) : null}
                </footer>
            ) : null}
        </main>
    );
}
