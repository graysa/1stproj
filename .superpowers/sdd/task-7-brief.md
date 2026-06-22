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

