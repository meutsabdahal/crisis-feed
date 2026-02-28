"use client";

import { useEffect, useMemo, useState } from "react";
import { Globe, Radio, TriangleAlert } from "lucide-react";

import { fetchAlerts } from "@/lib/api";
import type { NewsAlert } from "@/lib/types";

const POLL_INTERVAL_MS = 15_000;

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

export default function HomePage() {
    const [alerts, setAlerts] = useState<NewsAlert[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    useEffect(() => {
        let isCancelled = false;

        const loadAlerts = async (): Promise<void> => {
            try {
                const latest = await fetchAlerts();
                if (!isCancelled) {
                    setAlerts(latest);
                    setError(null);
                    setLastUpdated(new Date());
                }
            } catch {
                if (!isCancelled) {
                    setError("Failed to fetch alerts.");
                }
            } finally {
                if (!isCancelled) {
                    setIsLoading(false);
                }
            }
        };

        void loadAlerts();
        const intervalId = window.setInterval(() => {
            void loadAlerts();
        }, POLL_INTERVAL_MS);

        return () => {
            isCancelled = true;
            window.clearInterval(intervalId);
        };
    }, []);

    const updatedText = useMemo(() => {
        if (!lastUpdated) {
            return "never";
        }
        return lastUpdated.toLocaleTimeString();
    }, [lastUpdated]);

    const breakingCount = useMemo(() => alerts.filter((item) => item.is_breaking).length, [alerts]);
    const sourcesCount = useMemo(() => new Set(alerts.map((item) => formatSourceLabel(item.source))).size, [alerts]);

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

            {error ? (
                <p className="mb-4 rounded-md border border-red-700 bg-red-950/40 px-3 py-2 text-sm text-red-200">{error}</p>
            ) : null}

            <section className="space-y-3">
                {isLoading ? (
                    <p className="rounded-md border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">Loading feed...</p>
                ) : alerts.length === 0 ? (
                    <p className="rounded-md border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">No matching alerts yet.</p>
                ) : (
                    alerts.map((alert) => (
                        <article
                            key={alert.id}
                            className={`rounded-lg border p-4 transition-colors hover:border-slate-600 ${alert.is_breaking ? "border-red-600/90 bg-red-950/20" : "border-slate-800 bg-slate-900/40"}`}
                        >
                            <div className="mb-2 flex items-center justify-between gap-2">
                                <span className="text-xs uppercase tracking-[0.16em] text-slate-400">{formatSourceLabel(alert.source)}</span>
                                <time className="text-xs text-slate-500">{new Date(alert.published_at).toLocaleString()}</time>
                            </div>
                            <h2 className="text-base font-semibold leading-snug text-slate-100">{alert.headline}</h2>
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
        </main>
    );
}
