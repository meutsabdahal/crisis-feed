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

from app.database import SessionLocal
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

_RE_HTML_TAG = re.compile(r"<[^>]+>")
_RE_WHITESPACE = re.compile(r"\s+")


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
    text = _RE_HTML_TAG.sub(" ", text)
    text = _RE_WHITESPACE.sub(" ", text).strip()
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


async def _fetch_feed(
    client: httpx.AsyncClient, feed_url: str
) -> feedparser.FeedParserDict | None:
    """Fetch a single RSS feed, returning the parsed result or None on error."""
    try:
        response = await client.get(feed_url)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    result: feedparser.FeedParserDict = feedparser.parse(response.text)
    return result


async def fetch_and_store_alerts() -> int:
    inserted_count = 0

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        # Fetch all feeds concurrently
        results = await asyncio.gather(
            *(_fetch_feed(client, url) for url in RSS_FEEDS),
            return_exceptions=True,
        )

    async with SessionLocal() as session:
        for feed_url, result in zip(RSS_FEEDS, results, strict=True):
            if isinstance(result, BaseException) or result is None:
                continue

            parsed_feed = result
            entries: list[Any] = (
                parsed_feed.entries if isinstance(parsed_feed.entries, list) else []
            )
            if not entries:
                continue

            feed_title = str(getattr(parsed_feed.feed, "title", "") or "").strip()

            # Pre-filter entries and collect candidate URLs
            candidates: list[tuple[dict[str, Any], str, str, str]] = []
            for raw_entry in entries:
                entry = dict(raw_entry)
                headline = str(entry.get("title") or "").strip()
                url = str(entry.get("link") or "").strip()
                summary = _extract_description(entry)

                if not headline or not url:
                    continue
                if not _text_matches_keywords(f"{headline} {summary} {url}"):
                    continue

                candidates.append((entry, headline, url, summary))

            if not candidates:
                continue

            # Batch-check which URLs already exist
            candidate_urls = [c[2] for c in candidates]
            existing_query = select(NewsAlert.url, NewsAlert.description).where(
                NewsAlert.url.in_(candidate_urls)
            )
            existing_rows = await session.execute(existing_query)
            existing_map: dict[str, str | None] = {
                str(row[0]): row[1] for row in existing_rows.fetchall()
            }

            for entry, headline, url, summary in candidates:
                if url in existing_map:
                    # Backfill description if missing
                    if not existing_map[url] and summary:
                        stmt = select(NewsAlert).where(NewsAlert.url == url)
                        row = await session.execute(stmt)
                        alert = row.scalar_one_or_none()
                        if alert is not None:
                            alert.description = summary[:4000]
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
