# Care Group Attendance Tracker — Design Spec
**Date:** 2026-06-22  
**Status:** Approved

---

## Overview

A mobile-friendly Django web app for a church to track weekly care group attendance. Group leaders log in with a shared PIN, mark attendance for their group's roster, and view their group's attendance trends. An admin sees an overview across all groups. Deployed on Render's free tier using SQLite on a persistent disk.

---

## Data Model

### `CareGroup`
- `name` — group display name
- `meeting_day` — day of week (0=Monday … 6=Sunday)
- `meeting_time` — time of day (for display purposes)
- `pin` — hashed PIN (stored via Django's `make_password`)

### `Member`
- `name`
- `group` — FK to CareGroup
- `is_active` — bool; deactivating removes from roster without deleting history

### `MeetingDate`
- `group` — FK to CareGroup
- `date` — the specific calendar date of a meeting
- Created manually by admin or auto-generated based on `meeting_day`
- One row per scheduled meeting per group

### `AttendanceRecord`
- `meeting_date` — FK to MeetingDate
- `member` — FK to Member (nullable for system flexibility)
- `is_present` — bool
- Unique together: `(meeting_date, member)`

### `Visitor`
- `meeting_date` — FK to MeetingDate
- `name`
- `note` — optional free text (e.g. "friend of John", "first-time visitor")

**Notes:**
- Visitors are intentionally separate from Members — no risk of polluting the roster.
- `Member.is_active` preserves historical data when someone leaves the group.
- `MeetingDate` as a model (rather than derived calendar weeks) enables clean retroactive logging.

---

## Authentication & Session Flow

- **Login page** (`/login/`): group name dropdown + PIN field.
- On submit, PIN verified with Django's `check_password` against stored hash.
- On success, `group_id` written to Django session.
- **Session expires after 24 hours** of inactivity (`SESSION_COOKIE_AGE = 86400`).
- **Custom `group_login_required` decorator** checks session for `group_id`. Protected views derive the group from the session — leaders can only see/edit their own group's data regardless of URL.
- **Logout** (`/logout/`): flushes the session.
- **Admin login**: Django's standard `/admin/` superuser login.
- **Admin dashboard** (`/admin-dashboard/`): protected by `staff_required` (separate from group session).
- **PIN management**: admin-only via Django admin. No self-service PIN reset.

---

## Page Structure

### Public
| URL | Purpose |
|-----|---------|
| `/login/` | Group name dropdown + PIN entry |

### Leader views (group session required)
| URL | Purpose |
|-----|---------|
| `/` | Redirects to meeting list |
| `/meetings/` | List of all meeting dates for their group; tap to log/edit |
| `/meetings/<date>/` | Attendance checklist for that meeting; add visitor modal |
| `/analytics/` | Group attendance charts with date range controls |

### Admin views (staff required)
| URL | Purpose |
|-----|---------|
| `/admin/` | Django admin — manage groups, members, meeting dates, PINs |
| `/admin-dashboard/` | Cross-group analytics overview |

### UX / Mobile
- Attendance page: card-style list with large tap targets, checkboxes on the right.
- "Add visitor" opens an inline modal (name + note) without page navigation.
- Analytics charts stack vertically on narrow screens.
- Minimal navigation — top header with group name and logout link.

---

## Analytics

### Leader analytics (`/analytics/`)
- Attendance rate per member over selected period (bar or horizontal bar chart)
- Total attendance per meeting date (line chart showing trend)
- Date range presets: **1 month, 3 months (default), 6 months, 1 year**
- Custom date range picker (start + end date)

### Admin dashboard (`/admin-dashboard/`)
- Per-group total attendance per week (grouped line or bar chart)
- Comparative attendance rate across groups
- Same date range controls as leader analytics

**Implementation:** Chart.js via CDN. Django views return JSON data endpoints; charts render client-side.

---

## Deployment & Infrastructure

### Stack
- **Framework:** Django (latest stable)
- **Database:** SQLite on Render persistent disk
- **Static files:** WhiteNoise
- **Charts:** Chart.js via CDN
- **Hosting:** Render free tier (web service + 1 GB persistent disk)

### Project Structure
```
caregroup/
  attendance/
  static/
  templates/
manage.py
requirements.txt
render.yaml
build.sh
```

### Render Configuration (`render.yaml`)
Defines:
- Web service (Python, gunicorn)
- Persistent disk mounted at `/var/data/`
- Build command: `./build.sh`
- Start command: `gunicorn caregroup.wsgi`

### `build.sh`
```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

### Environment Variables (set in Render dashboard)
| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | Render-assigned domain |
| `DB_PATH` | `/var/data/db.sqlite3` |

### Deployment Flow
- Push to GitHub → Render auto-deploys via webhook
- `build.sh` runs on each deploy (collectstatic + migrate)
- SQLite file persists across deploys on the mounted disk

---

## Out of Scope
- Individual member accounts or self-service registration
- Push notifications or reminders
- Export to CSV/Excel (can be added later via Django admin)
- Multi-language support
- Postgres migration (revisit if storage needs grow significantly)
