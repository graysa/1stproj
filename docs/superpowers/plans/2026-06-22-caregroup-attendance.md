# Care Group Attendance Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a mobile-friendly Django web app for church care group attendance tracking, deployed on Render's free tier with SQLite on a persistent disk.

**Architecture:** Single Django app (`attendance`) with custom session-based group auth (no Django User model for leaders), function-based views, and Chart.js (CDN) for client-side analytics. SQLite lives on Render's persistent disk at a path set by `DB_PATH` env var.

**Tech Stack:** Python 3.12+, Django 5.1+, SQLite, WhiteNoise, gunicorn, Chart.js 4 (CDN)

## Global Constraints

- PINs stored hashed via Django's `make_password` / `check_password` — never plaintext
- `SESSION_COOKIE_AGE = 86400` (24 hours), `SESSION_SAVE_EVERY_REQUEST = True`
- SQLite path from `DB_PATH` env var, fallback to `BASE_DIR / db.sqlite3`
- `STATICFILES_STORAGE`: `StaticFilesStorage` when `DEBUG=True` (dev/tests), `CompressedManifestStaticFilesStorage` when `DEBUG=False` (Render)
- WhiteNoise serves static files — no separate CDN
- Mobile-first: minimum tap target 44px, cards with rounded corners and shadows
- Apple-style design: generous whitespace, `#007AFF` blue, `#34C759` green, `-apple-system` font stack
- Analytics default date range: 3 months (91 days)

---

### Task 1: Project Scaffolding

**Files:**
- Create: `caregroup/settings.py`
- Create: `caregroup/urls.py`
- Create: `caregroup/wsgi.py`
- Create: `attendance/__init__.py`
- Create: `attendance/apps.py`
- Create: `requirements.txt`
- Create: `render.yaml`
- Create: `build.sh`
- Create: `.gitignore`
- Create: `manage.py`

**Interfaces:**
- Produces: runnable Django project passing `python manage.py check`; `caregroup` project package; `attendance` app registered

- [ ] **Step 1: Initialize Django project and app**

```bash
pip install Django==5.1.* gunicorn==22.* whitenoise==6.*
django-admin startproject caregroup .
python manage.py startapp attendance
```

- [ ] **Step 2: Write requirements.txt**

```
Django==5.1.*
gunicorn==22.*
whitenoise==6.*
```

- [ ] **Step 3: Replace caregroup/settings.py**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost 127.0.0.1').split()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'attendance',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'caregroup.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'caregroup.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DB_PATH', str(BASE_DIR / 'db.sqlite3')),
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

- [ ] **Step 4: Replace caregroup/urls.py**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('attendance.urls')),
]
```

- [ ] **Step 5: Create attendance/urls.py (stub)**

```python
from django.urls import path

urlpatterns = []
```

- [ ] **Step 6: Write render.yaml**

```yaml
services:
  - type: web
    name: caregroup
    env: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn caregroup.wsgi"
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: ".onrender.com"
      - key: DB_PATH
        value: "/var/data/db.sqlite3"
    disk:
      name: caregroup-data
      mountPath: /var/data
      sizeGB: 1
```

- [ ] **Step 7: Write build.sh**

```bash
#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

Make executable:
```bash
chmod +x build.sh
```

- [ ] **Step 8: Create .gitignore**

```
__pycache__/
*.pyc
*.pyo
.env
db.sqlite3
staticfiles/
.DS_Store
```

- [ ] **Step 9: Verify project starts cleanly**

```bash
python manage.py migrate
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 10: Commit**

```bash
git init
git add .
git commit -m "feat: scaffold Django project with Render config"
```

---

### Task 2: Data Models + Django Admin

**Files:**
- Create: `attendance/models.py`
- Create: `attendance/admin.py`
- Create: `attendance/tests/__init__.py`
- Create: `attendance/tests/test_models.py`

**Interfaces:**
- Produces: `CareGroup` (with `.set_pin(raw)`, `.check_pin(raw)`), `Member`, `MeetingDate` (with `.attendance_count()`), `AttendanceRecord`, `Visitor` — all importable from `attendance.models`

- [ ] **Step 1: Write failing model tests**

Create `attendance/tests/__init__.py` (empty file).

Create `attendance/tests/test_models.py`:

```python
import datetime
from django.test import TestCase
from attendance.models import CareGroup, Member, MeetingDate, AttendanceRecord, Visitor


class CareGroupPINTest(TestCase):
    def setUp(self):
        self.group = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )

    def test_pin_is_stored_hashed(self):
        self.group.set_pin('1234')
        self.group.save()
        self.assertNotEqual(self.group.pin, '1234')

    def test_check_pin_correct(self):
        self.group.set_pin('1234')
        self.group.save()
        self.assertTrue(self.group.check_pin('1234'))

    def test_check_pin_wrong(self):
        self.group.set_pin('1234')
        self.group.save()
        self.assertFalse(self.group.check_pin('9999'))


class MemberModelTest(TestCase):
    def setUp(self):
        self.group = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )

    def test_member_is_active_by_default(self):
        member = Member.objects.create(name='John', group=self.group)
        self.assertTrue(member.is_active)

    def test_inactive_member_excluded_from_active_filter(self):
        Member.objects.create(name='Active', group=self.group)
        Member.objects.create(name='Inactive', group=self.group, is_active=False)
        self.assertEqual(
            Member.objects.filter(group=self.group, is_active=True).count(), 1
        )


class MeetingDateModelTest(TestCase):
    def setUp(self):
        self.group = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )
        self.member = Member.objects.create(name='John', group=self.group)
        self.meeting = MeetingDate.objects.create(
            group=self.group, date=datetime.date(2026, 1, 5)
        )

    def test_str_includes_date(self):
        self.assertIn('2026-01-05', str(self.meeting))

    def test_attendance_count_present_member_plus_visitor(self):
        AttendanceRecord.objects.create(
            meeting_date=self.meeting, member=self.member, is_present=True
        )
        Visitor.objects.create(meeting_date=self.meeting, name='Jane')
        self.assertEqual(self.meeting.attendance_count(), 2)

    def test_attendance_count_excludes_absent_members(self):
        AttendanceRecord.objects.create(
            meeting_date=self.meeting, member=self.member, is_present=False
        )
        self.assertEqual(self.meeting.attendance_count(), 0)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python manage.py test attendance.tests.test_models -v 2
