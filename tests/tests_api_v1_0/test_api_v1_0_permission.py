# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Project
from django.test import override_settings


@override_settings(DEBUG=True)
class PermissionTestCase(APITestCase):
    def setUp(self):
        # User A
        self.user = User.objects.create_user('aaaa@netsach.org')
        self.user.set_password('userA')
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        # User B
        self.user = User.objects.create_user('bbbb@netsach.org')
        self.user.set_password('userB')
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()

    def test_permission(self):
        url_projects = '/api/v1/project/'
        url_login = '/api/v1/auth/login/'
        # Create an object with AUTHENTICATED user
        # Login User A and user B
        resp = self.client.post(
            url_login, {"email": "aaaa@netsach.org", "password": "userA"}
        )
        self.token_user_A = resp.data['token']
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(
            url_login, {"email": "bbbb@netsach.org", "password": "userB"}
        )
        self.token_user_B = resp.data['token']
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotEqual(self.token_user_B, self.token_user_A)
        self.assertEqual(Project.objects.count(), 0)

        resp = self.client.post(
            url_projects,
            {
                "name": "ProjectUserA_PUBLIC",
                "description": "Project of User A",
                "expected_skills_uid": [],
                "members_uid": [],
                "public": True,
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)
        self.assertIn("url", resp.data)
        url_project_public = resp.data['url']
        # Check that patching object don't erase public true
        resp = self.client.patch(
            url_project_public,
            {"description": "Project de A"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
        )
        self.assertEqual(True, Project.objects.first().public)
        # GET an object if:
        # 1) object is PUBLIC (get with unauthenticated user)
        resp = self.client.get(url_project_public)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 2) object is PRIVATE user is AUTHENTICATED
        # and user is  admin of the object
        # set ProjectUserA_Private

        uid_userB = User.objects.get(email="bbbb@netsach.org").uid

        resp = self.client.post(
            url_projects,
            {
                "name": "ProjectUserA_PRIVATE",
                "description": "Project of User A",
                "expected_skills_uid": [],
                "members_uid": [],
                "public": False,
                "can_admin_users": [uid_userB],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertIn(uid_userB, resp.data["can_admin_users"])
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(
            False, Project.objects.get(name="ProjectUserA_PRIVATE").public
        )
        url_projectA_private = resp.data['url']
        # Access with User B
        resp = self.client.get(
            url_projectA_private,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 3) object is PRIVATE user is AUTHENTICATED and user is user view
        uid_userA = User.objects.get(email="aaaa@netsach.org").uid

        resp = self.client.post(
            url_projects,
            {
                "name": "ProjectUserB_PRIVATE",
                "description": "Project of User B",
                "expected_skills_uid": [],
                "members_uid": [],
                "public": False,
                "can_view_users": [uid_userA],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
            format="json",
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertIn(uid_userA, resp.data["can_view_users"])
        self.assertEqual(Project.objects.count(), 3)
        self.assertEqual(
            False, Project.objects.get(name="ProjectUserB_PRIVATE").public
        )
        url_projectB_private = resp.data['url']
        # Access with User B
        resp = self.client.get(
            url_projectB_private,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # CREATE/MODIFY an object if:
        # 1) user is AUTHENTICATED and the OWNER of the object
        # User B patch his own project
        new_descriptionB = "update description projectB"
        resp = self.client.patch(
            url_projectA_private,
            {"description": new_descriptionB},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(new_descriptionB, resp.data["description"])

        # 2) user is AUTHENTICATED and is admin of the project
        # User B patch User A project
        new_descriptionA = "update description projectA"
        resp = self.client.patch(
            url_projectA_private,
            {"description": new_descriptionA},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(new_descriptionA, resp.data["description"])

    def test_permission_on_error(self):
        # Create an object with an UNAUTHENTICATED user
        url_projects = '/api/v1/project/'
        url_login = '/api/v1/auth/login/'

        resp = self.client.post(
            url_projects,
            {
                "name": "ProjectUserA_PUBLIC",
                "description": "Project of User A",
                "expected_skills_uid": [],
                "members_uid": [],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # GET an object if:
        # Login User A and user B
        resp = self.client.post(
            url_login, {"email": "aaaa@netsach.org", "password": "userA"}
        )
        self.token_user_A = resp.data['token']
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(
            url_login, {"email": "bbbb@netsach.org", "password": "userB"}
        )
        self.token_user_B = resp.data['token']
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotEqual(self.token_user_B, self.token_user_A)

        resp = self.client.post(
            url_projects,
            {
                "name": "ProjectUserA_PRIVATE",
                "description": "Project of User A",
                "expected_skills_uid": [],
                "members_uid": [],
                "public": False,
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.data
        )
        self.assertEqual(Project.objects.count(), 1)
        url_projectA_private = resp.data['url']

        # 1) object is PRIVATE
        # Access with UNAUTHENTICATED user
        resp = self.client.get(url_projectA_private, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        # 2) object is PRIVATE user is AUTHENTICATED
        # and user is NOT admin of the object
        resp = self.client.get(
            url_projectA_private,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        # 4) object is PRIVATE user is AUTHENTICATED and user is NOT

        # CREATE/MODIFY an object if:
        # 1) user is AUTHENTICATED and NOT the OWNER of the object
        # 2) user is AUTHENTICATED and is NOT admin of the project

    def test_blocked_user(self):
        url_login = '/api/v1/auth/login/'
        blocked_user = User.objects.create_user('blocked@netsach.org')
        blocked_user.set_password('blocked')
        blocked_user.level = 'blocked'
        blocked_user.save()
        UserConfirmation.objects.create(
            user=blocked_user, confirmed=True
        ).save()

        resp = self.client.post(
            url_login, {"email": "blocked@netsach.org", "password": "blocked"}
        )

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertDictEqual(
            {'message': 'User blocked', "_errors": ["USER_BLOCKED"]}, resp.data
        )
