# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


#: Simple user does not have access to other users
class SimpleUserChangeScopesTestCase(APITestCase):
    def setUp(self):
        # Creation of one user of each level

        self.simple_user = User.objects.create_user('simpleuser@netsach.org')
        self.simple_user.set_password('plop')
        self.simple_user.public = True
        self.simple_user.save()

        UserConfirmation.objects.create(
            user=self.simple_user, confirmed=True
        ).save()

        self.staff = User.objects.create_user('staff@netsach.org')

        self.staff.set_password('plop')
        self.staff.is_staff = True
        self.staff.public = True
        self.staff.save()
        UserConfirmation.objects.create(user=self.staff, confirmed=True).save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "simpleuser@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.simpleuser2 = User.objects.create_user('simpleuser2@netsach.org')
        self.simpleuser2.set_password('plop')
        self.simpleuser2.is_staff = True
        self.simpleuser2.public = True
        self.simpleuser2.save()
        UserConfirmation.objects.create(
            user=self.simpleuser2, confirmed=True
        ).save()

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

        # Superuser has 3 dividers
        self.simple_user.defaultdividers.add(self.divider_1)
        self.simple_user.defaultdividers.add(self.divider_2)
        self.simple_user.defaultdividers.add(self.divider_3)

        self.staff.defaultdividers.add(self.divider_2)
        self.simpleuser2.defaultdividers.add(self.divider_2)

    def test_simpleuser_add_scopes(self):
        url_user = '/api/v1.1/user/{}/'
        # Change anything on a user is impossible except himself (fields)
        self.assertEqual(self.staff.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.staff.uid),
            data={"defaultdividers": [self.divider_1.uid, self.divider_2.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.staff.defaultdividers.count(), 1)

        self.assertEqual(self.simpleuser2.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.simpleuser2.uid),
            data={"defaultdividers": [self.divider_1.uid, self.divider_2.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.simpleuser2.defaultdividers.count(), 1)

    def test_simpleuser_change_data(self):
        self.simpleuser2.first_name = 'PreviousFirstNameSimpleU2'
        self.simpleuser2.last_name = 'PreviousLastNameSimpleU2'
        self.simple_user.first_name = 'PreviousFirstNameSimpleU'
        self.simple_user.last_name = 'PreviousLastNameSimpleU'
        self.simpleuser2.save()
        self.simple_user.save()

        url_user = '/api/v1.1/user/{}/'

        # Change data of other users is forbidden
        self.assertEqual(self.simpleuser2.defaultdividers.count(), 1)
        resp = self.client.patch(
            url_user.format(self.simpleuser2.uid),
            data={
                "first_name": "NewFirstNameSimpleU2",
                "last_name": "NewLastNameSimpleU2",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.simpleuser2.defaultdividers.count(), 1)
        self.assertEqual(
            self.simpleuser2.first_name, 'PreviousFirstNameSimpleU2'
        )
        self.assertEqual(
            self.simpleuser2.last_name, 'PreviousLastNameSimpleU2'
        )

        #: Change only data of himself
        self.assertEqual(self.simple_user.defaultdividers.count(), 3)
        resp = self.client.patch(
            url_user.format(self.simple_user.uid),
            data={
                "first_name": "NewFirstNameSimpleU",
                "last_name": "NewLastNameSimpleU",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.simple_user.refresh_from_db()
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #: Change only data of himself
        self.assertEqual(self.simple_user.defaultdividers.count(), 3)
        resp = self.client.patch(
            '/api/v1.1/account/me/',
            data={
                "first_name": "NewFirstNameSimpleU",
                "last_name": "NewLastNameSimpleU",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.simple_user.refresh_from_db()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(self.simple_user.defaultdividers.count(), 3)
        self.assertEqual(self.simple_user.first_name, 'NewFirstNameSimpleU')
        self.assertEqual(self.simple_user.last_name, 'NewLastNameSimpleU')
