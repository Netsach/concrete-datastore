# coding: utf-8
from django.test import TestCase
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Group,
    DefaultDivider,
    Category,
    NotScopedModel,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class RetrievePermissionLevel(TestCase):
    def setUp(self):
        self.simple = User.objects.create_user(
            email='simple@netsach.org', password='simple'
        )

        self.confirmation = UserConfirmation.objects.create(user=self.simple)
        self.confirmation.confirmed = True
        self.simple.set_level('simple', commit=True)
        self.confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "simple@netsach.org", "password": "simple"}
        )
        self.simple_token = resp.data['token']

        self.manager = User.objects.create_user(
            email='manager@netsach.org', password='manager'
        )

        self.confirmation = UserConfirmation.objects.create(user=self.manager)
        self.confirmation.confirmed = True
        self.manager.set_level('manager', commit=True)
        self.confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "manager@netsach.org", "password": "manager"}
        )
        self.manager_token = resp.data['token']

        self.admin = User.objects.create_user(
            email='admin@netsach.org', password='admin'
        )

        self.confirmation = UserConfirmation.objects.create(user=self.admin)
        self.confirmation.confirmed = True
        self.admin.set_level('admin', commit=True)
        self.confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "admin"}
        )
        self.admin_token = resp.data['token']

        self.group_can_admin = Group.objects.create(
            name="Group for administration"
        )
        self.group_can_admin.members.set(
            [self.simple.uid, self.manager.uid, self.admin.uid]
        )

        self.divider = DefaultDivider.objects.create(name='divider')

        self.category1 = Category.objects.create(
            name='v1', defaultdivider=self.divider
        )
        self.category1.can_admin_groups.set([self.group_can_admin.uid])
        self.category2 = Category.objects.create(
            name='v2', defaultdivider=self.divider
        )
        self.category2.can_admin_groups.set([self.group_can_admin.uid])

        self.category3 = Category.objects.create(
            name='v3', defaultdivider=self.divider
        )
        self.category3.can_admin_groups.set([self.group_can_admin.uid])

        self.simple.defaultdividers.add(self.divider)
        self.manager.defaultdividers.add(self.divider)
        self.admin.defaultdividers.add(self.divider)

        self.simple.save()
        self.manager.save()
        self.admin.save()

    def test_retrieve_permission_for_simple(self):
        url = '/api/v1/category/'

        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.simple_token),
            HTTP_X_ENTITY_UID=str(self.divider.uid),
        )
        self.assertEqual(len(resp.data['results']), 3)

        for category in resp.data['results']:
            resp = self.client.get(
                category['url'],
                HTTP_AUTHORIZATION='Token {}'.format(self.simple_token),
                HTTP_X_ENTITY_UID=str(self.divider.uid),
            )
            self.assertEqual(resp.status_code, 200)

        instance = NotScopedModel.objects.create(
            name='not-scoped', public=False
        )
        url = f'/api/v1/not-scoped-model/{instance.uid}/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.simple_token)
        )
        self.assertEqual(resp.status_code, 404)

        url = '/api/v1/not-scoped-model/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.simple_token)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 0)

        instance.delete()

    def test_retrieve_permission_for_manager(self):
        url = '/api/v1/category/'

        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.manager_token),
            HTTP_X_ENTITY_UID=str(self.divider.uid),
        )
        self.assertEqual(len(resp.data['results']), 3)

        for category in resp.data['results']:
            resp = self.client.get(
                category['url'],
                HTTP_AUTHORIZATION='Token {}'.format(self.manager_token),
                HTTP_X_ENTITY_UID=str(self.divider.uid),
            )
            self.assertEqual(resp.status_code, 200)

        instance = NotScopedModel.objects.create(
            name='not-scoped', public=False
        )

        url = '/api/v1/not-scoped-model/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.manager_token)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 0)

        url = f'/api/v1/not-scoped-model/{instance.uid}/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.manager_token)
        )
        self.assertEqual(resp.status_code, 404)

        instance.delete()

    def test_retrieve_permission_for_admin(self):
        url = '/api/v1/category/'

        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.admin_token),
            HTTP_X_ENTITY_UID=str(self.divider.uid),
        )
        self.assertEqual(len(resp.data['results']), 3)

        for category in resp.data['results']:
            resp = self.client.get(
                category['url'],
                HTTP_AUTHORIZATION='Token {}'.format(self.admin_token),
                HTTP_X_ENTITY_UID=str(self.divider.uid),
            )
            self.assertEqual(resp.status_code, 200)
