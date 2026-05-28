# Mini Project 2 — Submission

**Student:** Mingjing Zhang
**Course:** CSE552 — Full Stack Course
**Project:** Recompile Archive
**Date:** 2026-05-28

---

## 1. GitHub Repositories

| Repo | URL |
|---|---|
| Backend (FastAPI + PostgreSQL) | https://github.com/mingjing-zhang/project-2-api |
| Frontend (Next.js 16 + Tailwind) | https://github.com/mingjing-zhang/project-2-frontend |

Both repos are public. `.env` (backend) and `.env.local` (frontend) are gitignored.

---

## 2. Short description (lab submission item 3)

**Recompile Archive** is a personal CMS for the Bitcoin Script writing of *Aaron Recompile*. It organizes essays into named **series** (e.g. *Not Just HODLing — Real Bitcoin Script Engineering*, *OP_\* on Signet — Bitcoin Inquisition*) and renders each series as an ordered sequence of articles, while still surfacing standalone pieces in a flat list. From the UI you can browse series, drill into a series to see its articles in author-defined order, add new articles via a form that picks a series from a dropdown, edit an article's series/position inline, and delete articles or whole series (cascading). It would be used by the author to organize ~20+ published essays for navigation and to keep adding new ones without touching a database client.

---

## 3. How to run the whole stack

Backend + database (Docker Compose):
```bash
git clone https://github.com/mingjing-zhang/project-2-api.git
cd project-2-api
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/recompile" > .env
docker compose up --build -d
docker compose exec backend python seed.py   # one-time: load 3 series + 19 real articles
# Backend → http://localhost:8000  (Swagger at /docs)
```

Frontend (separate terminal):
```bash
git clone https://github.com/mingjing-zhang/project-2-frontend.git
cd project-2-frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm install
npm run dev
# Frontend → http://localhost:3000
```

---

## 4. Architecture at a glance

### The relationship (rubric's 20-point line)
```
Series (1) ────< (many) Article
   id                       id, title, subtitle, published_at, url, position
   name                     series_id  ──→ Series.id  (nullable)
   slug                     ⇒ position orders articles inside a series
   description              ⇒ null series_id ⇒ "standalone" article
   articles[] (relationship)
```

Implemented in [`models.py`](https://github.com/mingjing-zhang/project-2-api/blob/main/models.py) with `ForeignKey("series.id")`, `relationship("Article", back_populates=..., cascade="all, delete-orphan")`, and a server-side `order_by` clause that puts positioned articles first (`Article.position.asc().nullslast()`).

### Pydantic schemas demonstrate the join
- `SeriesResponse` — flat series
- `ArticleResponse` — flat article
- **`SeriesWithArticles`** — series + nested `articles: list[ArticleResponse]` ← this is what `GET /series/{id}` returns
- **`ArticleWithSeries`** — article + nested `series: SeriesResponse | None` ← this is what `GET /articles/{id}` returns

Both nested schemas are exercised by frontend pages.

### 9 API endpoints
| Method | Path | Notes |
|---|---|---|
| GET | `/series` | Flat list |
| GET | `/series/{id}` | **Includes articles inline** (the relationship) |
| POST | `/series` | Slug uniqueness enforced |
| PUT | `/series/{id}` | Partial update |
| DELETE | `/series/{id}` | Cascades to its articles |
| GET | `/articles` | Optional `?series_id=X` filter |
| GET | `/articles/{id}` | **Includes series inline** |
| POST | `/articles` | Validates `series_id` if provided |
| PUT | `/articles/{id}` | Used by inline edit on detail page |
| DELETE | `/articles/{id}` | |

### 6 frontend pages
| Path | Purpose |
|---|---|
| `/` | Landing, live counts of series + articles |
| `/series` | List of series cards with article counts (fetched per series) |
| `/series/[id]` | One series + its ordered articles + delete button |
| `/articles` | Flat list with series-filter dropdown |
| `/articles/[id]` | Article details + inline edit (series dropdown + position) + delete |
| `/articles/new` | Create form with series dropdown populated from `/series` |

---

## 5. Where each rubric line is satisfied

| Rubric line | Where to look |
|---|---|
| Next.js frontend with 3+ pages and navigation | 6 pages + sitewide nav in [`app/layout.tsx`](https://github.com/mingjing-zhang/project-2-frontend/blob/main/app/layout.tsx) |
| Data fetching with loading and error states | Every page that calls the API has `loading` + `error` state and early returns |
| Create, update, delete working in the UI | `app/articles/new/page.tsx` (POST), `app/articles/[id]/page.tsx` (PUT inline edit + DELETE), `app/series/[id]/page.tsx` (DELETE series) |
| FastAPI with 5+ endpoints | 9 endpoints in [`main.py`](https://github.com/mingjing-zhang/project-2-api/blob/main/main.py) |
| 2 database models with a relationship | [`models.py`](https://github.com/mingjing-zhang/project-2-api/blob/main/models.py) — Series and Article with `ForeignKey` + `relationship()` |
| Data persists in PostgreSQL | Postgres in Docker with named volume `pgdata` |
| CORS configured correctly | `main.py` — `CORSMiddleware` whitelisting `http://localhost:3000` |
| Code organized into proper files | `database.py` / `models.py` / `schemas.py` / `main.py` (+ `seed.py`) |
| App has a real, coherent use case | Real domain (Aaron Recompile's Bitcoin Script writing), real seed data, no placeholder text |

---

## 6. Sample data

The seed script [`seed.py`](https://github.com/mingjing-zhang/project-2-api/blob/main/seed.py) loads **3 series and 19 articles** — all real published essays:

- **Series 1: "Not Just HODLing — Real Bitcoin Script Engineering"** — 4 articles, positioned #1–#4 (CSV+P2SH → Bitcoinutils → 4-leaf Taproot tree → Control block deep analysis)
- **Series 2: "OP_* on Signet — Bitcoin Inquisition"** — 6 articles, positioned #1–#6 (OP_CAT → OP_CSFS → OP_CTV → OP_INTERNALKEY+CSFS → OP_CAT+CSFS → SIGHASH_ANYPREVOUT)
- **Series 3: "Mastering Taproot"** — 1 article (P2SH 2-of-3 multisig chapter)
- **8 standalone articles** (no series): Bitcoin Doesn't Use Encryption, Why V3 Matters, RootScope, The Missing Developer Stack of Taproot, Commit-Reveal vs Dual-Layer Scripts, etc.

The seed is **idempotent** — running it twice does not duplicate data.

---

## 7. Screenshots (lab submission item 4)

See [`screenshots/`](https://github.com/mingjing-zhang/project-2-api/tree/main/screenshots) for:
- A page listing records (e.g., `/series` or `/articles`)
- The create form filled out (`/articles/new`)
