# ATS job boards directory: 15,000+ company career boards on Greenhouse, Lever, Ashby, Workable, SmartRecruiters and Recruitee

An open list of company job boards hosted on six applicant tracking systems (ATS), each one checked against the system's public job-board API. Use it to build a job aggregator, track hiring at a set of companies, or find out which ATS a company uses.

<!-- stats -->
Verified on 2026-11-16.

| System | Boards | Open jobs when verified |
|---|---:|---:|
| greenhouse | 5,347 | 191,722 |
| ashby | 3,322 | 62,586 |
| workable | 3,177 | 132,874 |
| recruitee | 2,041 | 33,679 |
| smartrecruiters | 1,461 | 244,949 |
| lever | 299 | 27,248 |
| **Total** | **15,647** | **693,058** |
<!-- /stats -->

Only boards that answered with at least one open job on the verification date are included.

## Files

| File | What it is |
|---|---|
| [`boards.csv`](boards.csv) | The directory. One row per company board. |
| [`fetch_jobs.py`](fetch_jobs.py) | Small example (Python, standard library only) that reads open jobs for any board in the list. |

### `boards.csv` columns

| Column | Example | Notes |
|---|---|---|
| `ats` | `greenhouse` | One of `greenhouse`, `lever`, `ashby`, `workable`, `smartrecruiters`, `recruitee`. |
| `slug` | `stripe` | The company's identifier inside that system. |
| `company_name` | `Stripe` | As reported by the board; empty when the system does not report one. |
| `open_jobs` | `512` | Open jobs on the verification date. A size hint, not a live number. |
| `board_url` | `https://boards.greenhouse.io/stripe` | The human-readable board. |
| `api_url` | `https://boards-api.greenhouse.io/v1/boards/stripe/jobs` | Public JSON endpoint with the board's jobs. |

Rows are grouped by system and sorted by `open_jobs`, largest first.

## Public job-board endpoints

All six systems publish jobs through unauthenticated JSON endpoints, made so that companies can embed their openings on their own sites. No key, no login.

| System | Endpoint | Notes |
|---|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs` | Add `?content=true` for descriptions. |
| Lever | `https://api.lever.co/v0/postings/{slug}?mode=json` | EU accounts live on `api.eu.lever.co`. |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{slug}` | Add `?includeCompensation=true` for pay ranges. |
| Workable | `https://apply.workable.com/api/v1/widget/accounts/{slug}` | Add `?details=true` for descriptions. Rejects fast bursts with HTTP 429. |
| SmartRecruiters | `https://api.smartrecruiters.com/v1/companies/{slug}/postings` | Paginated: `limit` (max 100) and `offset`. Returns an empty list for unknown slugs. |
| Recruitee | `https://{slug}.recruitee.com/api/offers/` | Descriptions are included. |

## Quick start

```bash
# jobs from three boards
python fetch_jobs.py greenhouse:stripe ashby:openai lever:spotify

# data engineering jobs at the 50 largest Greenhouse boards
python fetch_jobs.py --ats greenhouse --top 50 --title "data engineer" > jobs.jsonl
```

The script sends one request per second and stops on HTTP 429. Please keep it that way: these endpoints are free because people do not hammer them.

## Need all the jobs, not the list?

Reading every board means one request per company at least, per-system rate limits, retries, pagination and six different response formats. If you would rather not maintain that, the same directory is built into a hosted scraper:

**[Career Site Jobs Search on Apify](https://apify.com/storesignal/ats-jobs-scraper)** returns jobs from all boards in this list (or your own list) in one normalized schema, with filters for title keywords, location, remote and posting date. It costs $1 per 1,000 jobs returned, plus a flat $0.30 for a run that scans more than 500 boards; boards with no matching jobs are free. A walkthrough with real numbers and code: [Who is hiring for RevOps right now? Turn 690,000 live job posts into a lead list](https://dev.to/storesignalhq/who-is-hiring-for-revops-right-now-turn-690000-live-job-posts-into-a-lead-list-47lb).

## How the list was built

1. Candidate board URLs come from the [Common Crawl](https://commoncrawl.org/) URL index (open data): every URL on the six systems' board hosts, reduced to unique company slugs.
2. Each candidate was requested once from the system's public job-board endpoint, slowly.
3. Boards that returned at least one open job were kept, with the job count and the company name the board reports.

The list is a snapshot and it ages: companies change systems, close boards or pause hiring. Expect a few percent of rows to return 404 or an empty list a month after the verification date. It is refreshed about once a month.

## What is not here

- No job postings and no descriptions. Fetch them from the boards (see above).
- No personal data. The list contains company identifiers and public URLs only.
- No boards behind a login, and no systems other than the six above.

## Corrections and removal

If your company's board should not be listed, or a row is wrong, open an issue or write to storesignalhq@proton.me. Removal requests are honored without questions.

## License

The directory (`boards.csv`) is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use it for anything, including commercial products, and credit "StoreSignal ATS job boards directory" with a link to this repository. `fetch_jobs.py` is released under the MIT license. Company names and trademarks belong to their owners; this project is not affiliated with any of the listed systems or companies.
