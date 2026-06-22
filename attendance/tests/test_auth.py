import datetime
from django.test import TestCase, Client
from django.urls import reverse
from attendance.models import CareGroup


def make_group(name='Alpha'):
    group = CareGroup.objects.create(
        name=name, meeting_day=6, meeting_time=datetime.time(10, 0)
    )
    group.set_pin('1234')
    group.save()
    return group


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = make_group()

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_correct_pin_sets_session(self):
        self.client.post(reverse('login'), {'group_name': 'Alpha', 'pin': '1234'})
        self.assertEqual(self.client.session['group_id'], self.group.pk)

    def test_login_correct_pin_redirects(self):
        response = self.client.post(
            reverse('login'), {'group_name': 'Alpha', 'pin': '1234'}
        )
        self.assertEqual(response.status_code, 302)

    def test_login_wrong_pin_does_not_set_session(self):
        self.client.post(reverse('login'), {'group_name': 'Alpha', 'pin': '9999'})
        self.assertNotIn('group_id', self.client.session)

    def test_login_wrong_pin_returns_200(self):
        response = self.client.post(
            reverse('login'), {'group_name': 'Alpha', 'pin': '9999'}
        )
        self.assertEqual(response.status_code, 200)

    def test_login_nonexistent_group_does_not_set_session(self):
        self.client.post(reverse('login'), {'group_name': 'Ghost', 'pin': '1234'})
        self.assertNotIn('group_id', self.client.session)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = make_group()
        self.client.post(reverse('login'), {'group_name': 'Alpha', 'pin': '1234'})

    def test_logout_clears_session(self):
        self.client.get(reverse('logout'))
        self.assertNotIn('group_id', self.client.session)

    def test_logout_redirects_to_login(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class DecoratorTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = make_group()

    def test_group_login_required_redirects_when_no_session(self):
        from attendance.decorators import group_login_required
        from django.test import RequestFactory
        from django.http import HttpResponse

        factory = RequestFactory()
        request = factory.get('/fake/')
        request.session = {}

        @group_login_required
        def fake_view(request):
            return HttpResponse('ok')

        response = fake_view(request)
        self.assertEqual(response.status_code, 302)
