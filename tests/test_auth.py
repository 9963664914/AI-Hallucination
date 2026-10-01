from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class AuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='Password123!', email='test@example.com')

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_invalid_password(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_registration(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'password1': 'NewUserPass123!',
            'password2': 'NewUserPass123!',
            'organization': 'Research Lab',
            'role': 'researcher'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.profile.organization, 'Research Lab')

    def test_profile_view_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
