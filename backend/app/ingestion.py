import asyncio
import re
from html import unescape
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal, init_db
from app.models import NewsAlert

RSS_FEEDS: tuple[str, ...] = (
    "https://feeds.reuters.com/reuters/worldNews",
    "http://rss.cnn.com/rss/edition_world.rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.npr.org/1004/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://rss.dw.com/rdf/rss-en-world",
)

DOMAIN_SOURCE_MAP: dict[str, str] = {
    "reuters.com": "Reuters",
    "cnn.com": "CNN",
    "aljazeera.com": "Al Jazeera",
    "bbc.co.uk": "BBC",
    "bbc.com": "BBC",
    "npr.org": "NPR",
    "theguardian.com": "The Guardian",
    "dw.com": "DW",
}

ACTOR_KEYWORDS: tuple[str, ...] = (
    "u.s.",
    "united states",
    "us military",
    "iran",
    "israel",
    "idf",
    "tehran",
    "khamenei",
)

CONFLICT_KEYWORDS: tuple[str, ...] = (
    "strike",
    "airstrike",
    "missile",
    "drone",
    "attack",
    "retaliation",
    "escalation",
    "military",
    "operation epic fury",
    "epic fury",
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
    has_actor = any(keyword in lowered for keyword in ACTOR_KEYWORDS)
    has_conflict_signal = any(keyword in lowered for keyword in CONFLICT_KEYWORDS)
    return has_actor and has_conflict_signal


def _is_breaking(headline: str) -> bool:
    lowered = headline.lower()
    return any(hint in lowered for hint in BREAKING_HINTS)


def _clean_description(raw_text: str) -> str:
    text = unescape(raw_text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


async def _get_alert_by_url(session: AsyncSession, url: str) -> NewsAlert | None:
    query = select(NewsAlert).where(NewsAlert.url == url)
    result = await session.execute(query)
    return result.scalar_one_or_none()


def _extract_description(entry: dict[str, Any]) -> str:
    summary_raw = str(entry.get("summary") or entry.get("description") or "").strip()
    summary = _clean_description(summary_raw)
    if summary:
        return summary

    content = entry.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                value = str(item.get("value") or "").strip()
                cleaned = _clean_description(value)
                if cleaned:
                    return cleaned

    return ""


def _clean_domain(raw_url: str) -> str:
    hostname = urlparse(raw_url).hostname or ""
    lowered = hostname.lower()

    for prefix in ("www.", "m.", "feeds.", "rss."):
        if lowered.startswith(prefix):
            lowered = lowered[len(prefix) :]

    return lowered


def _resolve_source_name(
    entry: dict[str, Any],
    article_url: str,
    feed_url: str,
    feed_title: str,
) -> str:
    source_detail = entry.get("source")
    if isinstance(source_detail, dict):
        source_title = str(source_detail.get("title") or "").strip()
        if source_title and "http" not in source_title.lower():
            return source_title

    for candidate in (article_url, feed_url):
        domain = _clean_domain(candidate)
        if not domain:
            continue

        for known_domain, known_name in DOMAIN_SOURCE_MAP.items():
            if domain.endswith(known_domain):
                return known_name

        return domain.replace(".", " ").title()

    if feed_title:
        return feed_title

    return "Newswire"


async def fetch_and_store_alerts() -> int:
    inserted_count = 0
    await init_db()

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
                feed_title = str(getattr(parsed_feed.feed, "title", "") or "").strip()

                for raw_entry in entries:
                    entry = dict(raw_entry)
                    headline = str(entry.get("title") or "").strip()
                    url = str(entry.get("link") or "").strip()
                    summary = _extract_description(entry)

                    if not headline or not url:
                        continue

                    if not _text_matches_keywords(f"{headline} {summary} {url}"):
                        continue

                    existing_alert = await _get_alert_by_url(session, url)
                    if existing_alert is not None:
                        if not existing_alert.description and summary:
                            existing_alert.description = summary[:4000]
                        continue

                    source = _resolve_source_name(
                        entry=entry,
                        article_url=url,
                        feed_url=feed_url,
                        feed_title=feed_title,
                    )

                    session.add(
                        NewsAlert(
                            headline=headline,
                            description=summary[:4000] if summary else None,
                            source=source[:255],
                            url=url[:1024],
                            published_at=_parse_published_at(entry),
                            is_breaking=_is_breaking(f"{headline} {summary}"),
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
