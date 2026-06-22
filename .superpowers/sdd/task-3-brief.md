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

