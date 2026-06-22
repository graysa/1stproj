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
