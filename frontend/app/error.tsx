"use client";

import { useEffect } from "react";

type ErrorPageProps = {
    error: Error & { digest?: string };
    reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
    useEffect(() => {
        console.error(error);
    }, [error]);

    return (
        <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
            <h1 className="text-2xl font-semibold text-slate-50">Something went wrong</h1>
            <p className="mt-3 text-sm text-slate-300">
                The page hit an unexpected error. Try loading it again.
            </p>
            <button
                type="button"
                onClick={reset}
                className="mt-6 inline-flex h-10 items-center justify-center rounded-md bg-slate-100 px-4 text-sm font-medium text-slate-900 hover:bg-slate-200"
            >
                Retry
            </button>
        </main>
    );
}