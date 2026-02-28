export type NewsAlert = {
    id: number;
    headline: string;
    description: string | null;
    source: string;
    url: string;
    published_at: string;
    is_breaking: boolean;
};
