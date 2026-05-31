"""HackerNews ingestion — fetches top stories and 'who is hiring' posts."""
import json
import logging
from datetime import datetime

import requests
from sqlalchemy import text

from db.models import get_db_connection

logger = logging.getLogger(__name__)

HN_BASE = "https://hacker-news.firebaseio.com/v0"
HN_ALGOLIA = "https://hn.algolia.com/api/v1/search"


def fetch_top_stories(limit: int = 100) -> list[dict]:
    resp = requests.get(f"{HN_BASE}/topstories.json", timeout=10)
    resp.raise_for_status()
    story_ids = resp.json()[:limit]

    stories = []
    for story_id in story_ids:
        try:
            r = requests.get(f"{HN_BASE}/item/{story_id}.json", timeout=10)
            r.raise_for_status()
            item = r.json()
            if item and item.get("type") == "story":
                stories.append(item)
        except Exception as e:
            logger.warning("Failed to fetch story %s: %s", story_id, e)
    return stories


def fetch_hiring_posts() -> list[dict]:
    params = {"query": "who is hiring", "tags": "story", "hitsPerPage": 20}
    resp = requests.get(HN_ALGOLIA, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("hits", [])


def store_articles(stories: list[dict]) -> int:
    conn = get_db_connection()
    inserted = 0
    try:
        for s in stories:
            external_id = str(s.get("id", ""))
            if not external_id:
                continue
            published_at = None
            ts = s.get("time")
            if ts:
                published_at = datetime.utcfromtimestamp(ts)

            conn.execute(
                text("""
                    INSERT INTO raw_articles
                        (source, external_id, title, summary, url,
                         published_at, score, num_comments, raw_json)
                    VALUES
                        (:source, :external_id, :title, :summary, :url,
                         :published_at, :score, :num_comments, :raw_json)
                    ON CONFLICT (source, external_id) DO NOTHING
                """),
                {
                    "source": "hackernews",
                    "external_id": external_id,
                    "title": s.get("title", ""),
                    "summary": s.get("text", "")[:500] if s.get("text") else None,
                    "url": s.get("url", ""),
                    "published_at": published_at,
                    "score": s.get("score", 0),
                    "num_comments": s.get("descendants", 0),
                    "raw_json": json.dumps(s),
                },
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()
    logger.info("HackerNews: inserted %d articles", inserted)
    return inserted


def run():
    logger.info("Fetching HackerNews top stories...")
    stories = fetch_top_stories(limit=100)
    hiring = fetch_hiring_posts()
    all_items = stories + hiring
    return store_articles(all_items)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
