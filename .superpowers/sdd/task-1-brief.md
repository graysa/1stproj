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

