"""Capture public article leads for offline candidate extraction only.

No selections are verified or fed to betting models. Fail closed when robots
cannot be checked, content is not HTML, or an article leaves its source host.
"""
import argparse
import datetime
import json
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path
from monty_expert_candidate_extract import extract

USER_AGENT = "MontyResearchBot/0.1 (research; respect robots.txt)"
MAX_BYTES = 350_000

class NoRedirects(urllib.request.HTTPRedirectHandler):
    # A redirect must never fetch an unreviewed URL or bypass its robots check.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def capture_article(source_url, article_url, fetcher=None, robots_allowed=None, clock=None):
    source = urllib.parse.urlsplit(source_url)
    article = urllib.parse.urlsplit(article_url)
    if (source.scheme != "https" or article.scheme != "https"
            or not source.hostname or article.hostname != source.hostname
            or source.username or source.password or source.port not in (None, 443)
            or article.username or article.password or article.port not in (None, 443)):
        return {"url": article_url, "status": "rejected", "reason": "Unsafe or cross-host article URL", "candidates": []}
    if robots_allowed is None:
        robots = urllib.robotparser.RobotFileParser()
        robots.set_url(f"https://{article.hostname}/robots.txt")
        try:
            robots.read()
            allowed = robots.can_fetch(USER_AGENT, article_url)
        except Exception:
            allowed = False
    else:
        allowed = robots_allowed(article_url)
    if not allowed:
        return {"url": article_url, "status": "rejected", "reason": "Robots unavailable or disallowed", "candidates": []}
    try:
        if fetcher is None:
            req = urllib.request.Request(article_url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
            with urllib.request.build_opener(NoRedirects()).open(req, timeout=10) as response:
                final = urllib.parse.urlsplit(response.geturl())
                if final.scheme != "https" or final.hostname != article.hostname:
                    raise ValueError("Redirect left allowed host")
                if "text/html" not in response.headers.get("Content-Type", "").lower():
                    raise ValueError("Not HTML")
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("Article too large")
                html = raw.decode("utf-8", "replace")
        else:
            html = fetcher(article_url)
            if len(html.encode("utf-8")) > MAX_BYTES:
                raise ValueError("Article too large")
        now = (clock or (lambda: datetime.datetime.now(datetime.timezone.utc)))()
        if now.tzinfo is None:
            raise ValueError("Capture time must be timezone-aware")
        candidates = extract(html, article_url, captured_at=now.isoformat())
        return {"url": article_url, "status": "captured_unverified", "captured_at": now.isoformat(),
                "candidates": candidates}
    except Exception as exc:
        return {"url": article_url, "status": "unavailable", "reason": type(exc).__name__, "candidates": []}

def process_leads(data, limit=10, fetcher=None, robots_allowed=None, clock=None):
    results = []
    for source in data.get("sources", []):
        for article in source.get("articles", [])[:max(0, limit)]:
            results.append(capture_article(
                source.get("source_url", "") or source.get("landing_url", "") or
                SOURCE_URLS.get(source.get("source", ""), ""),
                article.get("url", ""), fetcher=fetcher,
                robots_allowed=robots_allowed, clock=clock))
    return {"articles": results, "verified_tip_count": 0, "status": "RESEARCH_ONLY_NO_BET"}

from monty_expert_article_discovery import SOURCES as SOURCE_URLS

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("leads")
    parser.add_argument("--output", default="expert_article_candidates.json")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    result = process_leads(json.loads(Path(args.leads).read_text()), limit=args.limit)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"articles": len(result["articles"]),
                      "candidates": sum(len(a["candidates"]) for a in result["articles"]),
                      "verified_tip_count": 0}))
