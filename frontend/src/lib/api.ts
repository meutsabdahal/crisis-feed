import axios, {
    AxiosRequestConfig,
    AxiosError,
    AxiosInstance,
    AxiosResponse,
    InternalAxiosRequestConfig,
} from "axios";

import {
    Alert,
    AlertCreatedEvent,
    AuthResponse,
    CreateAlertPayload,
    LoginPayload,
    MessageResponse,
    RegisterPayload,
} from "@/lib/types";

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
    _retry?: boolean;
    url?: string;
    skipAuthRedirect?: boolean;
}

interface ApiRequestConfig extends AxiosRequestConfig {
    skipAuthRedirect?: boolean;
}

const DEFAULT_LOCAL_API_PORT = "8000";

function resolveApiBaseUrl(): string {
    if (process.env.NEXT_PUBLIC_API_BASE_URL) {
        return process.env.NEXT_PUBLIC_API_BASE_URL;
    }

    if (typeof window !== "undefined") {
        return `${window.location.protocol}//${window.location.hostname}:${DEFAULT_LOCAL_API_PORT}`;
    }

    return `http://127.0.0.1:${DEFAULT_LOCAL_API_PORT}`;
}

class ApiService {
    private readonly client: AxiosInstance;
    private refreshPromise: Promise<void> | null = null;

    constructor() {
        const apiBaseUrl = resolveApiBaseUrl();

        this.client = axios.create({
            baseURL: `${apiBaseUrl}/api/v1`,
            withCredentials: true,
            timeout: 15_000,
            headers: {
                "Content-Type": "application/json",
            },
        });

        this.client.interceptors.response.use(
            (response: AxiosResponse) => response,
            async (error: AxiosError) => {
                const originalRequest = error.config as RetriableRequestConfig | undefined;

                if (
                    error.response?.status === 401 &&
                    originalRequest &&
                    !originalRequest._retry &&
                    !originalRequest.url?.includes("/auth/refresh")
                ) {
                    originalRequest._retry = true;

                    try {
                        await this.refreshSession();
                        return this.client(originalRequest);
                    } catch (refreshError) {
                        if (!originalRequest.skipAuthRedirect && typeof window !== "undefined") {
                            window.location.assign("/login");
                        }
                        return Promise.reject(refreshError);
                    }
                }

                return Promise.reject(error);
            },
        );
    }

    private async refreshSession(): Promise<void> {
        if (!this.refreshPromise) {
            // Coalescing refresh attempts prevents a thundering herd when many requests expire at once.
            this.refreshPromise = this.client
                .post<MessageResponse>("/auth/refresh")
                .then(() => undefined)
                .finally(() => {
                    this.refreshPromise = null;
                });
        }

        if (!this.refreshPromise) {
            throw new Error("Session refresh could not be initialized.");
        }

        return this.refreshPromise;
    }

    async register(payload: RegisterPayload): Promise<AuthResponse> {
        const { data } = await this.client.post<AuthResponse>("/auth/register", payload);
        return data;
    }

    async login(payload: LoginPayload): Promise<AuthResponse> {
        const { data } = await this.client.post<AuthResponse>("/auth/login", payload);
        return data;
    }

    async me(config?: ApiRequestConfig): Promise<AuthResponse> {
        const { data } = await this.client.get<AuthResponse>("/auth/me", config);
        return data;
    }

    async logout(): Promise<MessageResponse> {
        const { data } = await this.client.post<MessageResponse>("/auth/logout");
        return data;
    }

    async listAlerts(limit = 100, config?: ApiRequestConfig): Promise<Alert[]> {
        const { data } = await this.client.get<Alert[]>("/alerts", { params: { limit }, ...config });
        return data;
    }

    async createAlert(payload: CreateAlertPayload): Promise<Alert> {
        const { data } = await this.client.post<Alert>("/alerts", payload);
        return data;
    }

    buildAlertsStreamUrl(): string {
        const apiBaseUrl = resolveApiBaseUrl();
        const streamBaseUrl = apiBaseUrl.startsWith("https://")
            ? apiBaseUrl.replace("https://", "wss://")
            : apiBaseUrl.replace("http://", "ws://");
        return `${streamBaseUrl}/api/v1/alerts/stream`;
    }

    parseAlertEvent(message: string): AlertCreatedEvent | null {
        try {
            const parsed = JSON.parse(message) as unknown;
            if (
                typeof parsed === "object" &&
                parsed !== null &&
                "event" in parsed &&
                (parsed as { event?: string }).event === "alert.created"
            ) {
                return parsed as AlertCreatedEvent;
            }
            return null;
        } catch {
            return null;
        }
    }
}

export const api = new ApiService();
