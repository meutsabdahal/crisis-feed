import asyncio
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.models import NewsAlert

RSS_FEEDS: tuple[str, ...] = (
    "https://feeds.reuters.com/reuters/worldNews",
    "http://rss.cnn.com/rss/edition_world.rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
)

KEYWORDS: tuple[str, ...] = (
    "us",
    "iran",
    "israel",
    "strike",
    "epic fury",
    "khamenei",
)

BREAKING_HINTS: tuple[str, ...] = (
    "breaking",
    "urgent",
    "strike",
    "escalation",
)

POLL_INTERVAL_SECONDS = 180


def _text_matches_keywords(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in KEYWORDS)


def _is_breaking(headline: str) -> bool:
    lowered = headline.lower()
    return any(hint in lowered for hint in BREAKING_HINTS)


def _parse_published_at(entry: dict[str, Any]) -> datetime:
    raw_value = entry.get("published") or entry.get("updated")
    if isinstance(raw_value, str):
        try:
            parsed = parsedate_to_datetime(raw_value)
            return parsed.astimezone(UTC).replace(tzinfo=None)
        except (TypeError, ValueError):
            pass

    return datetime.now(UTC).replace(tzinfo=None)


async def _alert_exists(session: AsyncSession, url: str) -> bool:
    query = select(NewsAlert.id).where(NewsAlert.url == url)
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def fetch_and_store_alerts() -> int:
    inserted_count = 0

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        async with SessionLocal() as session:
            for feed_url in RSS_FEEDS:
                try:
                    response = await client.get(feed_url)
                    response.raise_for_status()
                except httpx.HTTPError:
                    continue

                parsed_feed = feedparser.parse(response.text)
                entries = (
                    parsed_feed.entries if isinstance(parsed_feed.entries, list) else []
                )

                for raw_entry in entries:
                    entry = dict(raw_entry)
                    headline = str(entry.get("title") or "").strip()
                    url = str(entry.get("link") or "").strip()

                    if not headline or not url:
                        continue

                    if not _text_matches_keywords(f"{headline} {url}"):
                        continue

                    if await _alert_exists(session, url):
                        continue

                    source_detail = entry.get("source")
                    if isinstance(source_detail, dict):
                        source = str(source_detail.get("title") or feed_url)
                    else:
                        source = feed_url

                    session.add(
                        NewsAlert(
                            headline=headline,
                            source=source[:255],
                            url=url[:1024],
                            published_at=_parse_published_at(entry),
                            is_breaking=_is_breaking(headline),
                        )
                    )
                    inserted_count += 1

            await session.commit()

    return inserted_count


async def ingestion_loop() -> None:
    while True:
        try:
            await fetch_and_store_alerts()
        except Exception:
            pass
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
