-- AI Market Intelligence System — Database Schema

CREATE SCHEMA IF NOT EXISTS marts;

-- Raw job postings
CREATE TABLE IF NOT EXISTS raw_jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    external_id VARCHAR(200),
    title TEXT,
    company TEXT,
    location TEXT,
    description TEXT,
    salary_min NUMERIC,
    salary_max NUMERIC,
    currency VARCHAR(10),
    date_posted DATE,
    url TEXT,
    raw_json JSONB,
    ingested_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source, external_id)
);

-- Raw articles / news
CREATE TABLE IF NOT EXISTS raw_articles (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    external_id VARCHAR(200),
    title TEXT,
    summary TEXT,
    url TEXT,
    published_at TIMESTAMP,
    score INTEGER,
    num_comments INTEGER,
    raw_json JSONB,
    ingested_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source, external_id)
);

-- Raw startup launches
CREATE TABLE IF NOT EXISTS raw_startups (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    external_id VARCHAR(200),
    name TEXT,
    tagline TEXT,
    description TEXT,
    topics TEXT[],
    votes INTEGER,
    launch_date DATE,
    url TEXT,
    raw_json JSONB,
    ingested_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source, external_id)
);

-- Raw GitHub trending repos
CREATE TABLE IF NOT EXISTS raw_github_trending (
    id SERIAL PRIMARY KEY,
    repo_name TEXT,
    language TEXT,
    stars INTEGER,
    forks INTEGER,
    description TEXT,
    trending_date DATE,
    ingested_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (repo_name, trending_date)
);

-- Daily generated reports
CREATE TABLE IF NOT EXISTS daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE UNIQUE,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_raw_jobs_date ON raw_jobs (date_posted);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_company ON raw_jobs (company);
CREATE INDEX IF NOT EXISTS idx_raw_articles_published ON raw_articles (published_at);
CREATE INDEX IF NOT EXISTS idx_raw_articles_source ON raw_articles (source);
CREATE INDEX IF NOT EXISTS idx_raw_startups_launch ON raw_startups (launch_date);
CREATE INDEX IF NOT EXISTS idx_raw_github_date ON raw_github_trending (trending_date);
