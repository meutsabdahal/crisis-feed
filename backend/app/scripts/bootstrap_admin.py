from __future__ import annotations

import argparse
import asyncio
import getpass
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.database import build_engine, build_session_factory
from app.models.models import User


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"), help="Admin email")
    parser.add_argument(
        "--password", default=os.getenv("ADMIN_PASSWORD"), help="Admin password"
    )
    parser.add_argument(
        "--full-name", default=os.getenv("ADMIN_FULL_NAME"), help="Admin full name"
    )
    parser.add_argument(
        "--prompt-password",
        action="store_true",
        help="Prompt for password interactively instead of passing as argument",
    )
    return parser


async def upsert_admin_user(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str | None,
) -> tuple[User, bool]:
    existing_user = await session.scalar(select(User).where(User.email == email))
    hashed_password = hash_password(password)

    if existing_user is None:
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role="admin",
            is_active=True,
        )
        session.add(admin_user)
        created = True
    else:
        existing_user.hashed_password = hashed_password
        existing_user.full_name = full_name
        existing_user.role = "admin"
        existing_user.is_active = True
        admin_user = existing_user
        created = False

    await session.commit()
    await session.refresh(admin_user)
    return admin_user, created


async def _run() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if not isinstance(args.email, str) or not args.email.strip():
        raise SystemExit("Missing admin email. Provide --email or ADMIN_EMAIL.")

    password = args.password
    if args.prompt_password:
        password = getpass.getpass("Admin password: ")

    if not isinstance(password, str) or not password.strip():
        raise SystemExit(
            "Missing admin password. Provide --password, --prompt-password, or ADMIN_PASSWORD."
        )

    engine = build_engine()
    session_factory = build_session_factory(engine)

    try:
        async with session_factory() as session:
            user, created = await upsert_admin_user(
                session=session,
                email=args.email.strip().lower(),
                password=password,
                full_name=args.full_name,
            )

        action = "Created" if created else "Updated"
        print(f"{action} admin user: {user.email} (id={user.id})")
        return 0
    finally:
        await engine.dispose()


def main() -> None:
    exit_code = asyncio.run(_run())
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
