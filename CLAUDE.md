# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication

- Reply to the user in **Thai**. Code identifiers, file paths and commands stay as they are.
- Commit/PR messages in this repo are usually Thai, often prefixed with an issue number, e.g. `feat(#106): ...`, `fix(#91): ...`.

## Environment (Windows dev machine)

- Python **3.9** venv at `venv/` — pinned packages (mysqlclient 2.0.3, pandas 1.5.2, Django 4.2) have no wheels for newer Python. Call it directly: `./venv/Scripts/python.exe`.
- MySQL 8 runs locally on **port 13306** (root, empty password). The working database is set in `.env` / local `weight/settings.py` (currently `djangoweightdb3`).
- Console is cp1252: set `PYTHONIOENCODING=utf-8` (and `PYTHONUTF8=1` for tools reading Thai files) when running Python that prints or reads Thai.
- `weightapp/views.py`, templates and most source files use **CRLF** and contain Thai text. When patching with scripts, normalize `\r\n` before matching and restore it on write. Bash heredocs can mangle `\\` and Thai — write patch scripts to a file instead.

## Commands

```bash
# run the dev server
./venv/Scripts/python.exe manage.py runserver

# system check / missing migrations
./venv/Scripts/python.exe manage.py check
./venv/Scripts/python.exe manage.py makemigrations --check --dry-run

# tests — ALWAYS use weight.settings_ci (it drops the read-only Express Postgres alias `pg_db`;
# plain weight.settings would try to create a test database on the real Express server)
DJANGO_SETTINGS_MODULE=weight.settings_ci DB_NAME=djangoweightdb3 DB_PORT=13306 DB_PASSWORD= PYTHONIOENCODING=utf-8 \
  ./venv/Scripts/python.exe manage.py test weightapp --noinput

# a single test module / class / method
DJANGO_SETTINGS_MODULE=weight.settings_ci DB_NAME=djangoweightdb3 DB_PORT=13306 DB_PASSWORD= PYTHONIOENCODING=utf-8 \
  ./venv/Scripts/python.exe manage.py test weightapp.tests_export_document_case.ExportDocumentCaseTests.test_which_tickets_stay --noinput
```

- Known pre-existing failure: `weightapp.tests.UCWeightDeliveryTests.test_uc_weight_delivery_update_allowed_when_limit_reached` (500 != 200). Not caused by recent work.
- View tests that render templates need `@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')` (whitenoise manifest is not collected locally).
- Logged-in page tests need a `UserProfile` for the user and `session['company_code']`; without them views redirect to logout.
- CI (`.github/workflows/`): `django-checks.yml` (install, migrate on empty MySQL, `check`, `makemigrations --check` — no tests) and `security-checks.yml` (gitleaks, bandit vs `.github/bandit-baseline.json`, CodeQL, pip-audit, `check --deploy`). Both use `weight.settings_ci`.

## Git / data rules

- **Never commit `weight/settings.py`** — the local copy differs (DB name/port). Never commit `.env` (DB/email credentials) or `docs/`.
- Don't put credentials in `weight/settings.py` — they go in `.env` (keys listed in `.env.example`). The repo is public.
- Scripts run with `weight.settings` hit the **real** local database. Never mass-delete or bulk-update data from scripts; read-only checks only unless the user asks.
- The production/deploy database is separate from local. Data entered in local admin (map rows, aliases, permissions, freight rates) does **not** travel with the code; it must be re-entered on deploy. Don't move it with the admin import/export buttons — row ids differ between databases.

## Architecture

Single Django project `weight/` with one app `weightapp/`. Most logic lives in a few very large modules:
`views.py` (~14k lines: HTML pages, DRF APIs, Excel exports), `models.py`, `serializers.py`, `forms.py`, `admin.py`. Newer features are split into their own modules (`views_company_map.py`, `xlsx_template.py`).

**Databases** — `default` is MySQL. `pg_db` is the Express accounting system (Postgres), **read-only**, models declared `managed = False` (`ExOEINVH`, `ExOEINVD`, …); used only to pull fuel bills for the export report, and code falls back to daily average prices when it can't connect.

**Scale clients** (desktop weighing programs) talk to the server through DRF endpoints under `*/api/*` (JWT via `rest_framework_simplejwt`, see `tokens.py`). Each ticket is a `Weight` row; `bws` = the weighing station (`BaseWeightStation`, owned by a `BaseCompany`).

**Multi-company tabs** — the logged-in user picks a company tab; `request.session['company_code']` scopes most pages. Login silently bounces to logout unless the user has a `UserProfile` (company + visible tabs). `context_processors.py` builds the visible tabs.

**Import-time side effects** (matter for scripts/CI):
- `forms.py` queries `BaseLossType` at import, so anything that loads `urls.py` needs migrated tables (`migrate --skip-checks` first on an empty DB).
- `views.py` starts an APScheduler `BackgroundScheduler` at import.

**Weight field naming trap** — `weight_total` is the weight measured by *that* ticket's scale, `origin_weight` is the other side; 0 means "not weighed". On mine tickets `weight_total` = origin weight; on port tickets it's the destination weight.

### Export freight report (`/exportDocument/`) and freight rates (`/internationalFreightRate/`)

The main area of recent work. Key pieces in `views.py` (functions prefixed `_exportDocument*` / `_ifr*`):

- **Scope** (`_exportDocumentBaseQuerySet`, shared by the page, the Excel export and the weight-table "incomplete" panel): tickets from our own port scales (case 1) **or** mine sell scales to customers flagged `is_export_destination` in `BaseCompanyMapBaseCustomer` (case 2); carry type `ส่งให้` **or empty** (`_exportDocumentCarryQ`; empty ones are highlighted for review, `รับเอง` excluded); sites `200PL`/`300PL` excluded.
- **Duplicate tickets**: a trip into our own port has two tickets (mine + port). The port ticket is kept; mine tickets to our port are dropped from the port's scale go-live date (first ticket date, cached 1h). Port→port tickets are dropped.
- **Map table** `base_company_map_base_customer` names origins/destinations and holds the export/domestic flags; `BaseCompanyMapCustomerAlias` lets one map row own extra customer codes (alias follows the parent row's flags). Managed in admin and at `/internationalFreightRate/destinations/` (`views_company_map.py`, needs `change_basecompanymapbasecustomer` permission).
- **Freight rates** (`InternationalFreightRate` + `InternationalFreightRateTeam`) are versioned per route with approval; team rows hold per-weight-band freight, fuel adjustment per 1 baht/litre, and contract values. The create/edit page (`viewInternationalFreightRateCreate.html`) computes freight from contract values in JS only; the server never recalculates it on save.
- **Excel output** is filled into templates in `weightapp/exceltemplate/` (current trip report: `trip_report_template_v15.xlsx`, path in `xlsx_template.TRIP_REPORT_TEMPLATE`). The workbook is formula-driven; Python only writes raw data. Save with `xlsx_template.save_with_template_extensions` — plain openpyxl drops the x14 dropdowns. Column positions of the rate sheet are the `EXPORT_DOC_RATE_*_COL` constants and must match the template; to insert columns, edit the template in real Excel (it shifts ~2,700 cross-sheet formulas), never with openpyxl.

## Admin

`ImportExportModelAdmin` is used widely. Exporting the whole `weight` table (~1M rows) times out — filter first (`WeightAdmin` has a date-range filter, or `?date__gte=…&date__lte=…`), and prefer CSV.
