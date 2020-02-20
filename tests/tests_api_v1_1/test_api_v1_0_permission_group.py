# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    Group,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class PermissionGroupTestCase(APITestCase):
    def setUp(self):

        self.url_projects = '/api/v1.1/project/'
        self.url_login = '/api/v1.1/auth/login/'

        # Group G1
        Group.objects.get_or_create(name='G1')
        # Group G2
        Group.objects.get_or_create(name='G2')
        self.uid_group_1 = Group.objects.get(name='G1').uid
        self.uid_group_2 = Group.objects.get(name='G2').uid

        # User A
        self.userA = User.objects.create_user('aaaa@netsach.org')
        self.userA.set_password('userA')
        self.userA.save()
        UserConfirmation.objects.create(user=self.userA, confirmed=True).save()

        # User B, member of G1
        self.userB = User.objects.create_user('bbbb@netsach.org')
        self.userB.set_password('userB')
        self.userB.concrete_groups.add(Group.objects.get(name='G1'))
        self.userB.save()
        UserConfirmation.objects.create(user=self.userB, confirmed=True).save()

        # User C
        self.userC = User.objects.create_user('cccc@netsach.org')
        self.userC.set_password('userC')
        self.userC.save()
        UserConfirmation.objects.create(user=self.userC, confirmed=True).save()

    # Login user
    def login(self, email, password):
        resp = self.client.post(
            self.url_login, {"email": email, "password": password}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return resp.data['token']

    def create_project(self, params, token):
        current_count = Project.objects.count()
        resp = self.client.post(
            self.url_projects,
            params,
            HTTP_AUTHORIZATION='Token {}'.format(token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), current_count + 1)
        self.assertIn("url", resp.data)
        return resp.data['url']

    def test_permission(self):

        # Summary :
        # => User can GET object if at least one of the followings is true:
        #    - Object is public
        #    - (NOT IMPLEMENTED) User is authenticated and object is public_for_authenticated
        #    - User is owner of the project
        #    - User is in the can_view_groups of the object
        #    - User is in the can_admin_groups of the object
        # => User can PATCH object if :
        #    - User is owner of the object
        #    - User is in the can_admin_groups of the object

        # Login user A and user B
        self.token_user_B = self.login("bbbb@netsach.org", "userB")
        self.token_user_A = self.login("aaaa@netsach.org", "userA")
        self.assertNotEqual(self.token_user_B, self.token_user_A)

        url_project = self.create_project(
            {
                "name": "ProjectUserA_PRIVATE",
                "description": "Project of User A",
                "skills": [],
                "members": [],
                "public": False,
                "can_view_groups": [self.uid_group_1],
            },
            self.token_user_A,
        )

        self.assertEqual(
            Project.objects.first().can_view_groups.get_queryset()[0].uid,
            self.uid_group_1,
        )
        # GET an object if
        # 1) user is in the group G1
        resp = self.client.get(
            url_project,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 2) user is owner
        resp = self.client.get(
            url_project,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 3) project is public
        # A patch project to be public and remove G1 from can_view_groups
        resp = self.client.patch(
            url_project,
            {"public": True, "can_view_groups": []},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(True, Project.objects.first().public)
        resp = self.client.get(
            url_project,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 4) user is in the can_admin_groups
        url_project_2 = self.create_project(
            {
                "name": "P2",
                "description": "Project 2 of User A",
                "skills": [],
                "members": [],
                "public": False,
                "can_admin_groups": [self.uid_group_1],
            },
            self.token_user_A,
        )
        resp = self.client.get(
            url_project_2,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["description"], "Project 2 of User A")

        # 5) project is public_for_authenticated
        # url_project_3 = self.create_project({
        #         "name": "P3",
        #         "description": "Project 3 of User A",
        #         "skills": [],
        #         "members": [],
        #         "public": False,
        #         "public_for_authenticated": True,
        #     }, self.token_user_A
        # )
        # resp = self.client.get(
        #     url_project_3,
        #     {},
        #     HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B)
        # )
        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.assertEqual(resp.data["description"], "Project 3 of User A")

        # PATCH if
        url_project_4 = self.create_project(
            {
                "name": "P4",
                "description": "Project 4 of User A",
                "skills": [],
                "members": [],
                "public": False,
            },
            self.token_user_A,
        )
        # 1) user is AUTHENTICATED and the OWNER of the object
        resp = self.client.patch(
            url_project_4,
            {"can_admin_groups": [self.uid_group_1]},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.uid_group_1,
            Project.objects.get(name="P4")
            .can_admin_groups.get_queryset()[0]
            .uid,
        )

        # 2) user is AUTHENTICATED and is in the admin group
        new_descriptionB = "update from B"
        resp = self.client.patch(
            url_project_4,
            {"description": new_descriptionB},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(new_descriptionB, resp.data["description"])

    def test_permission_on_error(self):

        # Summary :
        # => For all of the GET tests errors, object is always private
        #      (otherwise GET would always return 200)
        #      User is denied permission to GET object if :
        #       - User is not authenticated
        #       - User is not in can_view_groups nor can_admin_groups
        #            and public_for_authenticated is false
        # => For all of the PATCH tests errors, object is always public
        #    - User is not authenticated
        #    - User is not in can_admin_groups

        # Login User A and user B
        self.token_user_A = self.login("aaaa@netsach.org", "userA")
        self.token_user_B = self.login("bbbb@netsach.org", "userB")
        self.assertNotEqual(self.token_user_B, self.token_user_A)

        url_project_1 = self.create_project(
            {
                "name": "P1",
                "description": "P1a",
                "skills": [],
                "members": [],
                "public": False,
                # "public_for_authenticated": True,
                "can_view_groups": [self.uid_group_1],
                "can_admin_groups": [self.uid_group_2],
            },
            self.token_user_A,
        )

        # GET
        # 1) User is not authenticated
        resp = self.client.get(url_project_1, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        resp = self.client.patch(
            url_project_1,
            {
                "description": "P1b",
                # "public_for_authenticated": False,
                "can_view_groups": [self.uid_group_2],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['description'], 'P1b')
        self.assertEqual(resp.data['can_view_groups'], [self.uid_group_2])
        self.assertEqual(
            Project.objects.first().can_view_groups.get_queryset()[0].uid,
            self.uid_group_2,
        )

        # 2) User is not in can_view_groups nor can_admin_groups
        resp = self.client.get(
            url_project_1,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
        )

        # PATCH
        url_project_2 = self.create_project(
            {
                "name": "P2",
                "description": "P1a",
                "skills": [],
                "members": [],
                "public": True,
                # "public_for_authenticated": True,
                "can_view_groups": [self.uid_group_1],
                "can_admin_groups": [self.uid_group_2],
            },
            self.token_user_A,
        )
        # 1) User is not authenticated
        resp = self.client.patch(
            url_project_2, {"description": "Not authenticated update"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check that description is NOT updated
        resp = self.client.get(
            url_project_2,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['description'], 'P1a')

        # 2) User is not in can_admin_groups
        resp = self.client.patch(
            url_project_2,
            {"description": "Not in admin group update"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_B),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Check that description is NOT updated
        resp = self.client.get(
            url_project_2,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user_A),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['description'], 'P1a')
