# AI Market Intelligence System

End-to-end platform that ingests data from job boards, tech news, and startup sources daily,
transforms it with dbt, powers an LangGraph AI agent, and serves a Streamlit dashboard.

## Tech Stack
- **Orchestration**: Apache Airflow 2.8 (Docker)
- **Database**: PostgreSQL 15 (Docker)
- **Transformations**: dbt Core (dbt-postgres)
- **AI Agent**: LangChain + LangGraph + OpenAI GPT-4o
- **Frontend**: Streamlit
- **Containerization**: Docker Compose

## Project Structure
```
airflow/dags/        — 6 DAGs (5 ingestion + 1 daily report)
ingestion/           — Python scripts for each data source
db/                  — init.sql schema + SQLAlchemy connection module
dbt_project/         — staging views + mart tables
agent/               — LangGraph tools, graph, prompts
report/              — daily report generator (LLM-powered)
app/                 — Streamlit app (dashboard, chat, report pages)
```

## Quick Start
```bash
# 1. Fill in API keys in .env
cp .env .env.local  # edit with real keys

# 2. Start infrastructure
docker-compose up postgres airflow-init
docker-compose up -d

# 3. Access services
#   Airflow:   http://localhost:8080  (admin / admin)
#   Streamlit: http://localhost:8501

# 4. Trigger DAGs in order (or wait for daily schedule):
#   hackernews_ingestion → rss_feeds_ingestion → producthunt_ingestion
#   → adzuna_jobs_ingestion → github_trending_ingestion → daily_report
```

## Environment Variables (`.env`)
| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Required for agent + report generation |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | Free at developer.adzuna.com |
| `PRODUCTHUNT_API_KEY` | Free at producthunt.com/v2/oauth/applications |
| `GITHUB_TOKEN` | Optional — raises rate limit from 60 to 5000 req/hr |
| `DATABASE_URL` | Auto-set in Docker; set to localhost:5432 for local dev |

## Database Schema
Raw tables: `raw_jobs`, `raw_articles`, `raw_startups`, `raw_github_trending`, `daily_reports`
Staging views: `staging.stg_jobs`, `staging.stg_articles`, `staging.stg_startups`
Mart tables: `marts.trending_skills`, `marts.top_hiring_companies`, `marts.topic_volumes`, `marts.daily_snapshot`

## DAG Schedule
| DAG | Time (UTC) | Output |
|---|---|---|
| hackernews_ingestion | 07:00 | raw_articles |
| rss_feeds_ingestion | 07:30 | raw_articles |
| producthunt_ingestion | 08:00 | raw_startups |
| adzuna_jobs_ingestion | 08:30 | raw_jobs + mart tables |
| github_trending_ingestion | 09:00 | raw_github_trending |
| daily_report | 10:00 | daily_reports |

## Development Notes
- All ingestion scripts are idempotent (`ON CONFLICT DO NOTHING`)
- dbt `profiles.yml` uses env vars for DB connection — works both inside Docker and locally
- The agent tool `query_database` enforces read-only by checking SQL prefix (SELECT/WITH/EXPLAIN)
- `PYTHONPATH=/opt/airflow` is set in docker-compose so DAGs can import `ingestion.*` and `db.*`
- Use `psycopg2-binary` (not `psycopg2`) for easier installation
