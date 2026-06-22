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

