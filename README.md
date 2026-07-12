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
Approving a CSR participation triggers a signal that awards XP to the user's profile. A follow-up signal checks the new XP total against `BadgeUnlockRule` thresholds and auto-awards badges via a many-to-many relationship. Users redeem XP in a Rewards Store, which decrements the reward's stock.

## 4. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.1x, Django 5.x (ORM, Signals, Class-Based Views) |
| Frontend | Django Templates + Bootstrap 5 + Chart.js |
| Database | PostgreSQL (production) / SQLite3 (local development) |
| REST layer | Django REST Framework |

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
├── apps/                        # every domain app is versioned
│   └── core/
│       └── v1/                  # apps.core.v1  (label: core_v1)
│           ├── models.py
│           ├── views.py
│           ├── urls.py
│           ├── serializers.py
│           ├── admin.py
│           ├── apps.py
│           ├── migrations/
│           └── tests/
│
├── templates/
│   ├── layout/                  # base/master layouts
│   ├── include/                 # reusable partials (navbar, footer, ...)
│   └── core/v1/                 # per-app, per-version templates
│
├── static/{css,js,img}/
└── media/
```

**Planned domain apps** (following the same `apps/<name>/v1/` pattern): ERP mock data (`FleetLog`, `PurchaseOrder`, `ExpenseRecord`), ESG metrics (`EmissionFactor`, `CarbonTransaction`), Social/CSR (`Challenge`, `EmployeeParticipation`), Governance (`Audit`, `ComplianceIssue`), and Gamification (`BadgeUnlockRule`, `Reward`) — each with its own `models.py`, `views.py`, `signals.py`, and `tests/`.

## 6. Getting Started

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then fill in SECRET_KEY, DATABASE_URL, etc.

python manage.py migrate
python manage.py runserver
```

By default `manage.py` runs against `config.settings.development`. Override with the `DJANGO_SETTINGS_MODULE` environment variable to point at `config.settings.production` when deploying.

## 7. Hackathon Execution Timeline

| Hours | Focus |
|---|---|
| 1–2 | Foundation — project setup, modular directory structure, base models, initial commit |
| 3–5 | Core engine — Mock ERP models, `EmissionFactor`, and `signals.py` carbon-automation logic |
| 6–8 | Data collection — Social & Governance models/forms, file-upload validation, compliance due dates |
| 9–11 | Gamification — XP logic, auto-badge signals, reward redemption |
| 12+ | UI & polish — Bootstrap 5 templates, Chart.js dashboards, CSV/PDF export |

---

Built for the Odoo Hackathon '26.
