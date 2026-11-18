"""Read the permanent source registry and produce a deterministic discovery queue.

No scraping or invented tips. Outputs public discovery URLs for a permitted
collector / human review; publication timestamps and authorship remain required.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

REGISTRY = Path(__file__).with_name("expert_sources.json")

def load_registry(path=REGISTRY):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sources = data["sources"]
    ids = set()
    for source in sources:
        sid = source["id"]
        if sid in ids:
            raise ValueError("Duplicate source id: " + sid)
        ids.add(sid)
        for key in ("homepage", "discovery_url"):
            url = urlparse(source[key])
            if url.scheme != "https" or not url.netloc:
                raise ValueError("Non-HTTPS URL for " + sid + ": " + key)
        if not isinstance(source["priority"], int) or source["priority"] < 1:
            raise ValueError("Invalid priority: " + sid)
    return data

def discovery_queue(registry, include_homepage_only=True):
    sources = registry["sources"]
    if not include_homepage_only:
        sources = [s for s in sources if s["status"] != "homepage_only"]
    return [
        {"source_id": s["id"], "name": s["name"],
         "url": s["discovery_url"], "priority": s["priority"],
         "known_analysts": s["known_analysts"], "verification_status": s["status"],
         "collection_state": "NOT_FETCHED"}
        for s in sorted(sources, key=lambda s: (s["priority"], s["id"]))
    ]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registry", type=Path, default=REGISTRY)
    p.add_argument("--output", type=Path, default=Path("expert_discovery_queue.json"))
    p.add_argument("--known-sections-only", action="store_true")
    args = p.parse_args()
    registry = load_registry(args.registry)
    queue = discovery_queue(registry, not args.known_sections_only)
    args.output.write_text(json.dumps({"schema_version": 1, "sources": queue}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"Queued {len(queue)} known source locations; no pages fetched.")

if __name__ == "__main__":
    main()
