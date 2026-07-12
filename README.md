# EcoSphere — Enterprise ESG Management Platform

> Built for the **Odoo Hackathon '26**

EcoSphere is a unified, automated, and gamified ESG (Environmental, Social, Governance) management platform built on a Django MVT architecture. It simulates an ERP data source and uses event-driven automation to turn routine operational records into real-time ESG insight — without requiring manual data entry from sustainability officers.

---

## 1. The Problem

Organizations face growing regulatory and social pressure to track and improve their ESG metrics, but are bottlenecked by legacy, manual processes:

- **Disconnected data silos** — ERP systems capture operational data (fleet fuel use, manufacturing output, procurement) while ESG reporting is done manually in spreadsheets, causing duplication and human error.
- **Lack of real-time visibility** — Leadership can't see live carbon footprint or compliance status; reporting is typically quarterly/annual, blocking proactive decisions.
- **Low employee engagement** — CSR initiatives fail without visibility or incentives for participation.
- **Manual compliance tracking** — Governance audits and violations are tracked by hand, so deadlines are missed and regulatory risk goes unmanaged.

## 2. Our Solution

EcoSphere addresses these gaps with:

- **Mock ERP integration layer** — a dedicated set of models (`FleetLog`, `PurchaseOrder`, `ExpenseRecord`) that simulate an existing ERP, proving the platform can hook into real business operations.
- **Event-driven automation (Django Signals)** — `post_save` signals intercept new ERP records, calculate environmental impact automatically, and generate the corresponding ESG record. No manual carbon-data entry required.
- **Versioned, modular app structure** — business logic is organized per app under a `v1/` namespace (e.g. `apps/core/v1/`) to avoid a "fat models.py" anti-pattern and keep the codebase enterprise-ready and scalable.

## 3. Core Modules

### 🌱 Environmental — Carbon Accounting & Metrics
Admins define dynamic `EmissionFactor` records (e.g. 1L Diesel = 2.68 kg CO2e). When a `FleetLog` entry is submitted (e.g. 50L diesel), a signal automatically fetches the active factor, computes the impact (`50 × 2.68 = 134 kg CO2e`), and creates a `CarbonTransaction` tied to the originating department — with zero manual entry.

### 🤝 Social — CSR & Workforce Engagement
Employees browse active CSR challenges (e.g. "Plant a Tree", "Cycle to Work") and submit an `EmployeeParticipation` record with mandatory evidence (image/PDF via `FileField`). Records stay `Pending` until a manager reviews and approves them.

### ⚖️ Governance — Policy & Compliance Tracking
Governance officers log `ComplianceIssue` records against audits, each with an `owner` and `due_date`. A custom manager/middleware flags any issue where `current_date > due_date` as **Overdue**, surfacing it on the executive dashboard.

### 🎮 Gamification — The Engagement Engine
Approving a CSR participation *or a Challenge participation* triggers a signal that awards XP to the user's profile. A follow-up signal checks the new XP total against `BadgeUnlockRule` thresholds and auto-awards badges via a many-to-many relationship. Users redeem XP in a Rewards Store, which decrements the reward's stock. Employee and department leaderboards (`apps/engagement/v1/leaderboard.py`) rank participants by XP and ESG performance.

### 📊 ESG Scoring Engine
`apps/environmental/v1/scoring.py` turns raw operational data into comparable 0–100 scores. Each department gets an **Environmental** (goal achievement + relative emission performance), **Social** (approved CSR/Challenge participation rate), and **Governance** (policy-acknowledgement rate + compliance health) score. These roll up into a **Department Total** using configurable weights on `GlobalConfiguration` (default E 40 / S 30 / G 30), and finally into an **Overall ESG Score** (mean of department totals). Snapshots are persisted per reporting year in `DepartmentScore` for trend charts.

