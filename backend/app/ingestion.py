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
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.npr.org/1004/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://rss.dw.com/rdf/rss-en-world",
    "https://moxie.foxnews.com/google-publisher/world.xml",  # Fox News world
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",  # NYT world
    "https://feeds.washingtonpost.com/rss/world",  # Washington Post world
    "https://www.france24.com/en/rss",  # France 24
)

DOMAIN_SOURCE_MAP: dict[str, str] = {
    "aljazeera.com": "Al Jazeera",
    "bbc.co.uk": "BBC",
    "bbc.com": "BBC",
    "npr.org": "NPR",
    "theguardian.com": "The Guardian",
    "dw.com": "DW",
    "foxnews.com": "Fox News",
    "nytimes.com": "New York Times",
    "washingtonpost.com": "Washington Post",
    "france24.com": "France 24",
    "reuters.com": "Reuters",
    "apnews.com": "AP News",
}

ACTOR_KEYWORDS: tuple[str, ...] = (
    "u.s.",
    "united states",
    "us military",
    "american",
    "pentagon",
    "white house",
    "trump",
    "iran",
    "iranian",
    "israel",
    "israeli",
    "idf",
    "tehran",
    "khamenei",
    "irgc",
    "hezbollah",
    "houthi",
    "hamas",
    "russia",
    "russian",
    "ukraine",
    "ukrainian",
    "nato",
    "china",
    "taiwan",
    "north korea",
    "syria",
    "yemen",
    "gaza",
    "west bank",
    "middle east",
)

CONFLICT_KEYWORDS: tuple[str, ...] = (
    "strike",
    "airstrike",
    "air strike",
    "missile",
    "drone",
    "attack",
    "retaliation",
    "escalation",
    "military",
    "operation epic fury",
    "epic fury",
    "war",
    "conflict",
    "bomb",
    "bombing",
    "offensive",
    "invasion",
    "troops",
    "deployment",
    "sanctions",
    "ceasefire",
    "cease-fire",
    "casualties",
    "killed",
    "deaths",
    "weapon",
    "nuclear",
    "hostage",
    "siege",
    "shelling",
    "artillery",
    "airspace",
    "naval",
    "warship",
    "intercept",
    "retaliate",
    "tension",
)

BREAKING_HINTS: tuple[str, ...] = (
    "breaking",
    "urgent",
    "strike",
    "escalation",
    "just in",
    "developing",
)

POLL_INTERVAL_SECONDS = 120

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
    # Track URLs added in this run to avoid cross-feed duplicates
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        # Fetch all feeds concurrently
        results = await asyncio.gather(
            *(_fetch_feed(client, url) for url in RSS_FEEDS),
            return_exceptions=True,
        )

    async with SessionLocal() as session:
        # Disable autoflush to prevent UNIQUE constraint errors during SELECT
        session.autoflush = False

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
                if url in existing_map or url in seen_urls:
                    # Backfill description if missing
                    if url in existing_map and not existing_map[url] and summary:
                        stmt = select(NewsAlert).where(NewsAlert.url == url)
                        row = await session.execute(stmt)
                        alert = row.scalar_one_or_none()
                        if alert is not None:
                            alert.description = summary[:4000]
                    continue

                seen_urls.add(url)
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
