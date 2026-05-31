"""RSS feed ingestion — fetches articles from tech/startup feeds."""
import json
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
from sqlalchemy import text

from db.models import get_db_connection

logger = logging.getLogger(__name__)

FEEDS = {
    "techcrunch": "https://techcrunch.com/feed/",
    "venturebeat": "https://feeds.feedburner.com/venturebeat/SZYF",
    "sifted": "https://sifted.eu/feed",
    "the_batch": "https://www.deeplearning.ai/the-batch/feed/",
    "hacker_newsletter": "https://hackernewsletter.com/issues.rss",
}


def parse_date(entry) -> datetime | None:
    for field in ("published", "updated"):
        val = entry.get(field)
        if val:
            try:
                return parsedate_to_datetime(val).replace(tzinfo=None)
            except Exception:
                pass
    struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if struct:
        return datetime(*struct[:6])
    return None


def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries:
            entries.append(
                {
                    "source": name,
                    "external_id": entry.get("id") or entry.get("link", ""),
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:1000],
                    "url": entry.get("link", ""),
                    "published_at": parse_date(entry),
                    "raw": dict(entry),
                }
            )
        logger.info("RSS %s: fetched %d entries", name, len(entries))
        return entries
    except Exception as e:
        logger.error("Failed to fetch RSS %s: %s", name, e)
        return []


def store_articles(articles: list[dict]) -> int:
    conn = get_db_connection()
    inserted = 0
    try:
        for a in articles:
            if not a.get("external_id"):
                continue
            conn.execute(
                text("""
                    INSERT INTO raw_articles
                        (source, external_id, title, summary, url,
                         published_at, score, num_comments, raw_json)
                    VALUES
                        (:source, :external_id, :title, :summary, :url,
                         :published_at, 0, 0, :raw_json)
                    ON CONFLICT (source, external_id) DO NOTHING
                """),
                {
                    "source": a["source"],
                    "external_id": str(a["external_id"])[:200],
                    "title": a["title"],
                    "summary": a["summary"],
                    "url": a["url"],
                    "published_at": a["published_at"],
                    "raw_json": json.dumps(a["raw"], default=str),
                },
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()
    logger.info("RSS: inserted %d articles", inserted)
    return inserted


def run():
    all_articles = []
    for name, url in FEEDS.items():
        all_articles.extend(fetch_feed(name, url))
    return store_articles(all_articles)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