### 📈 Reporting & Export
`apps/reporting/v1` builds Environmental, Social, Governance, and ESG Summary reports through a single `build_report(type, filters)` entry point (the Custom Report Builder), with filters for department, date range, module, employee, challenge, and ESG category. Any report exports to **CSV, XLSX (openpyxl), or PDF (reportlab)** via `exporters.export_report(result, fmt)`. Report definitions can be saved as `SavedReport` rows.

### 🔔 Automation & Maintenance
Signals raise in-app notifications for new/overdue compliance issues, CSR/Challenge approval decisions, and badge unlocks. The `run_esg_maintenance` management command (cron/scheduler friendly) recomputes all scores, flags overdue issues, and enrols + reminds employees on pending policy acknowledgements.

## 4. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.1x, Django 5.x (ORM, Signals, Class-Based Views) |
| Frontend | Django Templates + **Tailwind CSS** (utility-only, no custom CSS) + vanilla-JS AJAX against the JWT API |
| Database | **PostgreSQL** (required — row-level security) |
| REST layer | Django REST Framework + JWT (SimpleJWT) |
| Access control | RBAC + PostgreSQL **row-level security** (see [docs/rls.md](docs/rls.md)) |

## 5. Project Structure

The codebase is split into versioned Django apps and a `config/` settings package so multiple contributors can work on separate modules without merge conflicts, and settings never leak across environments:

```
odoo-ecosphere-esg/
├── manage.py
├── requirements.txt
├── .env.example
│
├── config/                     # project settings package (replaces settings.py)
│   ├── settings/
│   │   ├── base.py             # shared settings
│   │   ├── development.py      # local/dev overrides
│   │   └── production.py       # security hardening, prod overrides
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                        # every domain app is versioned under v1/
│   ├── core/v1/                 # shared kernel: base models, enums, managers,
│   │                            #   ActivityLog + audit middleware, permissions
│   ├── accounts/v1/             # custom User + JWT auth + role permissions
│   ├── system_core/v1/          # GlobalConfiguration singleton (feature flags)
│   ├── environmental/v1/        # Department, EmissionFactor, CarbonTransaction,
│   │                            #   SustainabilityGoal + emission service
│   ├── fleet_ops/v1/            # Vehicle, FleetLog        (ERP mock + signal)
│   ├── procurement/v1/          # Vendor, PurchaseOrder    (ERP mock + signal)
│   ├── manufacturing/v1/        # ProductionOrder, ResourceUsage (ERP + signal)
│   ├── social_impact/v1/        # CSRActivity, EmployeeParticipation (evidence)
│   ├── compliance/v1/           # ESGPolicy, Audit, ComplianceIssue (overdue)
│   ├── engagement/v1/           # EmployeeProfile, Challenge, Badge, Reward, ...
│   └── notifications/v1/        # Notification (automated alerts)
│                                # each app/v1: models, admin, apps, signals,
│                                #   services, migrations/, tests/
│
├── templates/
│   ├── layout/                  # base/master layouts
│   ├── include/                 # reusable partials (navbar, footer, ...)
│   └── core/v1/                 # per-app, per-version templates
│
├── static/{css,js,img}/
└── media/
```

### Apps at a glance

| App | Category | Key models | Automation |
|---|---|---|---|
| `system_core` | Config | `GlobalConfiguration` | Org-wide feature flags |
| `fleet_ops` | ERP mock | `Vehicle`, `FleetLog` | FleetLog save → CO2e |
| `procurement` | ERP mock | `Vendor`, `PurchaseOrder` | PO save → CO2e |
| `manufacturing` | ERP mock | `ProductionOrder`, `ResourceUsage` | Usage save → CO2e + waste |
| `environmental` | ESG (E) | `Department`, `EmissionFactor`, `CarbonTransaction`, `SustainabilityGoal` | Central emission service |
| `social_impact` | ESG (S) | `CSRActivity`, `EmployeeParticipation` | Approval → XP award |
| `compliance` | ESG (G) | `ESGPolicy`, `Audit`, `ComplianceIssue` | Overdue detection + alerts |
| `engagement` | Gamification | `EmployeeProfile`, `Challenge`, `Badge`, `BadgeUnlockRule`, `Reward`, `RewardRedemption` | XP → auto badges, reward redemption |
| `accounts` | Auth | custom `User` (roles) | Auto-creates gamification profile |
| `notifications` | Alerts | `Notification` | Written by signals/commands |

