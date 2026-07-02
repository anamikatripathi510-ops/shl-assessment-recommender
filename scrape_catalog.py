"""
Utility script to re-scrape and refresh catalog.json from the SHL website.

The SHL product catalog pages are JavaScript-rendered, so most content cannot
be retrieved with a plain HTTP request. This script fetches what it can and
merges it with the hand-curated entries already in catalog.json.

Run with:
    python scrape_catalog.py
"""
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.shl.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

PAGES = [
    ("/products/assessments/personality-assessment/shl-occupational-personality-questionnaire-opq/", "Personality"),
    ("/products/assessments/personality-assessment/shl-motivation-questionnaire-mq/", "Personality"),
    ("/products/assessments/behavioral-assessments/situation-judgement-tests-sjt/", "Situational Judgement"),
    ("/products/assessments/behavioral-assessments/global-skills-assessment-gsa/", "Behavioral"),
    ("/products/assessments/skills-and-simulations/call-center-simulations/", "Skills & Simulations"),
    ("/products/assessments/skills-and-simulations/business-skills/", "Skills & Simulations"),
    ("/products/assessments/skills-and-simulations/coding-simulations/", "Skills & Simulations"),
    ("/products/assessments/skills-and-simulations/technical-skills/", "Skills & Simulations"),
    ("/products/assessments/skills-and-simulations/language-evaluation/", "Skills & Simulations"),
    ("/products/assessments/assessment-and-development-centers/", "Assessment Centre"),
    ("/products/assessments/job-focused-assessments/", "Job Focused"),
]

CATALOG_PATH = Path(__file__).parent / "catalog.json"


def scrape_page(path: str, test_type: str) -> dict | None:
    url = BASE + path
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            print(f"  SKIP {url} -> HTTP {r.status_code}")
            return None
        soup = BeautifulSoup(r.text, "lxml")
        h1 = soup.find("h1")
        name = h1.get_text(strip=True) if h1 else ""
        desc = ""
        for p in soup.find_all("p"):
            txt = p.get_text(strip=True)
            if len(txt) > 80 and "browser" not in txt.lower():
                desc = txt[:400]
                break
        if not name:
            print(f"  SKIP {url} -> no title found")
            return None
        print(f"  OK  {name[:60]}")
        return {"name": name, "url": url, "test_type": test_type, "description": desc}
    except Exception as e:
        print(f"  ERR {url}: {e}")
        return None


def main():
    existing = json.loads(CATALOG_PATH.read_text()) if CATALOG_PATH.exists() else []
    existing_urls = {e["url"] for e in existing}

    print("Scraping SHL pages...")
    scraped = []
    for path, test_type in PAGES:
        entry = scrape_page(path, test_type)
        if entry and entry["url"] not in existing_urls:
            scraped.append(entry)

    merged = existing + scraped
    CATALOG_PATH.write_text(json.dumps(merged, indent=2))
    print(f"\nDone. Total entries: {len(merged)}")


if __name__ == "__main__":
    main()
