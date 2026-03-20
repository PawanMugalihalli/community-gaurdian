# Community Guardian

| | |
|---|---|
| **Candidate** | Pawan Mugalihalli |
| **Role** | New Grad SWE — Palo Alto Networks Take-Home |
| **Time Spent** | 6 hours |
| **Option** | Option 3 — Community Safety & Digital Wellness |
| **AI tools used** | Claude (architecture design, code review), Groq llama-3.1-8b-instant (runtime AI enrichment) |

---

**Video Demo:** https://youtu.be/CqWhsqtC5Ps

---

## Submission Details

### AI Disclosure

**Did you use an AI assistant?** Yes — Claude (Anthropic) for architecture design and code review. Groq llama-3.1-8b-instant is used as the runtime AI feature inside the app itself.

**How did you verify the suggestions?**
Every architectural decision was discussed and reasoned through before implementation — not accepted blindly. I questioned and revised several design choices during the process (e.g. whether AI should run at read time or write time, single model vs separate UserProfile, APScheduler vs Celery). Code suggestions were reviewed for correctness, tested manually via curl and the UI, and covered by the test suite.

**One example of a suggestion I rejected or changed:**
Two examples worth noting.

First — the initial design ran AI enrichment on every digest request. Every time a user loaded their feed, Groq was called. I rejected this because it made the read path dependent on AI availability and added latency to every page load. I redesigned it so AI runs at write time in a background batch job, making the feed a pure DB query. This was a deliberate systems design decision, not a copy-paste.

Second — the initial design had two separate endpoints: `/api/incidents/` for the public feed and `/api/digest/` for the personalised feed. I rejected this because the separation was artificial — both endpoints returned the same data shape with only filtering logic different. I merged them into a single `/api/incidents/` endpoint where passing `?profile_id=` activates personalised mode. This kept the API surface clean and avoided maintaining two endpoints that did essentially the same thing.

### Tradeoffs & Prioritization

**What I cut to stay within the time limit:**
- Safe Circles (encrypted status sharing with trusted contacts) — designed but not implemented
- Real-time notifications — out of scope for a prototype
- Distance-based location filtering — used case-insensitive string match instead, hardcoded location dropdowns in UI prevent mismatches
- Re-enrichment UI — the retry logic exists in the backend but there's no admin interface to trigger or monitor it

**What I'd build next with more time:**
- Safe Circles — trusted contact groups with Fernet-encrypted status updates during emergencies
- Celery + Redis for async enrichment so incident creation feels instant rather than queued
- Push notifications when high-severity incidents appear near the user
- Explicit deduplication surface in the UI — Groq already spots related reports in a batch, surface this as "3 reports of the same incident"
- Admin panel to review and correct noise classifications
- Data retention policy for DigestLog

**Known limitations:**
- Happy path tests make real Groq API calls — in CI/CD these should be mocked to avoid quota dependency
- APScheduler runs inside the Django process — in production this should be Celery so the enrichment job doesn't compete with web requests for resources
- The Groq free tier has rate limits — if quota is exceeded the fallback runs automatically, but AI enrichment will not retry until quota resets
- Location matching is string-based — handled by hardcoding location dropdowns in the UI to prevent mismatches

**Key tradeoffs made:**
- **APScheduler vs Celery** — APScheduler runs inside Django with zero extra infrastructure. Celery would give better reliability and horizontal scaling in production but requires Redis and a separate worker process, which adds setup complexity for a take-home evaluation
- **AI at write time vs read time** — running enrichment in a background job means the feed is always a pure DB query. Tradeoff is that very new incidents appear without category or action steps until the next batch run (up to 5 minutes)
- **Single User model via AbstractUser** — eliminates a join on every feed request. Tradeoff is tighter coupling between auth and app data
- **Single `/api/incidents/` endpoint** — merged the public and personalised feeds into one endpoint with an optional `?profile_id=` param. Tradeoff is slightly more logic in one place, but avoids maintaining two endpoints that return the same data shape
- **PostgreSQL over SQLite** — better concurrent write support and composite index performance. Tradeoff is slightly more setup, handled entirely by Docker Compose

---

## What It Does

