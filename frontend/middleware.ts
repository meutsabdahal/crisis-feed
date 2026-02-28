import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED_PATHS = ["/dashboard"];
const AUTH_PATHS = ["/login"];
const AUTH_COOKIE_NAME = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME ?? "grm_access_token";

export function middleware(request: NextRequest): NextResponse {
    const { pathname } = request.nextUrl;
    const accessToken = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    const isProtectedPath = PROTECTED_PATHS.some((path) => pathname.startsWith(path));
    const isAuthPath = AUTH_PATHS.some((path) => pathname.startsWith(path));

    if (isProtectedPath && !accessToken) {
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("next", pathname);
        return NextResponse.redirect(loginUrl);
    }

    if (isAuthPath && accessToken) {
        return NextResponse.redirect(new URL("/dashboard", request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: ["/dashboard/:path*", "/login"],
};
