"""ProductHunt GraphQL API ingestion — fetches today's top launches."""
import json
import logging
import os
from datetime import date

import requests
from sqlalchemy import text

from db.models import get_db_connection

logger = logging.getLogger(__name__)

PH_TOKEN_URL = "https://api.producthunt.com/v2/oauth/token"
PH_GRAPHQL = "https://api.producthunt.com/v2/api/graphql"

QUERY = """
query ($date: DateTime!) {
  posts(order: VOTES, postedAfter: $date, first: 50) {
    edges {
      node {
        id
        name
        tagline
        description
        votesCount
        createdAt
        website
        url
        topics {
          edges {
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""


def get_access_token() -> str:
    client_id = os.getenv("PRODUCTHUNT_CLIENT_ID", "")
    client_secret = os.getenv("PRODUCTHUNT_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError("PRODUCTHUNT_CLIENT_ID and PRODUCTHUNT_CLIENT_SECRET must be set in .env")
    resp = requests.post(
        PH_TOKEN_URL,
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_launches() -> list[dict]:
    try:
        access_token = get_access_token()
    except Exception as e:
        logger.warning("ProductHunt auth failed — skipping: %s", e)
        return []

    today = date.today().isoformat() + "T00:00:00Z"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"query": QUERY, "variables": {"date": today}}

    try:
        resp = requests.post(PH_GRAPHQL, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        edges = data.get("data", {}).get("posts", {}).get("edges", [])
        launches = []
        for edge in edges:
            node = edge.get("node", {})
            topics = [
                t["node"]["name"]
                for t in node.get("topics", {}).get("edges", [])
            ]
            node["_topics"] = topics
            launches.append(node)
        logger.info("ProductHunt: fetched %d launches", len(launches))
        return launches
    except Exception as e:
        logger.error("ProductHunt fetch error: %s", e)
        return []


def store_startups(launches: list[dict]) -> int:
    conn = get_db_connection()
    inserted = 0
    try:
        for item in launches:
            external_id = str(item.get("id", ""))
            if not external_id:
                continue

            created = item.get("createdAt", "")
            launch_date = None
            if created:
                try:
                    from datetime import datetime
                    launch_date = datetime.fromisoformat(created.replace("Z", "+00:00")).date()
                except Exception:
                    pass

            conn.execute(
                text("""
                    INSERT INTO raw_startups
                        (source, external_id, name, tagline, description,
                         topics, votes, launch_date, url, raw_json)
                    VALUES
                        (:source, :external_id, :name, :tagline, :description,
                         :topics, :votes, :launch_date, :url, :raw_json)
                    ON CONFLICT (source, external_id) DO NOTHING
                """),
                {
                    "source": "producthunt",
                    "external_id": external_id,
                    "name": item.get("name", ""),
                    "tagline": item.get("tagline", ""),
                    "description": item.get("description", ""),
                    "topics": item.get("_topics", []),
                    "votes": item.get("votesCount", 0),
                    "launch_date": launch_date,
                    "url": item.get("url", "") or item.get("website", ""),
                    "raw_json": json.dumps(item, default=str),
                },
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()
    logger.info("ProductHunt: inserted %d startups", inserted)
    return inserted


def run():
    launches = fetch_launches()
    return store_startups(launches)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
