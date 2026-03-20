# Community Guardian

**Candidate:** Pawan Mugalihalli
**Role:** New Grad SWE — Palo Alto Networks Take-Home
**Time Spent:** 6 hours
**Option chosen:** Option 3 — Community Safety & Digital Wellness
**AI tools used:** Claude (architecture design, code review), Groq llama-3.1-8b-instant (runtime AI enrichment)

---
***Video Demo Link: *** https://youtu.be/CqWhsqtC5Ps
---

## What It Does

Community Guardian is a safety digest platform that takes raw incident reports, uses AI to filter noise and categorise what matters, and presents users with calm, actionable alerts relevant to their location.

The core problem: people are overwhelmed by safety information scattered across news and social media — either too much noise or no context on what to do. This app gives a single, curated view.

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- A free Groq API key — steps below

### Getting a Groq API Key (free, no credit card)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up with your Google account or email
3. In the left sidebar click **API Keys**
4. Click **Create API Key** — give it any name
5. Copy the key (shown only once)
6. Paste it as `GROQ_API_KEY` in your `.env` file

### Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd community-guardian

# 2. Copy env file and fill in your values
cp .env.example .env
# Open .env and add:
#   GROQ_API_KEY=your_key_here
#   DJANGO_SECRET_KEY=any_long_random_string

# 3. Start the database and backend
docker-compose up --build -d

# 4. Run migrations
docker-compose exec backend python manage.py migrate

# 5. Load the synthetic dataset (15 fake incidents, no real data)
docker-compose exec backend python manage.py load_sample_data

# 6. Trigger the enrichment batch job manually
#
# Why: AI enrichment runs on a background cron job every 5 minutes.
# This design keeps the read path fast — the feed is always a pure
# DB query with no AI involved. Running it manually here means you
# see enriched incidents immediately rather than waiting 5 minutes.
#
docker-compose exec backend python manage.py shell -c \
  "from incidents.services.enrichment_service import EnrichmentService; EnrichmentService.enrich_pending()"

# 7. Open the app
open http://localhost:8000
```

### Run Tests

```bash
docker-compose exec backend python manage.py test incidents.tests
# Ran 5 tests — OK
```

---

## Architecture

### Data Flow
Write path:
  POST /api/incidents/ → saved raw immediately (unenriched)
  APScheduler (every 5 min) → queries ai_enriched=False
  → splits into chunks → sends each chunk to Groq together
  → if Groq fails on a chunk → keyword fallback runs for that chunk
  → writes enrichment back (category, severity, is_noise, action_steps)
  → continues to next chunk regardless

Read path:
  GET /api/incidents/ → pure DB query (is_noise=False)
  No AI on the read path — always fast, always available

AI runs at **write time**, not read time. This means the feed is always a pure database read — it works even when the AI service is completely down.

Batching incidents together (not one by one) lets Groq spot duplicate reports of the same event across the batch — something per-incident processing cannot do.

### Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Django + DRF | Requirement; solid ORM, batteries included |
| AI | Groq llama-3.1-8b-instant | Free tier, no credit card, fast JSON output |
| Fallback | Keyword matching (pure Python) | Zero dependencies, never fails |
| Scheduler | APScheduler | Runs inside Django, no extra infrastructure |
| Database | PostgreSQL | Better concurrent writes and index support vs SQLite |
| Auth | Django AbstractUser | Single model — name, location, concerns live directly on User |
| Frontend | Django templates + vanilla JS | Backend-heavy project, no framework needed |

### Folder Structure

```
community-guardian/
├── config/                      # Django project settings and URLs
├── incidents/
│   ├── models/
│   │   ├── user.py              # AbstractUser + name, location, concerns
│   │   ├── incident.py          # Raw + enriched fields + is_enriched, ai_enriched, is_noise flags
│   │   └── digest_log.py        # Logs every personalised feed request
│   ├── services/
│   │   ├── incident_service.py  # CRUD + composable filter methods
│   │   ├── enrichment_service.py # Orchestrates batch enrichment (AI vs fallback per chunk)
│   │   ├── groq_service.py      # Groq API call + JSON parsing
│   │   ├── fallback_service.py  # Keyword-based categorisation
│   │   ├── digest_service.py    # DigestLog write
│   │   └── profile_service.py   # User profile CRUD + concern validation
│   ├── views/
│   │   ├── __init__.py          # Exports IncidentViewSet, UserProfileViewSet
│   │   ├── incident_views.py    # List, create, retrieve, partial_update
│   │   ├── profile_views.py     # Create, retrieve, partial_update
│   │   └── api_exceptions.py    # @handle_exceptions decorator — maps ValueError to 404/400
│   ├── ui_views.py              # Django template views (feed, profile, report)
│   ├── auth_views.py            # Login, signup, logout
│   ├── scheduler.py             # APScheduler — starts enrichment job on Django startup
│   └── tests/
│       ├── test_happy_path.py
│       └── test_edge_cases.py
├── templates/
│   ├── base.html                # Shared nav, CSS variables, fonts
│   └── incidents/
│       ├── feed.html            # Safety feed with public/personalised toggle
│       ├── profile.html         # View + edit profile
│       ├── report.html          # Submit incident form
│       ├── login.html
│       └── signup.html
├── data/
│   └── incidents_sample.json    # 15 synthetic incidents (committed, no real data)
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

