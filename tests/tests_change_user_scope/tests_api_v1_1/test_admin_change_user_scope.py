# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)
import json


#: Admin user change scopes to other users
class AdminUserChangeScopesTestCase(APITestCase):
    def setUp(self):

        # Creation of one user of each level
        self.admin = User.objects.create_user('admin@netsach.org')

        self.admin.set_password('plop')
        self.admin.admin = True
        self.admin.is_staff = True
        self.admin.save()
        UserConfirmation.objects.create(user=self.admin, confirmed=True).save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

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

        self.admin_2 = User.objects.create_user('admin_2@netsach.org')
        self.admin_2.set_password('plop')
        self.admin_2.admin = True
        self.admin_2.is_staff = True
        self.admin_2.save()
        UserConfirmation.objects.create(
            user=self.admin_2, confirmed=True
        ).save()

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

        # Superuser has 3 dividers
        self.admin.defaultdividers.add(self.divider_1)
        self.admin.defaultdividers.add(self.divider_2)
        self.admin.defaultdividers.add(self.divider_3)

        self.admin_2.defaultdividers.add(self.divider_5)
        self.staff.defaultdividers.add(self.divider_5)
        self.simple_user.defaultdividers.add(self.divider_5)

    def test_admin_add_scopes(self):
        url_user = '/api/v1.1/user/{}/'
        # Add scopes to a superuser impossible
        self.assertEqual(self.superuser.defaultdividers.count(), 0)
        resp = self.client.patch(
            url_user.format(self.superuser.uid),
            data={"defaultdividers": [self.divider_1.uid, self.divider_2.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Add scopes to himself is impossible
        self.assertEqual(self.admin.defaultdividers.count(), 3)
        resp = self.client.patch(
            url_user.format(self.admin.uid),
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
        self.assertEqual(self.admin.defaultdividers.count(), 4)

        # Admin can add scopes he has to an admin
        self.assertEqual(self.admin_2.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.admin_2.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_5.uid,
                ]
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.admin_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.admin_2.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_5.uid]),
        )

        # Admin can add scopes he has to a staff
        self.assertEqual(self.staff.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.staff.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_5.uid,
                ]
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.staff.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.staff.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_5.uid]),
        )

        # Admin can add scopes he has to a simple user
        self.assertEqual(self.simple_user.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_5.uid,
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
            set([self.divider_1.uid, self.divider_2.uid, self.divider_5.uid]),
        )

        # Add scopes to an admin: Same request as above but with the content type
        # It is form data by default so it creates a QueryDict but the request can be a simple dict
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data=json.dumps(
                {
                    "defaultdividers": [
                        str(self.divider_1.uid),
                        str(self.divider_2.uid),
                        str(self.divider_5.uid),
                    ]
                }
            ),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.simple_user.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_5.uid]),
        )

    def test_admin_add_scopes_not_accessible(self):
        url_user = '/api/v1.1/user/{}/'
        # Add scope the admin does not have

        # Admin does not have divider_4 and can't give it to any other level:
        # To admin
        self.assertEqual(self.admin_2.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.admin_2.uid),
            data={"defaultdividers": [self.divider_4.uid, self.divider_5.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        new_dividers = self.admin_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.admin_2.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_5.uid, self.divider_4.uid])
        )

        # To staff
        self.assertEqual(self.staff.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.staff.uid),
            data={"defaultdividers": [self.divider_4.uid, self.divider_5.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.staff.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.staff.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_5.uid, self.divider_4.uid])
        )

        # To simple user
        self.assertEqual(self.simple_user.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data={"defaultdividers": [self.divider_4.uid, self.divider_5.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        new_dividers = self.simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.simple_user.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_5.uid, self.divider_4.uid])
        )

    def test_admin_add_scopes_and_data(self):
        url_user = '/api/v1.1/user/{}/'
        # Add scopes to a user and modify data in the same time
        self.admin_2.first_name = 'PreviousFirstNameAdmin2'
        self.admin_2.last_name = 'PreviousLastNameAdmin2'
        self.staff.first_name = 'PreviousFirstNameStaff'
        self.staff.last_name = 'PreviousLastNameStaff'
        self.simple_user.first_name = 'PreviousFirstNameSimpleU'
        self.simple_user.last_name = 'PreviousLastNameSimpleU'
        self.admin_2.save()
        self.staff.save()
        self.simple_user.save()

        # An admin can't change data to another admin
        self.assertEqual(self.admin_2.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.admin_2.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_5.uid,
                ],
                "first_name": "NewFirstNameAdmin2",
                "last_name": "NewLastNameAdmin2",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.admin_2.refresh_from_db()
        new_dividers = self.admin_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.admin_2.defaultdividers.count(), 1)
        self.assertEqual(set(new_dividers), set([self.divider_5.uid]))
        self.assertEqual(self.admin_2.first_name, 'PreviousFirstNameAdmin2')
        self.assertEqual(self.admin_2.last_name, 'PreviousLastNameAdmin2')

        # An admin is allowed to change data and scope to a staff user
        self.assertEqual(self.staff.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.staff.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_5.uid,
                ],
                "first_name": "NewFirstNameStaff",
                "last_name": "NewLastNameStaff",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.staff.refresh_from_db()
        new_dividers = self.staff.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.staff.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_5.uid]),
        )
        self.assertEqual(self.staff.first_name, 'NewFirstNameStaff')
        self.assertEqual(self.staff.last_name, 'NewLastNameStaff')

        # An admin is allowed to change data and scope to a simple user
        self.assertEqual(self.simple_user.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data={
                "defaultdividers": [
                    self.divider_1.uid,
                    self.divider_2.uid,
                    self.divider_5.uid,
                ],
                "first_name": "NewFirstNameSimpleU",
                "last_name": "NewLastNameSimpleU",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.simple_user.refresh_from_db()
        new_dividers = self.simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.simple_user.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_5.uid]),
        )
        self.assertEqual(self.simple_user.first_name, 'NewFirstNameSimpleU')
        self.assertEqual(self.simple_user.last_name, 'NewLastNameSimpleU')

    def test_admin_remove_scopes(self):
        url_user = '/api/v1.1/user/{}/'
        self.admin_2.defaultdividers.add(self.divider_1)
        self.admin_2.defaultdividers.add(self.divider_2)
        self.admin.defaultdividers.add(self.divider_1)
        self.admin.defaultdividers.add(self.divider_2)
        self.staff.defaultdividers.add(self.divider_1)
        self.staff.defaultdividers.add(self.divider_2)
        self.simple_user.defaultdividers.add(self.divider_1)
        self.simple_user.defaultdividers.add(self.divider_2)

        # Remove scopes to himself is impossible
        self.assertEqual(self.admin.defaultdividers.count(), 3)
        resp = self.client.patch(
            url_user.format(self.admin.uid),
            data={"defaultdividers": [self.divider_1.uid, self.divider_2.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(self.admin.defaultdividers.count(), 2)
        self.admin.refresh_from_db()
        new_dividers = self.admin.defaultdividers.values_list('uid', flat=True)

        self.assertEqual(
            set(new_dividers), set([self.divider_1.uid, self.divider_2.uid])
        )

        # Remove scopes to an admin: divider_2
        # Does not change anything, an admin can't remove a scope to an admin
        self.assertEqual(self.admin_2.defaultdividers.count(), 3)
        resp = self.client.patch(
            url_user.format(self.admin_2.uid),
            data={"defaultdividers": [self.divider_1.uid, self.divider_5.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.admin_2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.admin_2.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_1.uid, self.divider_5.uid])
        )

        # Remove scopes to an staff: divider_2
        self.assertEqual(self.staff.defaultdividers.count(), 3)
        resp = self.client.patch(
            url_user.format(self.staff.uid),
            data={"defaultdividers": [self.divider_1.uid, self.divider_5.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.staff.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(self.staff.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_1.uid, self.divider_5.uid])
        )

        # Remove scopes to a simple user: divider_2
        self.assertEqual(self.simple_user.defaultdividers.count(), 3)
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data={"defaultdividers": [self.divider_1.uid, self.divider_5.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_dividers = self.simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.simple_user.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_1.uid, self.divider_5.uid])
        )
