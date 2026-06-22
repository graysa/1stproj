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