---

## AI Feature + Fallback

### AI Path (Groq)
Incidents are sent in batches to `llama-3.1-8b-instant`. The prompt instructs the model to:
1. Determine if each incident is noise (venting, complaints, irrelevant posts)
2. Categorise real incidents as `physical`, `digital`, or `weather`
3. Rate severity 1–5
4. Write one calm, actionable step

### Fallback Path (Keyword Matching)
If Groq fails for any reason (quota, timeout, network error) the fallback fires automatically for that chunk. It uses keyword lists to classify incidents and assigns conservative fixed severity scores. The job continues to the next chunk regardless of whether a previous chunk failed.

### Enrichment Flags

| Flag | Default | Meaning |
|---|---|---|
| `is_enriched` | False | Has been processed by AI or fallback |
| `ai_enriched` | False | Was specifically processed by Groq |
| `is_noise` | False | Confirmed noise — excluded from feed |

The cron job queries `ai_enriched=False` on every run. This means incidents enriched by the fallback are **automatically retried** with Groq on the next batch — quality improves when AI recovers without any manual intervention.

### Feed Filtering

The feed shows all `is_noise=False` incidents — both enriched and pending. This means incidents appear immediately after submission, and gain category/severity/action detail once the batch job processes them.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/incidents/` | Submit a raw incident |
| GET | `/api/incidents/` | List all non-noise incidents |
| GET | `/api/incidents/?profile_id=1` | Personalised feed using profile defaults |
| GET | `/api/incidents/:id/` | Single incident detail |
| PATCH | `/api/incidents/:id/` | Update raw fields (title, description, location, source) |
| POST | `/api/profiles/` | Create user profile |
| GET | `/api/profiles/:id/` | Get profile |
| PATCH | `/api/profiles/:id/` | Update profile |

### Filter params (all optional, all stackable)

```
?location=Koramangala
?category=digital          # physical | digital | weather
?severity=3                # 3 = 3+, 4 = 4+, 5 = exactly 5
?search=phishing
?profile_id=1              # activates personalised mode
```

When `profile_id` is passed, the user's saved location and concern categories become default filters. Any additional params narrow further on top of those defaults. Manual overrides are always temporary — the profile is never mutated by a GET request.

### Error Handling

All view methods are wrapped with `@handle_exceptions` (defined in `views/api_exceptions.py`). This decorator maps `ValueError` containing "does not exist" to a DRF `NotFound` (404), other `ValueError` to `ValidationError` (400), and lets everything else propagate naturally. This keeps each view method free of try/except boilerplate while still returning clean structured error responses.

---

## UI Pages

| URL | Page |
|---|---|
| `/login/` | Sign in with username + password |
| `/signup/` | Create account — sets username, password, name, location, and concern categories in one form |
| `/incidents/` | Safety feed — toggle between public (all incidents + manual filters) and personalised (profile defaults) |
| `/profile/` | View profile (read-only) with inline edit mode toggle |
| `/report/` | Submit a new incident with example click-to-fill buttons |

---

## Tests

```bash
docker-compose exec backend python manage.py test incidents.tests
# Ran 5 tests in ~1.4s — OK
```

**Happy path** (`test_happy_path.py`) — 2 tests:
- Creates 5 incidents (3 real, 2 noise), runs enrichment, asserts feed returns only real incidents with valid category, severity (1–5), and non-empty action steps
- Hits `/api/incidents/?location=Koramangala` directly and asserts no noise leaks through the API response

**Edge cases** (`test_edge_cases.py`) — 3 tests:
- Mocks Groq to raise an exception — asserts fallback runs silently and all incidents are enriched with `ai_enriched=False`
- Asserts fallback result has correct structure (valid categories, severity within 1–5 range)
- Asserts fallback-enriched incidents (`ai_enriched=False`) are retried and upgraded when Groq recovers on the next batch run

Note: happy path tests make real Groq API calls. In CI/CD these should be mocked to avoid quota dependency. Edge case tests are fully offline by design.

---

## Synthetic Dataset

`data/incidents_sample.json` contains 15 fake incidents across 5 Bangalore neighbourhoods:
- Digital scams — phishing SMS, ATM skimming, data breaches, fraud calls
- Physical safety — theft, suspicious persons, chain snatching, gas leak
- Weather — waterlogging, thunderstorm warnings
- Intentional noise — venting and complaints to demonstrate filtering
- Intentional duplicates — to demonstrate batch-level deduplication by the model

Load with: `python manage.py load_sample_data` (safe to re-run — uses `get_or_create`)

---

## Tradeoffs & What I'd Build Next

**APScheduler vs Celery**: Used APScheduler (runs inside Django, zero extra infrastructure) instead of Celery + Redis. For production with high incident volume, Celery would give better reliability, retries, and horizontal scaling. The enrichment code is already structured as a plain function that would map directly to a Celery task with no refactoring.

**PostgreSQL over SQLite**: Chose PostgreSQL for concurrent write support and composite index performance (`is_noise`, `location`, `ai_enriched`). Tradeoff is slightly more setup — handled entirely by Docker Compose so the evaluator experience is a single command.

**Single User model via AbstractUser**: Extended `AbstractUser` directly with `name`, `location`, `concerns`. Eliminates the join overhead of a separate `UserProfile` table on every feed request. Tradeoff is tighter coupling between auth and app data — a larger team might prefer separation for cleaner ownership.

**Feed shows all non-noise incidents**: The feed filters only on `is_noise=False`, not `is_enriched=True`. This means incidents appear immediately on submission and gain enrichment detail progressively. Tradeoff is that very new incidents show without a category or action step until the next batch run.

**Re-enrichment by design**: The `ai_enriched` flag ensures fallback incidents are automatically retried when Groq recovers. No manual queue management needed.

**What I'd build next**:
- Push notifications when high-severity incidents appear near the user
- Celery + Redis for async enrichment so incident creation feels instant
- Explicit deduplication surface in the UI — Groq already spots related reports in a batch, surface this as "3 reports of the same incident"
- Distance-based location filtering instead of case-insensitive string match
- Admin panel to review and correct noise classifications
- Data retention policy for DigestLog

---

## Privacy Considerations

- Location is stored per user and used only for feed filtering — never shared with or logged to external services
- All incident data is synthetic — no real personal information is committed to the repo
- Passwords are hashed by Django's built-in PBKDF2 hasher
- API keys are loaded from environment variables via `.env` — never committed (`.gitignore` covers `.env`)
- `DigestLog` records what each user's feed returned and when — in production this would be covered by a data retention and deletion policy
