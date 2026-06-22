### Task 8: Mobile-First Apple-Style UI

**Files:**
- Modify: `attendance/static/attendance/css/style.css`

No automated tests — verify visually in the browser.

- [ ] **Step 1: Replace style.css with full stylesheet**

Replace `attendance/static/attendance/css/style.css` entirely:

```css
/* ===== Reset & Variables ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --blue:   #007AFF;
  --green:  #34C759;
  --red:    #FF3B30;
  --bg:     #F2F2F7;
  --surface:#FFFFFF;
  --surface2:#F9F9FB;
  --text:   #1C1C1E;
  --text2:  #6E6E73;
  --border: rgba(60,60,67,0.12);
  --shadow: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
  --r:      12px;
  --r-sm:   8px;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 16px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

/* ===== Header ===== */
.app-header {
  background: rgba(255,255,255,0.85);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 52px;
}

.app-title {
  font-size: 17px; font-weight: 600;
  position: absolute; left: 50%; transform: translateX(-50%);
  white-space: nowrap;
}

.header-back, .header-logout, .header-right-placeholder {
  font-size: 15px; color: var(--blue); text-decoration: none;
  min-width: 60px;
}

.header-right-placeholder { text-align: right; }

/* ===== Layout ===== */
.page-container {
  max-width: 640px; margin: 0 auto; padding: 20px 16px 64px;
}

.section-title {
  font-size: 12px; font-weight: 600; color: var(--text2);
  text-transform: uppercase; letter-spacing: 0.06em;
  margin: 24px 0 8px;
}

.empty-state {
  text-align: center; color: var(--text2);
  padding: 56px 24px; font-size: 15px; line-height: 1.6;
}

/* ===== Auth ===== */
.auth-card {
  max-width: 380px; margin: 48px auto;
  background: var(--surface); border-radius: var(--r);
  box-shadow: var(--shadow); padding: 32px 28px;
}

.auth-title { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
.auth-subtitle { color: var(--text2); margin-bottom: 28px; font-size: 15px; }

/* ===== Forms ===== */
.form-field { margin-bottom: 16px; }

.form-field label {
  display: block; font-size: 13px; font-weight: 500;
  color: var(--text2); margin-bottom: 6px;
}

.form-field select,
.form-field input[type="text"],
.form-field input[type="password"],
.form-input,
input[type="date"] {
  width: 100%; padding: 12px 14px;
  border: 1.5px solid var(--border); border-radius: var(--r-sm);
  font-size: 16px; font-family: inherit;
  background: var(--surface2); color: var(--text);
  -webkit-appearance: none; appearance: none; outline: none;
  transition: border-color 0.15s;
}

.form-field select:focus,
.form-field input:focus,
.form-input:focus { border-color: var(--blue); }

textarea.form-input { resize: vertical; min-height: 72px; }

.form-error {
  background: rgba(255,59,48,0.08); color: var(--red);
  border-radius: var(--r-sm); padding: 10px 14px;
  margin-bottom: 16px; font-size: 14px;
}

/* ===== Buttons ===== */
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 13px 20px; border-radius: var(--r-sm);
  font-size: 16px; font-weight: 600; font-family: inherit;
  cursor: pointer; border: none; text-decoration: none;
  transition: opacity 0.15s, transform 0.1s;
  -webkit-tap-highlight-color: transparent;
  min-height: 44px;
}

.btn:active { opacity: 0.8; transform: scale(0.98); }
.btn-primary  { background: var(--blue);  color: #fff; width: 100%; margin-top: 8px; }
.btn-secondary{ background: var(--surface); color: var(--blue); border: 1.5px solid var(--border); }
.btn-ghost    { background: transparent;  color: var(--text2); }

/* ===== Meeting List ===== */
.meeting-list {
  list-style: none; background: var(--surface);
  border-radius: var(--r); box-shadow: var(--shadow); overflow: hidden;
  margin-bottom: 20px;
}

.meeting-card { border-bottom: 1px solid var(--border); }
.meeting-card:last-child { border-bottom: none; }

.meeting-link {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 18px; text-decoration: none; color: var(--text);
  min-height: 56px;
}

.meeting-link:active { background: var(--bg); }
.meeting-date { font-size: 16px; font-weight: 500; }
.meeting-count { font-size: 14px; color: var(--text2); }

.analytics-link {
  display: block; text-align: center; margin-top: 16px;
}

/* ===== Roster ===== */
.roster-list {
  list-style: none; background: var(--surface);
  border-radius: var(--r); box-shadow: var(--shadow); overflow: hidden;
  margin-bottom: 20px;
}

.roster-item { border-bottom: 1px solid var(--border); }
.roster-item:last-child { border-bottom: none; }

.roster-label {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 18px; cursor: pointer; min-height: 56px;
}

.member-name { font-size: 16px; }

.roster-checkbox {
  width: 24px; height: 24px; border-radius: 6px;
  border: 2px solid var(--border); appearance: none; -webkit-appearance: none;
  cursor: pointer; flex-shrink: 0; margin-left: 12px;
  background: var(--surface2); transition: background 0.15s, border-color 0.15s;
  position: relative;
}

.roster-checkbox:checked { background: var(--blue); border-color: var(--blue); }

.roster-checkbox:checked::after {
  content: ''; position: absolute;
  left: 6px; top: 2px;
  width: 5px; height: 10px;
  border: 2px solid #fff; border-top: none; border-left: none;
  transform: rotate(45deg);
}

.save-btn { margin-bottom: 12px; }
.add-visitor-btn { width: 100%; }

/* ===== Visitors ===== */
.visitors-title { margin-top: 28px; }

.visitor-list {
  list-style: none; background: var(--surface);
  border-radius: var(--r); box-shadow: var(--shadow); overflow: hidden;
  margin-bottom: 20px;
}

.visitor-item {
  display: flex; flex-direction: column;
  padding: 14px 18px; border-bottom: 1px solid var(--border);
}

.visitor-item:last-child { border-bottom: none; }
.visitor-name { font-size: 15px; font-weight: 500; }
.visitor-note { font-size: 13px; color: var(--text2); margin-top: 2px; }

/* ===== Modal ===== */
.modal-overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.4); z-index: 200;
  align-items: flex-end; justify-content: center;
}

.modal-overlay.open { display: flex; }

.modal-card {
  background: var(--surface);
  border-radius: var(--r) var(--r) 0 0;
  padding: 24px 20px 40px;
  width: 100%; max-width: 640px;
  box-shadow: 0 -4px 32px rgba(0,0,0,0.15);
}

.modal-title { font-size: 18px; font-weight: 600; margin-bottom: 20px; }

.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.modal-actions .btn { flex: 1; margin-top: 0; }

/* ===== Analytics ===== */
.range-presets { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }

.preset-btn {
  padding: 7px 14px; border-radius: 20px;
  border: 1.5px solid var(--border); background: var(--surface);
  font-size: 14px; font-weight: 500; color: var(--text2);
  cursor: pointer; transition: all 0.15s; min-height: 36px;
}

.preset-btn.active { background: var(--blue); border-color: var(--blue); color: #fff; }

.custom-range {
  display: flex; gap: 8px; align-items: center;
  margin-bottom: 16px; flex-wrap: wrap;
}

.custom-range.hidden { display: none; }
.date-input { flex: 1; min-width: 130px; }

.chart-section {
  background: var(--surface); border-radius: var(--r);
  box-shadow: var(--shadow); padding: 20px; margin-bottom: 20px;
}

.chart-title {
  font-size: 15px; font-weight: 600; margin-bottom: 16px;
  display: flex; align-items: center; gap: 8px;
}

.rate-badge {
  font-size: 12px; font-weight: 600; color: var(--green);
  background: rgba(52,199,89,0.12); padding: 2px 8px; border-radius: 10px;
}

/* ===== Alerts ===== */
.alert {
  padding: 12px 16px; border-radius: var(--r-sm);
  margin-bottom: 16px; font-size: 14px;
  background: rgba(0,122,255,0.08); color: var(--blue);
}

/* ===== Responsive ===== */
@media (max-width: 480px) {
  .auth-card { margin: 24px 16px; }
  .chart-section { padding: 14px; }
  .preset-btn { font-size: 13px; padding: 6px 12px; }
}
```

- [ ] **Step 2: Visually verify on desktop and mobile viewport**

```bash
python manage.py runserver
```

Open `http://localhost:8000`. Check these flows manually:

1. **Login page** — centered card, group dropdown, PIN input, "Sign In" button
2. **Meeting list** — card list with dates and counts, "View Analytics" link below
3. **Attendance page** — large custom checkboxes, "Save Attendance" button, "+ Add Visitor" button opens bottom sheet modal
4. **Visitor modal** — name + note fields, Cancel and Add buttons side by side
5. **Analytics page** — pill preset buttons (3 months active by default), line chart + horizontal bar chart render
6. In Chrome DevTools → toggle device toolbar → iPhone 14 Pro (393px): verify no horizontal scroll, checkboxes ≥ 44px touch target, charts fit width

- [ ] **Step 3: Commit**

```bash
git add attendance/static/
git commit -m "feat: add Apple-style mobile-first CSS"
```

---

