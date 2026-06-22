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
