# coding: utf-8
from django.test import TestCase
from concrete_datastore.concrete.models import (
    User,
    DefaultDivider,
)


class TestUpdateOrCreateUserScope(TestCase):
    def setUp(self):
        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.admin = User.objects.create_user(
            email='admin@netsach.org', password='plop'
        )
        self.admin.set_level("admin")
        self.admin.save()
        self.manager = User.objects.create_user(
            email='manager@netsach.org', password='plop'
        )
        self.manager.set_level('manager')
        self.manager.save()
        self.admin.defaultdividers.add(self.divider_1)

        # Login to get admin user token
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "admin@netsach.org",
                "password": "plop",
            },
        )
        self.token_admin = resp.data['token']
        resp_user = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "manager@netsach.org",
                "password": "plop",
            },
        )
        self.token_user = resp_user.data['token']

    def test_user_update(self):
        self.assertEqual(self.manager.defaultdividers.count(), 0)
        # Register manager with scope info
        resp = self.client.post(
            '/api/v1.1/auth/register/',
            {
                "email": "manager@netsach.org",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
            HTTP_X_ENTITY_UID=self.divider_1.uid,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.manager.defaultdividers.count(), 1)
        self.assertEqual(self.manager.defaultdividers.first(), self.divider_1)

    def test_admin_update_by_manager(self):
        self.manager.defaultdividers.add(self.divider_2)
        self.assertEqual(self.admin.defaultdividers.count(), 1)
        resp = self.client.post(
            '/api/v1.1/auth/register/',
            {
                "email": "admin@netsach.org",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
            HTTP_X_ENTITY_UID=self.divider_2.uid,
        )
        resp_json = resp.json()
        self.assertDictEqual(
            resp_json,
            {
                "message": "manager is not allowed to update a user with level admin"
            },
        )
        self.assertEqual(resp.status_code, 403, msg=resp.content)
        self.assertEqual(self.admin.defaultdividers.count(), 1)
        self.assertEqual(self.admin.defaultdividers.first(), self.divider_1)

    def test_user_update_no_authorization(self):
        # Register manager with scope info
        resp = self.client.post(
            '/api/v1.1/auth/register/',
            {
                "email": "manager@netsach.org",
            },
            HTTP_AUTHORIZATION='Token FAKE TOKEN',
            HTTP_X_ENTITY_UID=self.divider_1.uid,
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(self.manager.defaultdividers.count(), 0)

    def test_user_create(self):
        self.assertEqual(self.manager.defaultdividers.count(), 0)
        self.assertEqual(User.objects.all().count(), 2)
        # Register manager with scope info
        resp = self.client.post(
            '/api/v1.1/auth/register/',
            {
                "email": "manager_does_not_exist@netsach.org",
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
            HTTP_X_ENTITY_UID=self.divider_1.uid,
        )
        user = User.objects.get(email="manager_does_not_exist@netsach.org")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(user.defaultdividers.count(), 1)
        self.assertEqual(user.defaultdividers.first(), self.divider_1)