Community Guardian is a safety digest platform that takes raw incident reports, uses AI to filter noise and categorise what matters, and presents users with calm, actionable alerts relevant to their location.

The core problem: people are overwhelmed by safety information scattered across news and social media — either too much noise or no context on what to do. This app gives a single, curated view.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Django + DRF | Solid ORM, batteries included |
| AI | Groq llama-3.1-8b-instant | Free tier, no credit card, fast JSON output |
| Fallback | Keyword matching (pure Python) | Zero dependencies, never fails |
| Scheduler | APScheduler | Runs inside Django, no extra infrastructure |
| Database | PostgreSQL | Better concurrent writes and index support vs SQLite |
| Auth | Django AbstractUser | Single model — name, location, concerns live directly on User |
| Frontend | Django templates + vanilla JS | Backend-heavy project, no framework needed |

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

# 5. Load the synthetic dataset (50 fake incidents, no real data)
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

```
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
```

AI runs at **write time**, not read time. This means the feed is always a pure database read — it works even when the AI service is completely down.

Batching incidents together (not one by one) lets Groq spot duplicate reports of the same event across the batch — something per-incident processing cannot do.

### Folder Structure

```
community-guardian/
├── config/                       # Django project settings and URLs
├── incidents/
│   ├── models/
│   │   ├── user.py               # AbstractUser + name, location, concerns
│   │   ├── incident.py           # Raw + enriched fields + is_enriched, ai_enriched, is_noise flags
│   │   └── digest_log.py         # Logs every personalised feed request
│   ├── services/
│   │   ├── incident_service.py   # CRUD + composable filter methods
│   │   ├── enrichment_service.py # Orchestrates batch enrichment (AI vs fallback per chunk)
│   │   ├── groq_service.py       # Groq API call + JSON parsing
│   │   ├── fallback_service.py   # Keyword-based categorisation
│   │   ├── digest_service.py     # DigestLog write
│   │   └── profile_service.py    # User profile CRUD + concern validation
│   ├── views/
│   │   ├── __init__.py           # Exports IncidentViewSet, UserProfileViewSet
│   │   ├── incident_views.py     # List, create, retrieve, partial_update
│   │   ├── profile_views.py      # Create, retrieve, partial_update
│   │   └── api_exceptions.py     # @handle_exceptions decorator — maps ValueError to 404/400
│   ├── ui_views.py               # Django template views (feed, profile, report)
│   ├── auth_views.py             # Login, signup, logout
│   ├── scheduler.py              # APScheduler — starts enrichment job on Django startup
│   └── tests/
│       ├── test_happy_path.py
│       └── test_edge_cases.py
├── templates/
│   ├── base.html                 # Shared nav, CSS variables, fonts
│   └── incidents/
│       ├── feed.html             # Safety feed with public/personalised toggle
│       ├── profile.html          # View + edit profile
│       ├── report.html           # Submit incident form
│       ├── login.html
│       └── signup.html
├── data/
│   └── incidents_sample.json     # 50 synthetic incidents (committed, no real data)
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
| `/` | Safety feed — toggle between public (all incidents + manual filters) and personalised (profile defaults) |
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

`data/incidents_sample.json` contains 50 fake incidents across 3 Bangalore neighbourhoods (Koramangala, HSR Layout, Whitefield):
- Digital scams — phishing SMS, ATM skimming, data breaches, fraud calls, UPI fraud, vishing
- Physical safety — theft, suspicious persons, chain snatching, gas leak, fire, drunk driver
- Weather — waterlogging, thunderstorm warnings, flash floods, heatwave advisory
- Intentional noise — venting and complaints to demonstrate filtering
- Intentional duplicates — to demonstrate batch-level deduplication by the model

Load with: `python manage.py load_sample_data` (safe to re-run — uses `get_or_create`)

---

## Privacy Considerations

- Location is stored per user and used only for feed filtering — never shared with or logged to external services
- All incident data is synthetic — no real personal information is committed to the repo
- Passwords are hashed by Django's built-in PBKDF2 hasher
- API keys are loaded from environment variables via `.env` — never committed (`.gitignore` covers `.env`)
- `DigestLog` records what each user's feed returned and when — in production this would be covered by a data retention and deletion policy