```

Expected: `ImportError: cannot import name 'CareGroup' from 'attendance.models'`

- [ ] **Step 3: Write attendance/models.py**

```python
from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password


class CareGroup(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    name = models.CharField(max_length=100, unique=True)
    meeting_day = models.IntegerField(choices=DAY_CHOICES)
    meeting_time = models.TimeField()
    pin = models.CharField(max_length=128, blank=True)

    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)

    def check_pin(self, raw_pin):
        return django_check_password(raw_pin, self.pin)

    def __str__(self):
        return self.name


class Member(models.Model):
    name = models.CharField(max_length=100)
    group = models.ForeignKey(CareGroup, on_delete=models.CASCADE, related_name='members')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class MeetingDate(models.Model):
    group = models.ForeignKey(CareGroup, on_delete=models.CASCADE, related_name='meetings')
    date = models.DateField()

    class Meta:
        ordering = ['-date']
        unique_together = [('group', 'date')]

    def attendance_count(self):
        present = self.records.filter(is_present=True).count()
        visitors = self.visitors.count()
        return present + visitors

    def __str__(self):
        return f"{self.group.name} — {self.date}"


class AttendanceRecord(models.Model):
    meeting_date = models.ForeignKey(
        MeetingDate, on_delete=models.CASCADE, related_name='records'
    )
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='records')
    is_present = models.BooleanField(default=False)

    class Meta:
        unique_together = [('meeting_date', 'member')]

    def __str__(self):
        status = 'present' if self.is_present else 'absent'
        return f"{self.member.name} — {status}"


class Visitor(models.Model):
    meeting_date = models.ForeignKey(
        MeetingDate, on_delete=models.CASCADE, related_name='visitors'
    )
    name = models.CharField(max_length=100)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"Visitor: {self.name}"
```

- [ ] **Step 4: Create and run migrations**

```bash
python manage.py makemigrations attendance
python manage.py migrate
```

Expected: migrations created and applied without errors.

- [ ] **Step 5: Run tests — expect all to pass**

```bash
python manage.py test attendance.tests.test_models -v 2
```

Expected: `OK` — 7 tests.

- [ ] **Step 6: Write attendance/admin.py**

```python
from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from .models import CareGroup, Member, MeetingDate, AttendanceRecord, Visitor


class CareGroupAdminForm(forms.ModelForm):
    new_pin = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text='Leave blank to keep the existing PIN. Enter a value to set a new one.',
    )

    class Meta:
        model = CareGroup
        fields = ['name', 'meeting_day', 'meeting_time', 'new_pin']

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_pin = self.cleaned_data.get('new_pin')
        if raw_pin:
            instance.pin = make_password(raw_pin)
        if commit:
            instance.save()
        return instance


class MemberInline(admin.TabularInline):
    model = Member
    extra = 1
    fields = ['name', 'is_active']


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ['member', 'is_present']


class VisitorInline(admin.TabularInline):
    model = Visitor
    extra = 0
    fields = ['name', 'note']


@admin.register(CareGroup)
class CareGroupAdmin(admin.ModelAdmin):
    form = CareGroupAdminForm
    list_display = ['name', 'get_meeting_day_display', 'meeting_time']
    inlines = [MemberInline]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'is_active']
    list_filter = ['group', 'is_active']


@admin.register(MeetingDate)
class MeetingDateAdmin(admin.ModelAdmin):
    list_display = ['group', 'date', 'attendance_count']
    list_filter = ['group']
    date_hierarchy = 'date'
    inlines = [AttendanceRecordInline, VisitorInline]

    def attendance_count(self, obj):
        return obj.attendance_count()
    attendance_count.short_description = 'Present'


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['name', 'meeting_date', 'note']
    list_filter = ['meeting_date__group']
```

- [ ] **Step 7: Create superuser and manually verify Django admin**

```bash
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://localhost:8000/admin/` — confirm CareGroup appears with `new_pin` field, Members can be added inline, MeetingDate shows attendance count column.

- [ ] **Step 8: Commit**

```bash
git add attendance/models.py attendance/admin.py attendance/tests/ attendance/migrations/
git commit -m "feat: add data models, admin registration, and PIN hashing"
```

---

### Task 3: Auth — Login, Logout, Decorator

**Files:**
- Create: `attendance/decorators.py`
- Create: `attendance/forms.py`
- Create: `attendance/views/__init__.py`
- Create: `attendance/views/auth.py`
- Create: `templates/attendance/base.html`
- Create: `templates/attendance/login.html`
- Create: `attendance/static/attendance/css/style.css` (stub)
- Modify: `attendance/urls.py`
- Create: `attendance/tests/test_auth.py`

**Interfaces:**
- Produces: `group_login_required(view_func)` and `staff_required(view_func)` decorators from `attendance.decorators`; `login_view`, `logout_view` from `attendance.views.auth`; session key `'group_id'` (int, the CareGroup pk) written on successful login

- [ ] **Step 1: Write failing auth tests**

Create `attendance/tests/test_auth.py`:

```python
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from attendance.models import CareGroup


def make_group(name='Alpha'):
    group = CareGroup.objects.create(
        name=name, meeting_day=6, meeting_time=datetime.time(10, 0)
    )
    group.set_pin('1234')
    group.save()
    return group


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = make_group()

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_correct_pin_sets_session(self):
        self.client.post(reverse('login'), {'group_name': 'Alpha', 'pin': '1234'})
        self.assertEqual(self.client.session['group_id'], self.group.pk)

    def test_login_correct_pin_redirects(self):
        response = self.client.post(
            reverse('login'), {'group_name': 'Alpha', 'pin': '1234'}
        )
        self.assertEqual(response.status_code, 302)

    def test_login_wrong_pin_does_not_set_session(self):
        self.client.post(reverse('login'), {'group_name': 'Alpha', 'pin': '9999'})
        self.assertNotIn('group_id', self.client.session)

    def test_login_wrong_pin_returns_200(self):
        response = self.client.post(
            reverse('login'), {'group_name': 'Alpha', 'pin': '9999'}
        )
        self.assertEqual(response.status_code, 200)

    def test_login_nonexistent_group_does_not_set_session(self):
        self.client.post(reverse('login'), {'group_name': 'Ghost', 'pin': '1234'})
        self.assertNotIn('group_id', self.client.session)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = make_group()
        self.client.post(reverse('login'), {'group_name': 'Alpha', 'pin': '1234'})

    def test_logout_clears_session(self):
        self.client.get(reverse('logout'))
        self.assertNotIn('group_id', self.client.session)

    def test_logout_redirects_to_login(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python manage.py test attendance.tests.test_auth -v 2
```

