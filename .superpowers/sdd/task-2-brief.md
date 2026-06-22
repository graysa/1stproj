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

