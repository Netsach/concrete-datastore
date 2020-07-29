# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


@override_settings(DEBUG=True)
class UserTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

    def test_user_changes_profile_data(self):
        url_login = '/api/v1.1/auth/login/'
        url_user = '/api/v1.1/account/me/'
        # User 1 try to access his info
        resp = self.client.get(
            url_user, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # check that the password isn't in the response
        excluded_fields = [
            'admin',
            'is_staff',
            'is_superuser',
            'is_active',
            'password',
        ]

        for field in excluded_fields:
            self.assertNotIn(field, resp.data)

        _new_email = "johncenaaaaaaaaaaa@wwe.com"
        # User change his email, first and last name
        resp = self.client.patch(
            url_user,
            {"email": _new_email, "first_name": "John", "last_name": "Cena"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Test that changes are done in DataBase
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertEqual(updated_user.email, _new_email)
        self.assertEqual(updated_user.first_name, "John")
        self.assertEqual(updated_user.last_name, "Cena")
        self.assertEqual(updated_user.password, self.user.password)

        # Connection with new email
        resp = self.client.post(
            url_login, {"email": _new_email, "password": "plop"}
        )
        # print(User.objects.all().values_list("email", "username"))
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn("token", resp.data)
        self.token = resp.data['token']

        # user access to his profile
        resp = self.client.get(
            url_user, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # only patch first and last name
        resp = self.client.patch(
            url_user,
            {
                # "email": _new_email,
                "first_name": "Triple",
                "last_name": "H",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertEqual(updated_user.email, _new_email)
        self.assertEqual(updated_user.first_name, "Triple")
        self.assertEqual(updated_user.last_name, "H")
        self.assertEqual(updated_user.password, self.user.password)

        resp = self.client.post(
            url_login, {"email": _new_email, "password": "plop"}
        )

    def test_user_patch_readonly_fields(self):
        url_user = '/api/v1.1/account/me/'
        resp = self.client.patch(
            url_user,
            {'admin': True},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertIs(self.user.admin, False)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_permissions_for_stats(self):
        url_user = '/api/v1.1/user/stats/timestamp_start:123456789.123/'
        resp = self.client.get(
            url_user, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(DEBUG=True)
class ConfirmableUserTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('johndoe@netsach.org')
        self.user.set_password('plop')
        self.user.save()

    def test_is_confirmed(self):
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        self.assertIs(self.user.is_confirmed(), True)

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_is_not_confirmed(self):
        UserConfirmation.objects.create(user=self.user).save()
        self.assertIs(self.user.is_confirmed(), False)

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=False)
    def test_confirm_email_in_settings(self):
        UserConfirmation.objects.create(user=self.user).save()
        self.assertIs(self.user.is_confirmed(), True)

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_no_confirmation(self):
        self.assertIs(self.user.is_confirmed(), False)

    def test_get_or_create_without_redirect(self):
        self.assertIs(
            type(self.user.get_or_create_confirmation()), UserConfirmation
        )

    def test_confirmate_user(self):
        UserConfirmation.objects.create(user=self.user).save()
        self.user.confirmate()
        self.assertIs(self.user.is_confirmed(), True)


@override_settings(DEBUG=True)
class UserLevelComparisonTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('superuser1@netsach.org')
        self.user1.set_password('plop')
        self.user1.is_superuser = True
        self.user1.save()

        self.user2 = User.objects.create_user('superuser2@netsach.org')
        self.user2.set_password('plop')
        self.user2.is_superuser = True
        self.user2.save()

        self.user3 = User.objects.create_user('admin@netsach.org')
        self.user3.set_password('plop')
        self.user3.admin = True
        self.user3.save()

    def test_user_comparison(self):
        self.assertTrue(self.user1 > self.user3)
        self.assertTrue(self.user1 >= self.user3)
        self.assertTrue(self.user3 < self.user1)
        self.assertTrue(self.user3 <= self.user1)
        self.assertTrue(self.user1 >= self.user2)
        self.assertTrue(self.user1 <= self.user2)


@override_settings(DEBUG=True)
class UserComparisonTestCase(APITestCase):
    def setUp(self):
        self.superuser1 = User.objects.create_user(
            'superuser1@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.superuser1.set_password('plop')
        self.superuser1.is_superuser = True
        self.superuser1.save()

        self.superuser2 = User.objects.create_user(
            'superuser2@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.superuser2.set_password('plop')
        self.superuser2.is_superuser = True
        self.superuser2.save()

        self.admin = User.objects.create_user(
            'admin@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.admin.set_password('plop')
        self.admin.admin = True
        self.admin.save()

    def test_compare_users(self):
        self.assertTrue(self.superuser1 > self.admin)
        self.assertFalse(self.superuser1 < self.admin)
        self.assertTrue(self.superuser1 >= self.admin)
        self.assertFalse(self.superuser1 <= self.admin)
        self.assertTrue(self.admin < self.superuser1)
        self.assertFalse(self.admin > self.superuser1)
        self.assertTrue(self.admin <= self.superuser1)
        self.assertFalse(self.admin >= self.superuser1)
        self.assertTrue(self.superuser1 >= self.superuser2)
        self.assertTrue(self.superuser1 <= self.superuser2)


@override_settings(DEBUG=True)
class UserScopesTestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_user(
            'superuser@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.superuser.set_password('plop')
        self.superuser.is_superuser = True
        self.superuser.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.superuser, confirmed=True
        ).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "superuser@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.admin = User.objects.create_user(
            'admin@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.admin.set_password('plop')
        self.admin.admin = True
        self.admin.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.admin, confirmed=True).save()

        self.superuser_test = User.objects.create_user(
            'superuser2@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.superuser_test.set_password('plop')
        self.superuser_test.is_superuser = True
        self.superuser_test.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.superuser_test, confirmed=True
        ).save()

        self.divider = DefaultDivider.objects.create(name='Divider')
