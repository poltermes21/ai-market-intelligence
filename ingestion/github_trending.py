"""GitHub Trending scraper — parses trending repos for multiple languages."""
import logging
from datetime import date

import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

from db.models import get_db_connection

logger = logging.getLogger(__name__)

LANGUAGES = ["python", "typescript", "rust", "go", "javascript"]
BASE_URL = "https://github.com/trending"


def scrape_trending(language: str = "python", since: str = "daily") -> list[dict]:
    url = f"{BASE_URL}/{language}?since={since}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MarketIntelligenceBot/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error("GitHub trending fetch error (%s): %s", language, e)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    repos = []

    for article in soup.select("article.Box-row"):
        try:
            name_tag = article.select_one("h2 a")
            repo_name = name_tag["href"].lstrip("/") if name_tag else ""

            desc_tag = article.select_one("p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            stars_tag = article.select("a.Link--muted")[0] if article.select("a.Link--muted") else None
            stars_text = stars_tag.get_text(strip=True).replace(",", "") if stars_tag else "0"
            try:
                stars = int(stars_text)
            except ValueError:
                stars = 0

            forks_tag = article.select("a.Link--muted")[1] if len(article.select("a.Link--muted")) > 1 else None
            forks_text = forks_tag.get_text(strip=True).replace(",", "") if forks_tag else "0"
            try:
                forks = int(forks_text)
            except ValueError:
                forks = 0

            repos.append(
                {
                    "repo_name": repo_name,
                    "language": language,
                    "stars": stars,
                    "forks": forks,
                    "description": description,
                }
            )
        except Exception as e:
            logger.debug("Parse error for repo article: %s", e)

    logger.info("GitHub trending %s: scraped %d repos", language, len(repos))
    return repos


def store_repos(repos: list[dict]) -> int:
    conn = get_db_connection()
    today = date.today()
    inserted = 0
    try:
        for repo in repos:
            if not repo.get("repo_name"):
                continue
            conn.execute(
                text("""
                    INSERT INTO raw_github_trending
                        (repo_name, language, stars, forks, description, trending_date)
                    VALUES
                        (:repo_name, :language, :stars, :forks, :description, :trending_date)
                    ON CONFLICT (repo_name, trending_date) DO NOTHING
                """),
                {
                    "repo_name": repo["repo_name"],
                    "language": repo["language"],
                    "stars": repo["stars"],
                    "forks": repo["forks"],
                    "description": repo["description"],
                    "trending_date": today,
                },
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()
    logger.info("GitHub trending: inserted %d repos", inserted)
    return inserted


def run():
    all_repos = []
    for lang in LANGUAGES:
        all_repos.extend(scrape_trending(lang))
    return store_repos(all_repos)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
