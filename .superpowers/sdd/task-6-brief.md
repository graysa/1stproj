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

