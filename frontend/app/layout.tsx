import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
    title: "Crisis Feed",
    description: "Real-time conflict news alert stream",
};

export const viewport: Viewport = {
    themeColor: "#020617",
    width: "device-width",
    initialScale: 1,
};

type RootLayoutProps = Readonly<{
    children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
    return (
        <html lang="en" className={inter.className}>
            <body>{children}</body>
        </html>
    );
}
