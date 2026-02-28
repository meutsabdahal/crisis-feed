"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchAlerts } from "@/lib/api";
import type { NewsAlert } from "@/lib/types";

const POLL_INTERVAL_MS = 15_000;

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

    return (
        <main className="mx-auto min-h-screen max-w-5xl px-4 py-8 md:px-8">
            <header className="mb-6 border border-slate-800 bg-slate-900/50 p-4">
                <h1 className="text-2xl font-semibold text-emerald-400">Crisis Feed</h1>
                <p className="mt-1 text-sm text-slate-400">
                    Live conflict alert stream · auto-refresh every 15s · last update {updatedText}
                </p>
            </header>

            {error ? <p className="mb-4 border border-red-700 bg-red-950/40 px-3 py-2 text-sm text-red-200">{error}</p> : null}

            <section className="space-y-3">
                {isLoading ? (
                    <p className="text-sm text-slate-400">Loading feed...</p>
                ) : alerts.length === 0 ? (
                    <p className="text-sm text-slate-400">No matching alerts yet.</p>
                ) : (
                    alerts.map((alert) => (
                        <article
                            key={alert.id}
                            className={`border p-4 ${alert.is_breaking ? "border-red-600 bg-red-950/20" : "border-slate-800 bg-slate-900/40"}`}
                        >
                            <div className="mb-2 flex items-center justify-between gap-2">
                                <span className="text-xs uppercase tracking-wide text-slate-400">{alert.source}</span>
                                <time className="text-xs text-slate-500">{new Date(alert.published_at).toLocaleString()}</time>
                            </div>
                            <h2 className="text-base font-medium text-slate-100">{alert.headline}</h2>
                            <div className="mt-3 flex items-center gap-3">
                                {alert.is_breaking ? (
                                    <span className="border border-red-500 px-2 py-0.5 text-xs font-semibold text-red-300">BREAKING</span>
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
