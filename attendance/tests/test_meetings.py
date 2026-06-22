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