Expected: `NoReverseMatch: Reverse for 'login' not found`

- [ ] **Step 3: Write attendance/decorators.py**

```python
from functools import wraps
from django.shortcuts import redirect


def group_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'group_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
```

- [ ] **Step 4: Write attendance/forms.py**

```python
from django import forms
from .models import CareGroup


class LoginForm(forms.Form):
    group_name = forms.ChoiceField(choices=[])
    pin = forms.CharField(widget=forms.PasswordInput, max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', '— Select your group —')] + [
            (g.name, g.name) for g in CareGroup.objects.order_by('name')
        ]
        self.fields['group_name'].choices = choices


class VisitorForm(forms.Form):
    name = forms.CharField(max_length=100, label='Visitor name')
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Note (optional)',
    )
```

- [ ] **Step 5: Create attendance/views/__init__.py (empty) and attendance/views/auth.py**

Create `attendance/views/__init__.py` as an empty file.

Create `attendance/views/auth.py`:

```python
from django.shortcuts import render, redirect
from attendance.forms import LoginForm
from attendance.models import CareGroup


def login_view(request):
    if 'group_id' in request.session:
        return redirect('meeting_list')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        group_name = form.cleaned_data['group_name']
        raw_pin = form.cleaned_data['pin']
        try:
            group = CareGroup.objects.get(name=group_name)
        except CareGroup.DoesNotExist:
            form.add_error(None, 'Invalid group or PIN.')
        else:
            if group.check_pin(raw_pin):
                request.session['group_id'] = group.pk
                return redirect('meeting_list')
            else:
                form.add_error(None, 'Invalid group or PIN.')

    return render(request, 'attendance/login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    return redirect('login')
```

- [ ] **Step 6: Create base template**

Create `templates/attendance/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Care Groups{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'attendance/css/style.css' %}">
</head>
<body>
  <header class="app-header">
    {% block header %}
    <span class="app-title">Care Groups</span>
    {% endblock %}
  </header>
  <main class="app-main">
    {% if messages %}
      {% for message in messages %}
        <div class="alert">{{ message }}</div>
      {% endfor %}
    {% endif %}
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

- [ ] **Step 7: Create login template**

Create `templates/attendance/login.html`:

```html
{% extends 'attendance/base.html' %}

{% block title %}Sign In — Care Groups{% endblock %}

{% block header %}
<span class="app-title">Care Groups</span>
{% endblock %}

{% block content %}
<div class="auth-card">
  <h1 class="auth-title">Welcome</h1>
  <p class="auth-subtitle">Sign in to your care group</p>
  <form method="post" class="auth-form">
    {% csrf_token %}
    {% if form.non_field_errors %}
      <div class="form-error">{{ form.non_field_errors }}</div>
    {% endif %}
    <div class="form-field">
      <label for="{{ form.group_name.id_for_label }}">Group</label>
      {{ form.group_name }}
    </div>
    <div class="form-field">
      <label for="{{ form.pin.id_for_label }}">PIN</label>
      {{ form.pin }}
    </div>
    <button type="submit" class="btn btn-primary">Sign In</button>
  </form>
</div>
{% endblock %}
```

- [ ] **Step 8: Create static CSS stub**

Create `attendance/static/attendance/css/style.css`:

```css
/* Full styles added in Task 8 */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  margin: 0;
  padding: 0;
  background: #F2F2F7;
}
```

- [ ] **Step 9: Wire up auth URLs**

Replace `attendance/urls.py`:

```python
from django.urls import path
from attendance.views.auth import login_view, logout_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
```

- [ ] **Step 10: Run auth tests**

```bash
python manage.py test attendance.tests.test_auth -v 2
```

Expected: `OK` — 8 tests. (The redirect tests check status 302 without following, so no `meeting_list` URL needed yet.)

- [ ] **Step 11: Commit**

```bash
git add attendance/ templates/
git commit -m "feat: add session-based group login, logout, and auth decorators"
```

---

### Task 4: Meeting List View

**Files:**
- Create: `attendance/views/meetings.py`
- Create: `templates/attendance/meeting_list.html`
- Modify: `attendance/urls.py`
- Create: `attendance/tests/test_meetings.py`

**Interfaces:**
- Consumes: `group_login_required` from `attendance.decorators`; `'group_id'` from `request.session`; `CareGroup`, `MeetingDate` from `attendance.models`
- Produces: URL name `meeting_list`; template context: `group` (CareGroup), `meetings` (QuerySet[MeetingDate] ordered by `-date`)

- [ ] **Step 1: Write failing tests**

Create `attendance/tests/test_meetings.py`:

```python
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from attendance.models import (
    CareGroup, Member, MeetingDate, AttendanceRecord, Visitor
)


def login_as(client, group, pin='0000'):
    group.set_pin(pin)
    group.save()
    client.post(reverse('login'), {'group_name': group.name, 'pin': pin})


class MeetingListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )
        self.other = CareGroup.objects.create(
            name='Beta', meeting_day=0, meeting_time=datetime.time(19, 0)
        )
        self.m1 = MeetingDate.objects.create(group=self.group, date=datetime.date(2026, 6, 15))
        self.m2 = MeetingDate.objects.create(group=self.group, date=datetime.date(2026, 6, 8))
        self.other_m = MeetingDate.objects.create(group=self.other, date=datetime.date(2026, 6, 15))
        login_as(self.client, self.group)

    def test_meeting_list_loads(self):
        response = self.client.get(reverse('meeting_list'))
        self.assertEqual(response.status_code, 200)

    def test_shows_own_meetings(self):
        response = self.client.get(reverse('meeting_list'))
        meetings = list(response.context['meetings'])
        self.assertIn(self.m1, meetings)
        self.assertIn(self.m2, meetings)

    def test_does_not_show_other_group_meetings(self):
        response = self.client.get(reverse('meeting_list'))
        self.assertNotIn(self.other_m, list(response.context['meetings']))

    def test_ordered_most_recent_first(self):
        response = self.client.get(reverse('meeting_list'))
        meetings = list(response.context['meetings'])
        self.assertEqual(meetings[0], self.m1)
        self.assertEqual(meetings[1], self.m2)

    def test_requires_login(self):
        self.client.get(reverse('logout'))
        response = self.client.get(reverse('meeting_list'))
        self.assertEqual(response.status_code, 302)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python manage.py test attendance.tests.test_meetings -v 2
```

Expected: `NoReverseMatch: Reverse for 'meeting_list' not found`

- [ ] **Step 3: Write attendance/views/meetings.py**

```python
import datetime as dt
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from attendance.decorators import group_login_required
from attendance.models import CareGroup, MeetingDate, Member, AttendanceRecord, Visitor
from attendance import forms as attendance_forms


