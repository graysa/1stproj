### Task 9: Deployment to Render

**Files:**
- Verify (no changes): `render.yaml`, `build.sh`, `caregroup/settings.py`

No automated tests — verify via Render dashboard and live URL.

- [ ] **Step 1: Run full test suite**

```bash
python manage.py test attendance -v 2
```

Expected: All tests pass. Fix any failures before proceeding.

- [ ] **Step 2: Verify render.yaml and build.sh are committed**

```bash
git status
```

Confirm `render.yaml` and `build.sh` are tracked (not in .gitignore).

- [ ] **Step 3: Push to GitHub**

```bash
git remote add origin <your-github-repo-url>
git push -u origin main
```

- [ ] **Step 4: Create Render web service**

1. Log into [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Render detects `render.yaml` — confirm:
   - Build command: `./build.sh`
   - Start command: `gunicorn caregroup.wsgi`
   - Disk: `caregroup-data` mounted at `/var/data/`, 1 GB
4. Under **Environment**, confirm these vars (add `SECRET_KEY` manually with a long random value):
   ```
   SECRET_KEY  = <run: python -c "import secrets; print(secrets.token_hex(50))">
   DEBUG       = False
   ALLOWED_HOSTS = .onrender.com
   DB_PATH     = /var/data/db.sqlite3
   ```
5. Click **Deploy**

- [ ] **Step 5: Create superuser via Render shell**

In Render dashboard → your service → **Shell**:

```bash
python manage.py createsuperuser
```

- [ ] **Step 6: Smoke test the live app**

1. Visit `https://<your-app>.onrender.com/admin/` — log in with superuser
2. Create a CareGroup with a name and PIN
3. Add 2–3 Members to that group
4. Create a MeetingDate for today
5. Visit `/login/` → sign in as the group
6. Open the meeting from the list → check off a member → save
7. Add a visitor via the modal
8. Visit `/analytics/` → confirm charts render with data
9. Push a trivial commit (e.g. add a blank line to README) → wait for Render to redeploy → confirm attendance data still shows

- [ ] **Step 7: Final commit**

```bash
git add .
git commit -m "chore: ready for production — smoke tested on Render"
git push
```
