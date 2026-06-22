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