@group_login_required
def meeting_list(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    meetings = MeetingDate.objects.filter(group=group).order_by('-date')
    return render(request, 'attendance/meeting_list.html', {
        'group': group,
        'meetings': meetings,
    })
```

- [ ] **Step 4: Create templates/attendance/meeting_list.html**

```html
{% extends 'attendance/base.html' %}

{% block title %}Meetings — {{ group.name }}{% endblock %}

{% block header %}
<a href="{% url 'logout' %}" class="header-logout">Sign out</a>
<span class="app-title">{{ group.name }}</span>
<a href="#" class="header-right-placeholder"></a>
{% endblock %}

{% block content %}
<div class="page-container">
  {% if meetings %}
    <ul class="meeting-list">
      {% for meeting in meetings %}
        <li class="meeting-card">
          <a href="{% url 'meeting_detail' meeting.date|date:'Y-m-d' %}" class="meeting-link">
            <span class="meeting-date">{{ meeting.date|date:"D, d M Y" }}</span>
            <span class="meeting-count">{{ meeting.attendance_count }} present</span>
          </a>
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p class="empty-state">No meetings recorded yet. Add meeting dates in the admin panel.</p>
  {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 5: Update attendance/urls.py**

```python
from django.urls import path
from attendance.views.auth import login_view, logout_view
from attendance.views.meetings import meeting_list

urlpatterns = [
    path('', meeting_list, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('meetings/', meeting_list, name='meeting_list'),
]
```

- [ ] **Step 6: Run all tests**

```bash
python manage.py test attendance -v 2
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add attendance/ templates/
git commit -m "feat: add meeting list view scoped to logged-in group"
```

---

### Task 5: Attendance Detail View (Checklist + Visitor)

**Files:**
- Modify: `attendance/views/meetings.py`
- Create: `templates/attendance/meeting_detail.html`
- Modify: `attendance/urls.py`
- Modify: `attendance/tests/test_meetings.py`

**Interfaces:**
- Consumes: `VisitorForm` from `attendance.forms`; `group_login_required`; `MeetingDate`, `Member`, `AttendanceRecord`, `Visitor` models
- Produces: URL names `meeting_detail` (takes `<str:date>` in `YYYY-MM-DD` format) and `add_visitor` (same date arg); template context for `meeting_detail`: `group`, `meeting`, `member_data` (list of `{'member': Member, 'is_present': bool}`), `visitors` (QuerySet), `visitor_form`

- [ ] **Step 1: Write failing tests**

Append to `attendance/tests/test_meetings.py`:

```python
class MeetingDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )
        self.member1 = Member.objects.create(name='Alice', group=self.group)
        self.member2 = Member.objects.create(name='Bob', group=self.group)
        self.inactive = Member.objects.create(
            name='Inactive', group=self.group, is_active=False
        )
        self.meeting = MeetingDate.objects.create(
            group=self.group, date=datetime.date(2026, 6, 15)
        )
        login_as(self.client, self.group)

    def test_detail_page_loads(self):
        response = self.client.get(reverse('meeting_detail', args=['2026-06-15']))
        self.assertEqual(response.status_code, 200)

    def test_shows_active_members_only(self):
        response = self.client.get(reverse('meeting_detail', args=['2026-06-15']))
        names = [item['member'].name for item in response.context['member_data']]
        self.assertIn('Alice', names)
        self.assertIn('Bob', names)
        self.assertNotIn('Inactive', names)

    def test_submit_saves_present_and_absent(self):
        self.client.post(reverse('meeting_detail', args=['2026-06-15']), {
            'action': 'save_attendance',
            'present_members': [self.member1.pk],
        })
        r1 = AttendanceRecord.objects.get(meeting_date=self.meeting, member=self.member1)
        r2 = AttendanceRecord.objects.get(meeting_date=self.meeting, member=self.member2)
        self.assertTrue(r1.is_present)
        self.assertFalse(r2.is_present)

    def test_submit_redirects_to_meeting_list(self):
        response = self.client.post(reverse('meeting_detail', args=['2026-06-15']), {
            'action': 'save_attendance',
            'present_members': [],
        })
        self.assertRedirects(response, reverse('meeting_list'))

    def test_cannot_access_other_groups_meeting(self):
        other = CareGroup.objects.create(
            name='Beta', meeting_day=0, meeting_time=datetime.time(19, 0)
        )
        MeetingDate.objects.create(group=other, date=datetime.date(2026, 6, 14))
        response = self.client.get(reverse('meeting_detail', args=['2026-06-14']))
        self.assertEqual(response.status_code, 404)


class AddVisitorViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )
        self.meeting = MeetingDate.objects.create(
            group=self.group, date=datetime.date(2026, 6, 15)
        )
        login_as(self.client, self.group)

    def test_add_visitor_creates_record(self):
        self.client.post(reverse('add_visitor', args=['2026-06-15']), {
            'name': 'Jane Visitor',
            'note': 'Friend of Alice',
        })
        self.assertTrue(
            Visitor.objects.filter(
                meeting_date=self.meeting, name='Jane Visitor'
            ).exists()
        )

    def test_add_visitor_redirects_back_to_detail(self):
        response = self.client.post(reverse('add_visitor', args=['2026-06-15']), {
            'name': 'Jane',
            'note': '',
        })
        self.assertRedirects(
            response, reverse('meeting_detail', args=['2026-06-15'])
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python manage.py test attendance.tests.test_meetings -v 2
```

Expected: `NoReverseMatch: Reverse for 'meeting_detail' not found`

- [ ] **Step 3: Append meeting_detail and add_visitor to attendance/views/meetings.py**

```python
@group_login_required
def meeting_detail(request, date):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    try:
        parsed_date = dt.date.fromisoformat(date)
    except ValueError:
        raise Http404

    meeting = get_object_or_404(MeetingDate, group=group, date=parsed_date)
    active_members = Member.objects.filter(group=group, is_active=True)
    existing = {r.member_id: r for r in AttendanceRecord.objects.filter(meeting_date=meeting)}

    if request.method == 'POST' and request.POST.get('action') == 'save_attendance':
        present_ids = set(int(pk) for pk in request.POST.getlist('present_members'))
        for member in active_members:
            AttendanceRecord.objects.update_or_create(
                meeting_date=meeting,
                member=member,
                defaults={'is_present': member.pk in present_ids},
            )
        return redirect('meeting_list')

    member_data = [
        {
            'member': m,
            'is_present': existing[m.pk].is_present if m.pk in existing else False,
        }
        for m in active_members
    ]

    return render(request, 'attendance/meeting_detail.html', {
        'group': group,
        'meeting': meeting,
        'member_data': member_data,
        'visitors': meeting.visitors.all(),
        'visitor_form': attendance_forms.VisitorForm(),
    })


@group_login_required
def add_visitor(request, date):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    try:
        parsed_date = dt.date.fromisoformat(date)
    except ValueError:
        raise Http404

    meeting = get_object_or_404(MeetingDate, group=group, date=parsed_date)

    if request.method == 'POST':
        form = attendance_forms.VisitorForm(request.POST)
        if form.is_valid():
            Visitor.objects.create(
                meeting_date=meeting,
                name=form.cleaned_data['name'],
                note=form.cleaned_data.get('note', ''),
            )
    return redirect('meeting_detail', date=date)
```

- [ ] **Step 4: Create templates/attendance/meeting_detail.html**

```html
{% extends 'attendance/base.html' %}

{% block title %}{{ meeting.date|date:"d M Y" }} — {{ group.name }}{% endblock %}

{% block header %}
<a href="{% url 'meeting_list' %}" class="header-back">‹ Meetings</a>
<span class="app-title">{{ meeting.date|date:"d M Y" }}</span>
<a href="{% url 'logout' %}" class="header-logout">Sign out</a>
{% endblock %}

{% block content %}
<div class="page-container">
  <form method="post">
    {% csrf_token %}
    <input type="hidden" name="action" value="save_attendance">

    <ul class="roster-list">
      {% for item in member_data %}
        <li class="roster-item">
          <label class="roster-label">
            <span class="member-name">{{ item.member.name }}</span>
            <input type="checkbox" name="present_members" value="{{ item.member.pk }}"
              class="roster-checkbox" {% if item.is_present %}checked{% endif %}>
          </label>
        </li>
      {% endfor %}
    </ul>

    <button type="submit" class="btn btn-primary save-btn">Save Attendance</button>
  </form>

  <button type="button" class="btn btn-secondary add-visitor-btn"
    onclick="document.getElementById('visitor-modal').classList.add('open')">
    + Add Visitor
  </button>

  {% if visitors %}
    <h3 class="section-title visitors-title">Visitors</h3>
    <ul class="visitor-list">
      {% for v in visitors %}
        <li class="visitor-item">
          <span class="visitor-name">{{ v.name }}</span>
          {% if v.note %}<span class="visitor-note">{{ v.note }}</span>{% endif %}
        </li>
      {% endfor %}
    </ul>
  {% endif %}
</div>

<div id="visitor-modal" class="modal-overlay">
  <div class="modal-card">
    <h3 class="modal-title">Add Visitor</h3>
    <form method="post" action="{% url 'add_visitor' meeting.date|date:'Y-m-d' %}">
      {% csrf_token %}
      <div class="form-field">
        <label>Name</label>
        <input type="text" name="name" class="form-input" required autocomplete="off">
      </div>
      <div class="form-field">
        <label>Note (optional)</label>
        <textarea name="note" class="form-input" rows="2"></textarea>
      </div>
      <div class="modal-actions">
        <button type="button" class="btn btn-ghost"
          onclick="document.getElementById('visitor-modal').classList.remove('open')">
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">Add</button>
      </div>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Update attendance/urls.py**

```python
from django.urls import path
from attendance.views.auth import login_view, logout_view
from attendance.views.meetings import meeting_list, meeting_detail, add_visitor

urlpatterns = [
    path('', meeting_list, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('meetings/', meeting_list, name='meeting_list'),
    path('meetings/<str:date>/', meeting_detail, name='meeting_detail'),
    path('meetings/<str:date>/visitor/', add_visitor, name='add_visitor'),
]
```

- [ ] **Step 6: Run all tests**

```bash
python manage.py test attendance -v 2
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add attendance/ templates/
git commit -m "feat: add attendance detail view with checklist and visitor modal"
```

---

### Task 6: Leader Analytics

**Files:**
- Create: `attendance/views/analytics.py`
- Create: `templates/attendance/analytics.html`
- Create: `attendance/static/attendance/js/charts.js`
- Modify: `attendance/urls.py`
- Modify: `templates/attendance/meeting_list.html` (add analytics link)
- Create: `attendance/tests/test_analytics.py`

**Interfaces:**
- Consumes: `group_login_required`; `AttendanceRecord`, `MeetingDate`, `Visitor`, `Member` models
- Produces: URL names `analytics` and `analytics_data`; `analytics_data` returns JSON: `{'weekly': {'labels': [str], 'totals': [int]}, 'member_rates': [{'name': str, 'rate': float, 'attended': int, 'total': int}], 'from_date': str, 'to_date': str}`; shared helpers `_default_date_range()` and `_parse_date_params(request)` used also by Task 7

- [ ] **Step 1: Write failing tests**

Create `attendance/tests/test_analytics.py`:

```python
import datetime
import json
from django.test import TestCase, Client
from django.urls import reverse
from attendance.models import CareGroup, Member, MeetingDate, AttendanceRecord, Visitor


def login_as(client, group, pin='0000'):
    group.set_pin(pin)
    group.save()
    client.post(reverse('login'), {'group_name': group.name, 'pin': pin})


class AnalyticsDataViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )
        self.member1 = Member.objects.create(name='Alice', group=self.group)
        self.member2 = Member.objects.create(name='Bob', group=self.group)
        self.m1 = MeetingDate.objects.create(group=self.group, date=datetime.date(2026, 6, 1))
        self.m2 = MeetingDate.objects.create(group=self.group, date=datetime.date(2026, 6, 8))
        AttendanceRecord.objects.create(meeting_date=self.m1, member=self.member1, is_present=True)
        AttendanceRecord.objects.create(meeting_date=self.m1, member=self.member2, is_present=False)
        AttendanceRecord.objects.create(meeting_date=self.m2, member=self.member1, is_present=True)
        AttendanceRecord.objects.create(meeting_date=self.m2, member=self.member2, is_present=True)
        Visitor.objects.create(meeting_date=self.m1, name='Guest')
        login_as(self.client, self.group)

    def test_requires_login(self):
        self.client.get(reverse('logout'))
        response = self.client.get(reverse('analytics_data'))
        self.assertEqual(response.status_code, 302)

    def test_returns_json(self):
        response = self.client.get(reverse('analytics_data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_weekly_totals_include_visitors(self):
        response = self.client.get(reverse('analytics_data') + '?from=2026-06-01&to=2026-06-30')
        data = json.loads(response.content)
        labels = data['weekly']['labels']
        totals = data['weekly']['totals']
        # m1: 1 present + 1 visitor = 2
        self.assertEqual(totals[labels.index('2026-06-01')], 2)
        # m2: 2 present = 2
        self.assertEqual(totals[labels.index('2026-06-08')], 2)

    def test_member_rates(self):
        response = self.client.get(reverse('analytics_data') + '?from=2026-06-01&to=2026-06-30')
        data = json.loads(response.content)
        rates = {item['name']: item['rate'] for item in data['member_rates']}
        self.assertEqual(rates['Alice'], 100.0)
        self.assertEqual(rates['Bob'], 50.0)

    def test_date_filter_excludes_out_of_range(self):
        response = self.client.get(reverse('analytics_data') + '?from=2026-06-05&to=2026-06-15')
        data = json.loads(response.content)
        labels = data['weekly']['labels']
        self.assertNotIn('2026-06-01', labels)
        self.assertIn('2026-06-08', labels)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python manage.py test attendance.tests.test_analytics -v 2
```

Expected: `NoReverseMatch: Reverse for 'analytics_data' not found`

- [ ] **Step 3: Create attendance/views/analytics.py**

```python
import datetime
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from attendance.decorators import group_login_required, staff_required
from attendance.models import CareGroup, Member, MeetingDate, AttendanceRecord, Visitor


def _default_date_range():
    today = datetime.date.today()
    return today - datetime.timedelta(days=91), today


def _parse_date_params(request):
    try:
        from_date = datetime.date.fromisoformat(request.GET.get('from', ''))
    except ValueError:
        from_date = None
    try:
        to_date = datetime.date.fromisoformat(request.GET.get('to', ''))
    except ValueError:
        to_date = None
    if not from_date or not to_date:
        from_date, to_date = _default_date_range()
    return from_date, to_date


@group_login_required
def analytics(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    return render(request, 'attendance/analytics.html', {'group': group})


@group_login_required
def analytics_data(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    from_date, to_date = _parse_date_params(request)

    meetings = MeetingDate.objects.filter(
        group=group, date__gte=from_date, date__lte=to_date
    ).order_by('date')
    meeting_ids = list(meetings.values_list('pk', flat=True))
    meeting_count = len(meeting_ids)

    weekly_labels, weekly_totals = [], []
    for meeting in meetings:
        present = AttendanceRecord.objects.filter(
            meeting_date=meeting, is_present=True
        ).count()
        visitors = Visitor.objects.filter(meeting_date=meeting).count()
        weekly_labels.append(str(meeting.date))
        weekly_totals.append(present + visitors)

    active_members = Member.objects.filter(group=group, is_active=True)
    member_rates = []
    for member in active_members:
        attended = AttendanceRecord.objects.filter(
            meeting_date_id__in=meeting_ids, member=member, is_present=True
        ).count()
        rate = round((attended / meeting_count) * 100, 1) if meeting_count > 0 else 0.0
        member_rates.append({
            'name': member.name,
            'rate': rate,
            'attended': attended,
            'total': meeting_count,
        })

    return JsonResponse({
        'weekly': {'labels': weekly_labels, 'totals': weekly_totals},
        'member_rates': member_rates,
        'from_date': str(from_date),
        'to_date': str(to_date),
    })
```

- [ ] **Step 4: Create templates/attendance/analytics.html**

```html
{% extends 'attendance/base.html' %}

{% block title %}Analytics — {{ group.name }}{% endblock %}

{% block header %}
<a href="{% url 'meeting_list' %}" class="header-back">‹ Meetings</a>
<span class="app-title">Analytics</span>
<a href="{% url 'logout' %}" class="header-logout">Sign out</a>
{% endblock %}

{% block content %}
<div class="page-container">
  <div class="range-presets">
    <button class="preset-btn" data-days="30">1 month</button>
    <button class="preset-btn active" data-days="91">3 months</button>
    <button class="preset-btn" data-days="183">6 months</button>
    <button class="preset-btn" data-days="365">1 year</button>
    <button class="preset-btn" data-custom="true">Custom</button>
  </div>
  <div id="custom-range" class="custom-range hidden">
    <input type="date" id="from-date" class="date-input">
    <span>to</span>
    <input type="date" id="to-date" class="date-input">
    <button class="btn btn-secondary" id="apply-range">Apply</button>
  </div>

  <div class="chart-section">
    <h3 class="chart-title">Weekly Attendance</h3>
    <canvas id="weekly-chart"></canvas>
  </div>

  <div class="chart-section">
    <h3 class="chart-title">Attendance Rate by Member</h3>
    <canvas id="member-chart"></canvas>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
{% load static %}
<script>const DATA_URL = "{% url 'analytics_data' %}";</script>
<script src="{% static 'attendance/js/charts.js' %}"></script>
{% endblock %}
```

- [ ] **Step 5: Create attendance/static/attendance/js/charts.js**

```javascript
let weeklyChart = null;
let memberChart = null;

function getDaysAgo(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

function today() {
  return new Date().toISOString().split('T')[0];
}

async function loadCharts(fromDate, toDate) {
  const res = await fetch(`${DATA_URL}?from=${fromDate}&to=${toDate}`);
  const data = await res.json();

  if (weeklyChart) weeklyChart.destroy();
  if (memberChart) memberChart.destroy();

  weeklyChart = new Chart(document.getElementById('weekly-chart'), {
    type: 'line',
    data: {
      labels: data.weekly.labels,
      datasets: [{
        label: 'Total Present',
        data: data.weekly.totals,
        borderColor: '#007AFF',
        backgroundColor: 'rgba(0,122,255,0.1)',
        tension: 0.3,
        fill: true,
        pointBackgroundColor: '#007AFF',
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    }
  });

  memberChart = new Chart(document.getElementById('member-chart'), {
    type: 'bar',
    data: {
      labels: data.member_rates.map(m => m.name),
      datasets: [{
        label: 'Attendance %',
        data: data.member_rates.map(m => m.rate),
        backgroundColor: '#34C759',
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, max: 100 } },
    }
  });
}

// Default: 3 months (active preset)
loadCharts(getDaysAgo(91), today());

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (btn.dataset.custom) {
      document.getElementById('custom-range').classList.toggle('hidden');
    } else {
      document.getElementById('custom-range').classList.add('hidden');
      loadCharts(getDaysAgo(parseInt(btn.dataset.days)), today());
    }
  });
});

document.getElementById('apply-range').addEventListener('click', () => {
  const from = document.getElementById('from-date').value;
  const to = document.getElementById('to-date').value;
  if (from && to) loadCharts(from, to);
});
```

- [ ] **Step 6: Update attendance/urls.py**

```python
from django.urls import path
from attendance.views.auth import login_view, logout_view
from attendance.views.meetings import meeting_list, meeting_detail, add_visitor
from attendance.views.analytics import analytics, analytics_data

urlpatterns = [
    path('', meeting_list, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('meetings/', meeting_list, name='meeting_list'),
    path('meetings/<str:date>/', meeting_detail, name='meeting_detail'),
    path('meetings/<str:date>/visitor/', add_visitor, name='add_visitor'),
    path('analytics/', analytics, name='analytics'),
    path('analytics/data/', analytics_data, name='analytics_data'),
]
```

- [ ] **Step 7: Add analytics link to meeting_list.html**

In `templates/attendance/meeting_list.html`, before the closing `</div>` of `.page-container`, add:

```html
  <a href="{% url 'analytics' %}" class="btn btn-secondary analytics-link">View Analytics</a>
```

- [ ] **Step 8: Run all tests**

```bash
python manage.py test attendance -v 2
```

Expected: All tests pass.

- [ ] **Step 9: Commit**

```bash
git add attendance/ templates/
git commit -m "feat: add leader analytics with Chart.js and date range controls"
```

---

### Task 7: Admin Dashboard

**Files:**
- Modify: `attendance/views/analytics.py`
- Create: `templates/attendance/admin_dashboard.html`
- Create: `attendance/static/attendance/js/admin_charts.js`
- Modify: `attendance/urls.py`
- Modify: `attendance/tests/test_analytics.py`

**Interfaces:**
- Consumes: `staff_required`; `_parse_date_params` from `attendance.views.analytics`; all models
- Produces: URL names `admin_dashboard` and `admin_dashboard_data`; JSON: `{'groups': [{'name': str, 'weekly': {'labels': [str], 'totals': [int]}, 'overall_rate': float, 'meeting_count': int}], 'from_date': str, 'to_date': str}`

- [ ] **Step 1: Write failing tests**

Append to `attendance/tests/test_analytics.py`:

```python
class AdminDashboardDataViewTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.client = Client()
        self.staff = User.objects.create_user('admin', password='pass', is_staff=True)
        self.client.login(username='admin', password='pass')
        self.g1 = CareGroup.objects.create(
            name='Alpha', meeting_day=6, meeting_time=datetime.time(10, 0)
        )
        self.g2 = CareGroup.objects.create(
            name='Beta', meeting_day=0, meeting_time=datetime.time(19, 0)
        )
        m1 = Member.objects.create(name='Alice', group=self.g1)
        m2 = Member.objects.create(name='Bob', group=self.g2)
        meet1 = MeetingDate.objects.create(group=self.g1, date=datetime.date(2026, 6, 1))
        meet2 = MeetingDate.objects.create(group=self.g2, date=datetime.date(2026, 6, 1))
        AttendanceRecord.objects.create(meeting_date=meet1, member=m1, is_present=True)
        AttendanceRecord.objects.create(meeting_date=meet2, member=m2, is_present=True)

    def test_requires_staff(self):
        self.client.logout()
        response = self.client.get(reverse('admin_dashboard_data'))
        self.assertEqual(response.status_code, 302)

    def test_returns_json(self):
        response = self.client.get(reverse('admin_dashboard_data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_includes_all_groups(self):
        response = self.client.get(reverse('admin_dashboard_data'))
        data = json.loads(response.content)
        names = [g['name'] for g in data['groups']]
        self.assertIn('Alpha', names)
        self.assertIn('Beta', names)

    def test_weekly_totals_per_group(self):
        response = self.client.get(
            reverse('admin_dashboard_data') + '?from=2026-06-01&to=2026-06-30'
        )
        data = json.loads(response.content)
        alpha = next(g for g in data['groups'] if g['name'] == 'Alpha')
        idx = alpha['weekly']['labels'].index('2026-06-01')
        self.assertEqual(alpha['weekly']['totals'][idx], 1)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python manage.py test attendance.tests.test_analytics.AdminDashboardDataViewTest -v 2
```

Expected: `NoReverseMatch: Reverse for 'admin_dashboard_data' not found`

- [ ] **Step 3: Append admin views to attendance/views/analytics.py**

```python
@staff_required
def admin_dashboard(request):
    from attendance.models import CareGroup as CG
    groups = CG.objects.all().order_by('name')
    return render(request, 'attendance/admin_dashboard.html', {'groups': groups})


@staff_required
def admin_dashboard_data(request):
    from_date, to_date = _parse_date_params(request)
    groups = CareGroup.objects.all().order_by('name')
    result = []

    for group in groups:
        meetings = MeetingDate.objects.filter(
            group=group, date__gte=from_date, date__lte=to_date
        ).order_by('date')
        meeting_ids = list(meetings.values_list('pk', flat=True))
        meeting_count = len(meeting_ids)

        weekly_labels, weekly_totals = [], []
        for meeting in meetings:
            present = AttendanceRecord.objects.filter(
                meeting_date=meeting, is_present=True
            ).count()
            visitors = Visitor.objects.filter(meeting_date=meeting).count()
            weekly_labels.append(str(meeting.date))
            weekly_totals.append(present + visitors)

        active_member_count = Member.objects.filter(group=group, is_active=True).count()
        total_attended = AttendanceRecord.objects.filter(
            meeting_date_id__in=meeting_ids, is_present=True
        ).count()
        denominator = meeting_count * active_member_count
        overall_rate = round((total_attended / denominator) * 100, 1) if denominator > 0 else 0.0

        result.append({
            'name': group.name,
            'weekly': {'labels': weekly_labels, 'totals': weekly_totals},
            'overall_rate': overall_rate,
            'meeting_count': meeting_count,
        })

    return JsonResponse({
        'groups': result,
        'from_date': str(from_date),
        'to_date': str(to_date),
    })
```

- [ ] **Step 4: Create templates/attendance/admin_dashboard.html**

```html
{% extends 'attendance/base.html' %}

{% block title %}Admin Dashboard{% endblock %}

{% block header %}
<a href="/admin/" class="header-back">‹ Admin</a>
<span class="app-title">All Groups</span>
<a href="{% url 'logout' %}" class="header-logout">Sign out</a>
{% endblock %}

{% block content %}
<div class="page-container">
  <div class="range-presets">
    <button class="preset-btn" data-days="30">1 month</button>
    <button class="preset-btn active" data-days="91">3 months</button>
    <button class="preset-btn" data-days="183">6 months</button>
    <button class="preset-btn" data-days="365">1 year</button>
    <button class="preset-btn" data-custom="true">Custom</button>
  </div>
  <div id="custom-range" class="custom-range hidden">
    <input type="date" id="from-date" class="date-input">
    <span>to</span>
    <input type="date" id="to-date" class="date-input">
    <button class="btn btn-secondary" id="apply-range">Apply</button>
  </div>
  <div id="group-charts"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
{% load static %}
<script>const ADMIN_DATA_URL = "{% url 'admin_dashboard_data' %}";</script>
<script src="{% static 'attendance/js/admin_charts.js' %}"></script>
{% endblock %}
```

- [ ] **Step 5: Create attendance/static/attendance/js/admin_charts.js**

```javascript
let charts = [];

function getDaysAgo(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

function today() {
  return new Date().toISOString().split('T')[0];
}

async function loadAdminCharts(fromDate, toDate) {
  charts.forEach(c => c.destroy());
  charts = [];
  document.getElementById('group-charts').innerHTML = '';

  const res = await fetch(`${ADMIN_DATA_URL}?from=${fromDate}&to=${toDate}`);
  const data = await res.json();

  data.groups.forEach(group => {
    const section = document.createElement('div');
    section.className = 'chart-section';
    const safeId = 'chart-' + group.name.replace(/\W/g, '-');
    section.innerHTML = `
      <h3 class="chart-title">
        ${group.name}
        <span class="rate-badge">${group.overall_rate}%</span>
      </h3>
      <canvas id="${safeId}"></canvas>
    `;
    document.getElementById('group-charts').appendChild(section);

    charts.push(new Chart(document.getElementById(safeId), {
      type: 'bar',
      data: {
        labels: group.weekly.labels,
        datasets: [{
          label: 'Present',
          data: group.weekly.totals,
          backgroundColor: '#007AFF',
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
      }
    }));
  });
}

loadAdminCharts(getDaysAgo(91), today());

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (btn.dataset.custom) {
      document.getElementById('custom-range').classList.toggle('hidden');
    } else {
      document.getElementById('custom-range').classList.add('hidden');
      loadAdminCharts(getDaysAgo(parseInt(btn.dataset.days)), today());
    }
  });
});

document.getElementById('apply-range').addEventListener('click', () => {
  const from = document.getElementById('from-date').value;
  const to = document.getElementById('to-date').value;
  if (from && to) loadAdminCharts(from, to);
});
```

- [ ] **Step 6: Update attendance/urls.py**

```python
from django.urls import path
from attendance.views.auth import login_view, logout_view
from attendance.views.meetings import meeting_list, meeting_detail, add_visitor
from attendance.views.analytics import (
    analytics, analytics_data, admin_dashboard, admin_dashboard_data
)

urlpatterns = [
    path('', meeting_list, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('meetings/', meeting_list, name='meeting_list'),
    path('meetings/<str:date>/', meeting_detail, name='meeting_detail'),
    path('meetings/<str:date>/visitor/', add_visitor, name='add_visitor'),
    path('analytics/', analytics, name='analytics'),
    path('analytics/data/', analytics_data, name='analytics_data'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/data/', admin_dashboard_data, name='admin_dashboard_data'),
]
```

- [ ] **Step 7: Run all tests**

```bash
python manage.py test attendance -v 2
```

Expected: All tests pass.

- [ ] **Step 8: Commit**

```bash
git add attendance/ templates/
git commit -m "feat: add admin dashboard with cross-group analytics"
```

---

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
