import type { NewsAlert } from "@/lib/types";

const DEFAULT_API_PORT = "8000";
const REQUEST_TIMEOUT_MS = 10_000;

function resolveApiBaseUrl(): string {
    if (process.env.NEXT_PUBLIC_API_BASE_URL) {
        return process.env.NEXT_PUBLIC_API_BASE_URL;
    }

    if (typeof window !== "undefined") {
        return `${window.location.protocol}//${window.location.hostname}:${DEFAULT_API_PORT}`;
    }

    return `http://127.0.0.1:${DEFAULT_API_PORT}`;
}

export async function fetchAlerts(): Promise<NewsAlert[]> {
    const controller = new AbortController();
    const timeoutId = globalThis.setTimeout(() => {
        controller.abort();
    }, REQUEST_TIMEOUT_MS);

    let response: Response;
    try {
        response = await fetch(`${resolveApiBaseUrl()}/api/alerts`, {
            method: "GET",
            cache: "no-store",
            signal: controller.signal,
        });
    } finally {
        globalThis.clearTimeout(timeoutId);
    }

    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
    }

    const payload: unknown = await response.json();
    if (!Array.isArray(payload)) {
        throw new Error("Invalid alerts response format.");
    }

    return payload as NewsAlert[];
}