### Security & architecture notes

- **Database row-level security (RLS)** — PostgreSQL policies filter every query by the requesting user's role and department, so a user only ever sees rows they're permitted to (full matrix + design in [docs/rls.md](docs/rls.md)). Enforced by the DB, not just the ORM — a forgotten `.filter()` can't leak data. Apply with `manage.py setup_rls`.
- **JWT auth** (`djangorestframework-simplejwt`) with **refresh-token rotation + blacklist** — a leaked refresh token has a short useful life. Role is embedded in the token so the frontend can gate UI without an extra round-trip.
- **Role-based permissions** (`apps/core/v1/permissions.py`) — `IsAdmin`, `IsManager`, `IsGovernanceOfficer`, `IsOwnerOrReadOnly`.
- **Audit trail** — `ActivityLogMiddleware` persists every mutating API request (who / what / when / IP) for governance.
- **Emission logic lives in one service** (`environmental/v1/services.py`); every ERP signal calls it, so the carbon maths is never duplicated.
- **Overdue compliance** is a live queryset/property (`ComplianceIssue.objects.overdue()`, `issue.is_overdue`) plus a `flag_overdue_issues` management command for scheduled alerts — cheaper and more correct than a per-request middleware.
- **Rate limiting** and **pagination** enabled globally in DRF.

## 6. API Overview

All endpoints are namespaced under `/api/v1/`. Authentication is JWT (`Authorization: Bearer <access>`).

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register/` | Create an account |
| POST | `/api/v1/auth/login/` | Obtain access + refresh tokens |
| POST | `/api/v1/auth/refresh/` | Rotate access token |
| POST | `/api/v1/auth/logout/` | Blacklist a refresh token |
| GET/PATCH | `/api/v1/me/` | Current user's profile |

Module & data endpoints (all RLS-scoped, JWT-authenticated):

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/dashboard/summary/` | Executive dashboard aggregates (scores, trend, ranking, counts) |
| GET | `/api/v1/environmental/{emission-factors,carbon,goals}/` | Environmental tables |
| GET | `/api/v1/catalog/{departments,products,categories}/` | Master data |
| GET/POST | `/api/v1/social/participation/` | Participation queue; POST = submit evidence (multipart) |
| POST | `/api/v1/social/participation/{id}/{approve,reject}/` | Manager review (approve awards XP) |
| GET | `/api/v1/governance/{policies,acknowledgements,audits,issues}/` | Governance tables |
| POST | `/api/v1/governance/acknowledgements/{id}/acknowledge/` | Acknowledge a policy |
| GET | `/api/v1/gamification/{challenges,badges,rewards,leaderboard}/` | Gamification data |
| POST | `/api/v1/gamification/rewards/{id}/redeem/` | Redeem a reward (deducts XP + stock) |
| GET | `/api/v1/reports/export/?type=ESG_SUMMARY&fmt=pdf` | Export CSV / XLSX / PDF |
| GET/POST | `/api/v1/notifications/` · `.../unread_count/` · `.../read_all/` | Notification bell |

## 7. Getting Started (local setup)

### Prerequisites
- **Python 3.11+**
- **PostgreSQL 16** (or Docker) — required; row-level security depends on it.

