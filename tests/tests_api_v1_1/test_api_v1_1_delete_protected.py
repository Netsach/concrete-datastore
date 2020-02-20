# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Category,
    Skill,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class CreationMinimumLevelTestCase(APITestCase):
    def setUp(self):

        self.user_superuser = User.objects.create_user('su@netsach.org')
        self.user_superuser.set_password('plop')
        self.user_superuser.set_level('superuser')
        self.user_superuser.save()
        confirmation = UserConfirmation.objects.create(
            user=self.user_superuser
        )
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "su@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']
        self.category = Category.objects.create(name="TEST_CAT")
        self.skill = Skill.objects.create(
            name="TEST_SKILL", category=self.category
        )

    def test_delete_protected(self):
        """
        Model Skill has a FK to model Category with "on_delete=PROTECTED".
        Attempting to delete a category related to a skill should fail
        with a response HTTP_412_PRECONDITION_FAILED
        """
        url_category = f'/api/v1.1/category/{self.category.uid}/'
        resp = self.client.delete(
            url_category, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_412_PRECONDITION_FAILED)
