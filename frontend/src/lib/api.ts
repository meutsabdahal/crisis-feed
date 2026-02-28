import type { NewsAlert } from "@/lib/types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

function resolveApiBaseUrl(): string {
    return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

export async function fetchAlerts(): Promise<NewsAlert[]> {
    const response = await fetch(`${resolveApiBaseUrl()}/api/alerts`, {
        method: "GET",
        cache: "no-store",
    });

    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
    }

    const payload: unknown = await response.json();
    if (!Array.isArray(payload)) {
        throw new Error("Invalid alerts response format.");
    }

    return payload as NewsAlert[];
}
