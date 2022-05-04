# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


#: Superuser change scopes to other users
class SuperUserChangeScopesTestCase(APITestCase):
    def setUp(self):

        # Creation of one user of each level
        self.superuser = User.objects.create_user('superuser@netsach.org')
        self.superuser.set_password('plop')
        self.superuser.is_superuser = True
        self.superuser.admin = True
        self.superuser.is_staff = True
        self.superuser.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.superuser, confirmed=True
        ).save()

        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "superuser@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.admin = User.objects.create_user('admin@netsach.org')
        self.admin.set_password('plop')
        self.admin.admin = True
        self.admin.is_staff = True
        self.admin.save()
        UserConfirmation.objects.create(user=self.admin, confirmed=True).save()

        self.staff = User.objects.create_user('staff@netsach.org')
        self.staff.set_password('plop')
        self.staff.is_staff = True
        self.staff.save()
        UserConfirmation.objects.create(user=self.staff, confirmed=True).save()

        self.simple_user = User.objects.create_user('simpleuser@netsach.org')
        self.simple_user.set_password('plop')
        self.simple_user.save()

        UserConfirmation.objects.create(
            user=self.simple_user, confirmed=True
        ).save()

        self.superuser_2 = User.objects.create_user('superuser_2@netsach.org')
        self.superuser_2.set_password('plop')
        self.superuser_2.is_superuser = True
        self.superuser_2.admin = True
        self.superuser_2.is_staff = True
        self.superuser_2.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.superuser_2, confirmed=True
        ).save()

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

        # Superuser has 3 dividers
        self.superuser.defaultdividers.add(self.divider_1)
        self.superuser.defaultdividers.add(self.divider_2)
        self.superuser.defaultdividers.add(self.divider_3)

    def test_su_add_scopes(self):
        url_user = '/api/v1/user/{}/'
        # Add scopes to a superuser
        self.assertEqual(self.superuser_2.defaultdividers.count(), 0)
        resp = self.client.patch(
            url_user.format(self.superuser_2.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_3.uid,
                ]
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.superuser_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.superuser_2.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_3.uid]),
        )

        # Add scopes to an admin
        self.assertEqual(self.admin.defaultdividers.count(), 0)
        resp = self.client.patch(
            url_user.format(self.admin.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_3.uid,
                ]
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.admin.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.admin.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_3.uid]),
        )

        # Add scopes to a staff
        self.assertEqual(self.staff.defaultdividers.count(), 0)
        resp = self.client.patch(
            url_user.format(self.staff.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_3.uid,
                ]
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.staff.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.staff.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_3.uid]),
        )

        # Add scopes to a simple user
        self.assertEqual(self.simple_user.defaultdividers.count(), 0)
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_3.uid,
                ]
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.simple_user.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_3.uid]),
        )

        # Add scope super user does not have
        self.assertEqual(self.superuser_2.defaultdividers.count(), 3)
        # Super user does not have divider_5 but can give it to another user
        resp = self.client.patch(
            url_user.format(self.superuser_2.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_3.uid,
                    self.divider_5.uid,
                ]
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.superuser_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.superuser_2.defaultdividers.count(), 4)
        self.assertEqual(
            set(new_dividers),
            set(
                [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_3.uid,
                    self.divider_5.uid,
                ]
            ),
        )

    def test_su_remove_scopes(self):
        url_user = '/api/v1/user/{}/'
        self.superuser_2.defaultdividers.add(self.divider_1)
        self.superuser_2.defaultdividers.add(self.divider_2)
        self.admin.defaultdividers.add(self.divider_1)
        self.admin.defaultdividers.add(self.divider_2)
        self.staff.defaultdividers.add(self.divider_1)
        self.staff.defaultdividers.add(self.divider_2)
        self.simple_user.defaultdividers.add(self.divider_1)
        self.simple_user.defaultdividers.add(self.divider_2)

        # Remove scopes to a superuser: divider_2
        self.assertEqual(self.superuser_2.defaultdividers.count(), 2)
        resp = self.client.patch(
            url_user.format(self.superuser_2.uid),
            data={"defaultdividers": [self.divider_1.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.superuser_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.superuser_2.defaultdividers.count(), 1)
        self.assertEqual(set(new_dividers), set([self.divider_1.uid]))

        # Remove scopes to an admin: divider_2
        self.assertEqual(self.admin.defaultdividers.count(), 2)
        resp = self.client.patch(
            url_user.format(self.admin.uid),
            data={"defaultdividers": [self.divider_1.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.admin.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.admin.defaultdividers.count(), 1)
        self.assertEqual(set(new_dividers), set([self.divider_1.uid]))

        # Remove scopes to a staff: divider_2
        self.assertEqual(self.staff.defaultdividers.count(), 2)
        resp = self.client.patch(
            url_user.format(self.staff.uid),
            data={"defaultdividers": [self.divider_1.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.staff.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.staff.defaultdividers.count(), 1)
        self.assertEqual(set(new_dividers), set([self.divider_1.uid]))

        # Remove scopes to a simple user: divider_2
        self.assertEqual(self.simple_user.defaultdividers.count(), 2)
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data={"defaultdividers": [self.divider_1.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.simple_user.defaultdividers.count(), 1)
        self.assertEqual(set(new_dividers), set([self.divider_1.uid]))

    def test_su_add_scopes_and_data(self):
        url_user = '/api/v1/user/{}/'
        # Add scopes to a superuser and modify data
        self.assertEqual(self.superuser_2.defaultdividers.count(), 0)
        self.superuser_2.first_name = 'PreviousFirstName'
        self.superuser_2.last_name = 'PreviousLastName'
        self.superuser_2.save()

        resp = self.client.patch(
            url_user.format(self.superuser_2.uid),
            data={
                "defaultdividers": [self.divider_1.uid, self.divider_2.uid],
                "first_name": "NewFirstName",
                "last_name": "NewLastName",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.superuser_2.refresh_from_db()
        new_dividers = self.superuser_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.superuser_2.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_1.uid, self.divider_2.uid])
        )
        self.assertEqual(self.superuser_2.first_name, 'NewFirstName')
        self.assertEqual(self.superuser_2.last_name, 'NewLastName')
