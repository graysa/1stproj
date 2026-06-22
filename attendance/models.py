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
