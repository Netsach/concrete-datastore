# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Project
from django.test import override_settings
from django.contrib.gis.measure import D
from django.contrib.gis.geos import GEOSGeometry


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
        pnt = GEOSGeometry('POINT(2.32 32.0)', srid=4326)

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
            f'{url_projects}?dist=1883000&point=2.32,32.0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.json()['objects_count'], 1, msg=resp.content)

        #: There is an approximation to compute degrees to meters so 1882 gives
        #: the project anyway
        #: https://github.com/openwisp/django-rest-framework-gis#distancetopointfilter
        #:  the errors at latitudes > 60 degrees are > 25%.
        resp = self.client.get(
            f'{url_projects}?dist=1882000&point=2.32,32.0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.json()['objects_count'], 1, msg=resp.content)
        #: With the API, the distance between the two points is approximately 1745 km
        #: There is a difference of ~130 km between the queryset filter and the API filtering
        resp = self.client.get(
            f'{url_projects}?dist=1750000&point=2.32,32.0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.json()['objects_count'], 1, msg=resp.content)

        resp = self.client.get(
            f'{url_projects}?dist=1740000&point=2.32,32.0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.json()['objects_count'], 0, msg=resp.content)
