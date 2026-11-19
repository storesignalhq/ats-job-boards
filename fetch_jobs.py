"""Fetch open jobs for boards listed in boards.csv, straight from the public job-board APIs.

Usage:
    python fetch_jobs.py greenhouse:stripe ashby:openai lever:spotify
    python fetch_jobs.py --ats ashby --top 20          # 20 largest Ashby boards from boards.csv
    python fetch_jobs.py --ats greenhouse --top 50 --title "data engineer" > jobs.jsonl

Prints one JSON object per job (JSON Lines): ats, company, title, location, url, posted_at.
Standard library only. One request per second on purpose: these are free public
endpoints, and some of them (Workable above all) reject fast bursts with HTTP 429.
SmartRecruiters is paginated (100 jobs per request); this script reads the first 1,000.
"""
import argparse
import csv
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = {"User-Agent": "ats-job-boards-example/1.0", "Accept": "application/json"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def greenhouse(slug):
    for j in get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")["jobs"]:
        yield j["title"], (j.get("location") or {}).get("name"), j["absolute_url"], j.get("first_published") or j.get("updated_at")


def lever(slug):
    for j in get(f"https://api.lever.co/v0/postings/{slug}?mode=json"):
        ts = j.get("createdAt")
        posted = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts / 1000)) if ts else None
        yield j["text"], (j.get("categories") or {}).get("location"), j["hostedUrl"], posted


def ashby(slug):
    for j in get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")["jobs"]:
        yield j["title"], j.get("location"), j["jobUrl"], j.get("publishedAt")


def workable(slug):
    for j in get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}")["jobs"]:
        loc = ", ".join(x for x in (j.get("city"), j.get("country")) if x)
        yield j["title"], loc or None, j.get("url") or j.get("shortlink"), j.get("published_on")


def smartrecruiters(slug):
    for offset in range(0, 1000, 100):
        page = get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={offset}")
        for j in page.get("content", []):
            loc = j.get("location") or {}
            place = ", ".join(x for x in (loc.get("city"), loc.get("country")) if x)
            yield j["name"], place or None, f"https://jobs.smartrecruiters.com/{slug}/{j['id']}", j.get("releasedDate")
        if offset + 100 >= page.get("totalFound", 0):
            break
        time.sleep(1)


def recruitee(slug):
    for j in get(f"https://{slug}.recruitee.com/api/offers/")["offers"]:
        yield j["title"], j.get("location"), j.get("careers_url"), j.get("published_at")


FETCH = {f.__name__: f for f in (greenhouse, lever, ashby, workable, smartrecruiters, recruitee)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("boards", nargs="*", help="ats:slug pairs")
    ap.add_argument("--ats", choices=sorted(FETCH), help="take boards of this system from boards.csv")
    ap.add_argument("--top", type=int, default=10, help="how many boards to take with --ats (largest first)")
    ap.add_argument("--title", help="keep only jobs whose title contains this text (case-insensitive)")
    args = ap.parse_args()

    targets = [tuple(b.split(":", 1)) for b in args.boards]
    names = {}
    if args.ats:
        with open(pathlib.Path(__file__).with_name("boards.csv"), encoding="utf-8", newline="") as f:
            rows = [r for r in csv.DictReader(f) if r["ats"] == args.ats][: args.top]
        targets += [(r["ats"], r["slug"]) for r in rows]
        names = {(r["ats"], r["slug"]): r["company_name"] for r in rows}
    if not targets:
        ap.error("give ats:slug pairs or --ats")

    needle = args.title.lower() if args.title else None
    out = open(sys.stdout.fileno(), "w", encoding="utf-8", closefd=False)
    for i, (ats, slug) in enumerate(targets):
        if i:
            time.sleep(1)
        if ats not in FETCH:
            print(f"{ats}:{slug}: unknown system", file=sys.stderr)
            continue
        try:
            n = 0
            for title, location, url, posted in FETCH[ats](urllib.parse.quote(slug, safe="")):
                if needle and needle not in title.lower():
                    continue
                n += 1
                out.write(json.dumps({"ats": ats, "company": names.get((ats, slug)) or slug, "title": title,
                                      "location": location, "url": url, "posted_at": posted}, ensure_ascii=False) + "\n")
            print(f"{ats}:{slug}: {n} jobs", file=sys.stderr)
        except urllib.error.HTTPError as e:
            print(f"{ats}:{slug}: HTTP {e.code}", file=sys.stderr)
            if e.code == 429:
                print("rate limited, stopping instead of retrying", file=sys.stderr)
                break
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
            print(f"{ats}:{slug}: {type(e).__name__}: {e}", file=sys.stderr)
    out.flush()


if __name__ == "__main__":
    main()
