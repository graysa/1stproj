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
