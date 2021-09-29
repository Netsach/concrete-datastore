# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Project
from django.test import override_settings
from django.contrib.gis.measure import D
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import Point, Polygon


@override_settings(DEBUG=True)
class PointFieldTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

    def test_success_create_with_valid_coordinates(self):
        url_projects = '/api/v1.1/project/'

        self.assertEqual(Project.objects.count(), 0)

        # CREATE a valid project and ensure that request is valid(201)
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                "gps_address": {
                    "latitude": 48.925_432_928_223,
                    "longitude": 2.555_056_530_762,
                },
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            format='json',
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)
        self.assertDictEqual(
            resp.json()['gps_address'],
            {"latitude": 48.925_432_928_223, "longitude": 2.555_056_530_762},
            msg=resp.content,
        )

    def test_success_filter_against_distance(self):
        url_projects = '/api/v1.1/project/'

        self.assertEqual(Project.objects.count(), 0)

        # CREATE a valid project and ensure that request is valid(201)
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                "gps_address": {
                    "latitude": 48.925_432_928_223,
                    "longitude": 2.555_056_530_762,
                },
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            format='json',
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        #: The project point and (32.0, 2.32) are separated from approximately 1883 km

        self.assertDictEqual(
            resp.json()['gps_address'],
            {"latitude": 48.925_432_928_223, "longitude": 2.555_056_530_762},
            msg=resp.content,
        )

        pnt = Point(2.32, 32.0)

        self.assertEqual(
            Project.objects.filter(
                gps_address__distance_lte=(pnt, D(km=1883))
            ).count(),
            1,
        )

        self.assertEqual(
            Project.objects.filter(
                gps_address__distance_lte=(pnt, D(km=1882))
            ).count(),
            0,
        )
        self.assertEqual(
            Project.objects.filter(
                gps_address__distance_lte=(pnt, D(km=1882.6554))
            ).count(),
            1,
        )

        #: The distance is in meter and it's longitude first
        resp = self.client.get(
            f'{url_projects}?gps_address__distance=1883000,2.32,32.0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.json()['objects_count'], 1, msg=resp.content)

        resp = self.client.get(
            f'{url_projects}?gps_address__distance=1882000,2.32,32.0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.json()['objects_count'], 0, msg=resp.content)

        #: Using distance filter with more that 3 values returns 400
        resp = self.client.get(
            f'{url_projects}?gps_address__distance=1,2,3,4',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        #: Using distance filter with less that 3 values returns 400
        resp = self.client.get(
            f'{url_projects}?gps_address__distance=1,2',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        #: Using `__distance` on a field that is not PointField will ignore
        #: the filter and returns all results
        resp = self.client.get(
            f'{url_projects}?name__distance=fakeName',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.data)
        self.assertEqual(resp.json()['objects_count'], 1, msg=resp.data)