### Step 1 — Virtual environment & dependencies
```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Start PostgreSQL and create the role + database
The app connects as a **non-superuser** role (`ecosphere_app`, `NOSUPERUSER NOBYPASSRLS`) so RLS is actually enforced. [`scripts/db/init.sql`](scripts/db/init.sql) creates that role and the `ecosphere` database.

**Option A — Docker (recommended):**
```bash
docker compose up -d db             # runs scripts/db/init.sql automatically on first boot
```
> If port 5432 is already taken (e.g. a native Postgres), edit the port mapping in `docker-compose.yml` to `"5433:5432"` and set `DB_PORT=5433` in `.env` (Step 3).

**Option B — An existing PostgreSQL** (run once as a superuser):
```bash
psql -U postgres -f scripts/db/init.sql
```

### Step 3 — Environment file
```bash
cp .env.example .env
```
Then set at least `SECRET_KEY` and the `DB_*` values (the defaults already match `scripts/db/init.sql`):
```dotenv
SECRET_KEY=change-me                # generate: python -c "import secrets; print(secrets.token_urlsafe(50))"
DB_NAME=ecosphere
DB_USER=ecosphere_app
DB_PASSWORD=ecosphere
DB_HOST=localhost
DB_PORT=5432                        # use 5433 if Docker maps to 5433
```

### Step 4 — Migrate, apply RLS, create an admin
```bash
python manage.py migrate            # create the schema
python manage.py setup_rls          # apply row-level-security policies (required)
python manage.py createsuperuser    # your first login (admin)
python manage.py seed_demo          # optional: populate demo data (users, ERP, ESG, gamification)
```
> Every screen reads its data from the RLS-scoped APIs — nothing is hard-coded in
> the templates or JS. `seed_demo` (idempotent) puts realistic demo data in the
> database so the dashboards, tables, and reports have something to show. Demo
> logins it creates use the password `Demo!2345` (e.g. `demo`, a Manager).
> `setup_rls` is what turns on the security model. Skip it and the tables have no policies; re-run it after any model/registry change. Preview with `--dry-run`, remove with `--drop`.

### Step 5 — Run
```bash
python manage.py runserver
```
- **App** → http://localhost:8000/ (redirects to the login page)
- **Django admin** → http://localhost:8000/admin/
- **API root** → http://localhost:8000/api/v1/

By default `manage.py` uses `config.settings.development`. Set `DJANGO_SETTINGS_MODULE=config.settings.production` when deploying.

### Creating login users
- **Self sign-up** — open `/register/` (or `POST /api/v1/auth/register/`); new users get the **EMPLOYEE** role.
- **Admin** — `python manage.py createsuperuser`.
- **A specific role + department** — use the shell (wrap in `rls_admin()` so the department is visible under RLS):
  ```python
  # python manage.py shell
  from django.contrib.auth import get_user_model
  from apps.core.v1.rls.context import rls_admin
  from apps.environmental.v1.models import Department
  User = get_user_model()
  with rls_admin():
      dept, _ = Department.objects.get_or_create(code="OPS", defaults={"name": "Operations"})
      User.objects.create_user("manoj", email="manoj@x.com", password="Str0ng!2345",
                               role="MANAGER", department=dept)
  ```
  Roles: `ADMIN`, `MANAGER`, `GOVERNANCE_OFFICER`, `EMPLOYEE` — they drive what each user can see via RLS.

### Handy management commands
```bash
python manage.py seed_demo                   # populate/refresh demo data (idempotent)
python manage.py setup_rls --dry-run        # preview the RLS SQL (no DB writes)
python manage.py run_esg_maintenance        # recompute scores, flag overdue issues, policy reminders
python manage.py flag_overdue_issues        # notify owners of overdue compliance issues
python manage.py shell < scripts/verify_rls.py   # prove RLS scoping end-to-end
python manage.py test                       # run the test suite
```

## 8. Hackathon Execution Timeline

| Hours | Focus |
|---|---|
| 1–2 | Foundation — project setup, modular directory structure, base models, initial commit |
| 3–5 | Core engine — Mock ERP models, `EmissionFactor`, and `signals.py` carbon-automation logic |
| 6–8 | Data collection — Social & Governance models/forms, file-upload validation, compliance due dates |
| 9–11 | Gamification — XP logic, auto-badge signals, reward redemption |
| 12+ | UI & polish — Tailwind templates, Chart.js dashboards, CSV/PDF export |

---

Built for the Odoo Hackathon '26.
