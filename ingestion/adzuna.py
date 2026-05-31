"""Adzuna Jobs API ingestion — fetches job postings for AI/data roles."""
import json
import logging
import os
import re
from datetime import datetime

import requests
from sqlalchemy import text

from db.models import get_db_connection

logger = logging.getLogger(__name__)

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"
SEARCH_TERMS = [
    "data engineer",
    "machine learning engineer",
    "AI engineer",
    "backend developer",
    "data scientist",
    "MLOps",
    "LLM engineer",
]
COUNTRIES = ["gb", "us"]

SKILL_PATTERNS = [
    "Python", "SQL", "Spark", "Kafka", "dbt", "Airflow", "Docker",
    "Kubernetes", "AWS", "GCP", "Azure", "React", "FastAPI", "LangChain",
    "PyTorch", "TensorFlow", "Rust", "Go", "TypeScript", "GraphQL",
    "Scala", "Java", "R", "Tableau", "Power BI", "Snowflake", "Databricks",
]


def extract_skills(description: str) -> list[str]:
    if not description:
        return []
    found = []
    for skill in SKILL_PATTERNS:
        if re.search(rf"\b{re.escape(skill)}\b", description, re.IGNORECASE):
            found.append(skill)
    return found


def fetch_jobs(country: str, query: str, pages: int = 2) -> list[dict]:
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")
    if not app_id or not app_key:
        logger.warning("ADZUNA_APP_ID / ADZUNA_APP_KEY not set — skipping")
        return []

    jobs = []
    for page in range(1, pages + 1):
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 50,
            "what": query,
            "content-type": "application/json",
        }
        try:
            url = f"{ADZUNA_BASE}/{country}/search/{page}"
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            jobs.extend(data.get("results", []))
        except Exception as e:
            logger.error("Adzuna fetch error (%s, %s, p%d): %s", country, query, page, e)
            break
    logger.info("Adzuna %s '%s': fetched %d jobs", country, query, len(jobs))
    return jobs


def parse_salary(job: dict):
    sal_min = job.get("salary_min")
    sal_max = job.get("salary_max")
    try:
        sal_min = float(sal_min) if sal_min else None
        sal_max = float(sal_max) if sal_max else None
    except (TypeError, ValueError):
        sal_min = sal_max = None
    return sal_min, sal_max


def parse_date(job: dict):
    created = job.get("created")
    if not created:
        return None
    try:
        return datetime.fromisoformat(created.replace("Z", "+00:00")).date()
    except Exception:
        return None


def store_jobs(jobs: list[dict]) -> int:
    conn = get_db_connection()
    inserted = 0
    try:
        for j in jobs:
            external_id = str(j.get("id", ""))
            if not external_id:
                continue
            sal_min, sal_max = parse_salary(j)
            date_posted = parse_date(j)
            conn.execute(
                text("""
                    INSERT INTO raw_jobs
                        (source, external_id, title, company, location,
                         description, salary_min, salary_max, currency,
                         date_posted, url, raw_json)
                    VALUES
                        (:source, :external_id, :title, :company, :location,
                         :description, :salary_min, :salary_max, :currency,
                         :date_posted, :url, :raw_json)
                    ON CONFLICT (source, external_id) DO NOTHING
                """),
                {
                    "source": "adzuna",
                    "external_id": external_id,
                    "title": j.get("title", ""),
                    "company": j.get("company", {}).get("display_name", ""),
                    "location": j.get("location", {}).get("display_name", ""),
                    "description": j.get("description", ""),
                    "salary_min": sal_min,
                    "salary_max": sal_max,
                    "currency": "GBP" if j.get("currency", "GBP") == "GBP" else "USD",
                    "date_posted": date_posted,
                    "url": j.get("redirect_url", ""),
                    "raw_json": json.dumps(j),
                },
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()
    logger.info("Adzuna: inserted %d jobs", inserted)
    return inserted


def run():
    all_jobs = []
    for country in COUNTRIES:
        for term in SEARCH_TERMS:
            all_jobs.extend(fetch_jobs(country, term))
    return store_jobs(all_jobs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
