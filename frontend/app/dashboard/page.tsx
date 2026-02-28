"use client";

import axios from "axios";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Alert, AlertCreatedEvent, User } from "@/lib/types";

export default function DashboardPage() {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        setIsLoading(true);
        setErrorMessage(null);

        try {
            const [currentUser, latestAlerts] = await Promise.all([api.me(), api.listAlerts(50)]);
            setUser(currentUser.user);
            setAlerts(latestAlerts);
        } catch (error: unknown) {
            if (axios.isAxiosError(error) && error.response?.status === 401) {
                router.push("/login");
                return;
            }
            setErrorMessage("Failed to load dashboard data.");
        } finally {
            setIsLoading(false);
        }
    }, [router]);

    useEffect(() => {
        void loadData();
    }, [loadData]);

    useEffect(() => {
        const socket = new WebSocket(api.buildAlertsStreamUrl());

        socket.onmessage = (event: MessageEvent<string>) => {
            const parsed = api.parseAlertEvent(event.data);
            if (!parsed) {
                return;
            }

            const alertEvent: AlertCreatedEvent = parsed;
            setAlerts((currentAlerts) => {
                const existingIndex = currentAlerts.findIndex((item) => item.id === alertEvent.payload.id);
                if (existingIndex >= 0) {
                    const updated = [...currentAlerts];
                    updated[existingIndex] = alertEvent.payload;
                    return updated;
                }
                return [alertEvent.payload, ...currentAlerts].slice(0, 50);
            });
        };

        socket.onerror = () => {
            // Keep UI non-blocking if stream is unavailable; polling refresh still works.
        };

        return () => {
            socket.close();
        };
    }, []);

    const handleLogout = async () => {
        try {
            await api.logout();
        } finally {
            router.push("/login");
            router.refresh();
        }
    };

    return (
        <main className="mx-auto min-h-screen max-w-6xl px-6 py-10">
            <header className="mb-8 flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-semibold text-slate-50">Operational Dashboard</h1>
                    <p className="mt-1 text-sm text-slate-400">
                        {user ? `Signed in as ${user.email}` : "Authenticating session..."}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="secondary" onClick={() => void loadData()} disabled={isLoading}>
                        Refresh
                    </Button>
                    <Button variant="destructive" onClick={() => void handleLogout()}>
                        Sign out
                    </Button>
                </div>
            </header>

            {errorMessage ? (
                <p className="mb-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {errorMessage}
                </p>
            ) : null}

            <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                <h2 className="mb-4 text-lg font-medium text-slate-100">Latest Alerts</h2>

                {isLoading ? (
                    <p className="text-sm text-slate-400">Loading alerts...</p>
                ) : alerts.length === 0 ? (
                    <p className="text-sm text-slate-400">No alerts are available yet.</p>
                ) : (
                    <ul className="space-y-3">
                        {alerts.map((alert) => (
                            <li key={alert.id} className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                    <p className="text-sm font-medium text-slate-100">
                                        {alert.region} · {alert.severity_level}
                                    </p>
                                    <p className="text-xs text-slate-400">{new Date(alert.timestamp).toLocaleString()}</p>
                                </div>
                                <p className="mt-2 text-sm text-slate-300">{alert.description}</p>
                                <p className="mt-2 text-xs text-slate-500">Source: {alert.source}</p>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </main>
    );
}
