# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    AuthToken,
    UserConfirmation,
    DefaultDivider,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class ChangePasswordTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.super_user = User.objects.create_user(email='super@super.super')
        self.super_user.is_superuser = True
        self.super_user.admin = True
        self.super_user.is_staff = True
        self.super_user.save()
        confirmation = UserConfirmation.objects.create(user=self.super_user)
        confirmation.confirmed = True
        confirmation.save()

        self.super_user_token = AuthToken.objects.filter(
            user=self.super_user
        ).first()
        if not self.super_user_token:
            self.super_user_token = AuthToken.objects.create(
                user=self.super_user
            )

        self.admin_user = User.objects.create_user(email='admin@admin.admin')
        self.admin_user.is_superuser = False
        self.admin_user.admin = True
        self.admin_user.is_staff = True
        self.admin_user.save()

        self.admin_user_token = AuthToken.objects.filter(
            user=self.admin_user
        ).first()
        if not self.admin_user_token:
            self.admin_user_token = AuthToken.objects.create(
                user=self.admin_user
            )

        self.staff_user = User.objects.create_user(email='staff@staff.staff')
        self.staff_user.is_superuser = False
        self.staff_user.admin = False
        self.staff_user.is_staff = True
        self.staff_user.save()

        self.staff_user_token = AuthToken.objects.filter(
            user=self.staff_user
        ).first()
        if not self.staff_user_token:
            self.staff_user_token = AuthToken.objects.create(
                user=self.staff_user
            )

        self.simple_user = User.objects.create_user(
            email='simple@simple.simple'
        )
        self.simple_user.is_superuser = False
        self.simple_user.admin = False
        self.simple_user.is_staff = False
        self.simple_user.set_password('passwordInitial')
        self.simple_user.save()
        confirmation = UserConfirmation.objects.create(user=self.simple_user)
        confirmation.confirmed = True
        confirmation.save()

        self.simple_user_2 = User.objects.create_user(
            email='simple2@simple2.simple2'
        )
        confirmation = UserConfirmation.objects.create(user=self.simple_user_2)
        confirmation.confirmed = True
        confirmation.save()
        self.simple_user_2_token = AuthToken.objects.filter(
            user=self.simple_user_2
        ).first()
        if not self.simple_user_2_token:
            self.simple_user_2_token = AuthToken.objects.create(
                user=self.simple_user_2
            )

        self.divider_1 = DefaultDivider.objects.create()
        self.divider_2 = DefaultDivider.objects.create()
        self.assertNotEqual(self.divider_1.uid, self.divider_2.uid)
        self.url_login = '/api/v1.1/auth/login/'
        self.url_change = '/api/v1.1/auth/change-password/'

    def test_change_password_invalid_serializer(self):
        resp = self.client.post(
            self.url_change,
            {"email": self.simple_user.email, "password1": "abcas"},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])

    def test_change_password_user_doesnt_exist(self):
        resp = self.client.post(
            self.url_change,
            {
                "email": "jenniferdoe@netsach.com",
                "password1": "abc",  # short password (at least 4 characters)
                "password2": "abc12",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])

    def test_change_password_missmatch(self):
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "abc",  # short password (at least 4 characters)
                "password2": "abc12",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['MISMATCH_PASSWORDS'])

    def test_change_password_with_insecure_password(self):
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "abc",  # short password (at least 4 characters)
                "password2": "abc",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['NOT_ENOUGH_CHARS'])

    @override_settings(ALLOW_REUSE_PASSWORD_ON_CHANGE=False)
    def test_change_password_reused(self):
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "passwordInitial",  # short password (at least 4 characters)
                "password2": "passwordInitial",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['CANNOT_USE_SAME_PASSWORD'])

    def test_basic_change_password_by_super_user(self):
        """
        Test basic change-password workflow
        """

        # Ensure that the simple user can login with initial password
        resp = self.client.post(
            self.url_login,
            {"email": 'simple@simple.simple', "password": "passwordInitial"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Ensure that a super user can change the password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "passwordChangeBy-super-user",
                "password2": "passwordChangeBy-super-user",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Ensure that the simple user can login with password by super user
        resp = self.client.post(
            self.url_login,
            {
                "email": 'simple@simple.simple',
                "password": "passwordChangeBy-super-user",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_basic_change_password_by_admin_user(self):

        # Ensure that the simple user can login with initial password
        resp = self.client.post(
            self.url_login,
            {"email": 'simple@simple.simple', "password": "passwordInitial"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Ensure that a admin user can change the password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "passwordChangeBy-admin-user",
                "password2": "passwordChangeBy-admin-user",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.admin_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Ensure that the simple user can login with password by admin user
        resp = self.client.post(
            self.url_login,
            {
                "email": 'simple@simple.simple',
                "password": "passwordChangeBy-admin-user",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_basic_change_password_by_staff_user_not_in_divider(self):

        # Ensure that a staff user can change the password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "passwordChangeBy-staff-user",
                "password2": "passwordChangeBy-staff-user",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.staff_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_basic_change_password_by_staff_user_in_different_divider(self):

        self.simple_user.defaultdividers.add(self.divider_1)
        self.staff_user.defaultdividers.add(self.divider_2)

        # Ensure that a staff user can change the password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "passwordChangeBy-staff-user",
                "password2": "passwordChangeBy-staff-user",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.staff_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_basic_change_password_of_an_admin_by_staff_user(self):
        # Condition is same divider
        self.admin_user.defaultdividers.add(self.divider_1)
        self.staff_user.defaultdividers.add(self.divider_1)

        # Ensure that a staff user can change the password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.admin_user.email,
                "password1": "passwordChangeBy-staff-user",
                "password2": "passwordChangeBy-staff-user",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.staff_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_basic_change_password_of_an_super_by_staff_user(self):
        # Condition is same divider
        self.super_user.defaultdividers.add(self.divider_1)
        self.staff_user.defaultdividers.add(self.divider_1)

        # Ensure that a staff user can change the password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.super_user.email,
                "password1": "passwordChangeBy-staff-user",
                "password2": "passwordChangeBy-staff-user",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.staff_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_basic_change_password_by_staff_user_same_divider(self):

        # Ensure that the simple user can login with initial password
        resp = self.client.post(
            self.url_login,
            {"email": 'simple@simple.simple', "password": "passwordInitial"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.simple_user.defaultdividers.add(self.divider_1)
        self.staff_user.defaultdividers.add(self.divider_1)

        # Ensure that a staff user can change the password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "passwordChangeBy-staff-user",
                "password2": "passwordChangeBy-staff-user",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.staff_user_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Ensure that the simple user can login with password by staff user
        resp = self.client.post(
            self.url_login,
            {
                "email": 'simple@simple.simple',
                "password": "passwordChangeBy-staff-user",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_basic_change_password_by_simple_user_same_divider(self):
        # simpleuser cannot change another simpleuser's password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user.email,
                "password1": "failed-to-changed",
                "password2": "failed-to-changed",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.simple_user_2_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # simpleuser can change his own password
        resp = self.client.post(
            self.url_change,
            {
                "email": self.simple_user_2.email,
                "password1": "change-success",
                "password2": "change-success",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.simple_user_2_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_basic_authentication_error_cases(self):
        """
        Test basic auth workflow
        """
        # POST an invalid arguiment and get an error (400)
        resp = self.client.post(self.url_change, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])
