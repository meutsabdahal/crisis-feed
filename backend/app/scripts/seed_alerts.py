from __future__ import annotations

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import build_engine, build_session_factory
from app.models.models import Alert

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
REGIONS = [
    "Eastern Europe",
    "South China Sea",
    "Middle East",
    "Horn of Africa",
    "Black Sea",
    "South Atlantic",
]
SOURCES = ["internal-intel", "partner-feed", "open-source-monitor", "satellite-feed"]
DESCRIPTIONS = [
    "Military posture escalation near strategic corridor.",
    "Port throughput delay due to regional security event.",
    "Airspace restriction impacting cargo rerouting.",
    "Critical logistics node experiencing disruption.",
    "State-level sanctions increasing procurement risk.",
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed synthetic alerts for local development")
    parser.add_argument("--count", type=int, default=25, help="Number of alerts to insert")
    return parser


async def _seed_alerts(session: AsyncSession, count: int) -> None:
    now = datetime.now(UTC)
    alerts: list[Alert] = []

    for idx in range(count):
        alert = Alert(
            severity_level=random.choice(SEVERITY_LEVELS),
            region=random.choice(REGIONS),
            description=random.choice(DESCRIPTIONS),
            source=random.choice(SOURCES),
            timestamp=now - timedelta(minutes=idx * random.randint(3, 20)),
        )
        alerts.append(alert)

    session.add_all(alerts)
    await session.commit()


async def _run() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.count <= 0:
        raise SystemExit("--count must be greater than zero")

    engine = build_engine()
    session_factory = build_session_factory(engine)

    try:
        async with session_factory() as session:
            await _seed_alerts(session, args.count)
        print(f"Inserted {args.count} synthetic alerts.")
        return 0
    finally:
        await engine.dispose()


def main() -> None:
    exit_code = asyncio.run(_run())
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
