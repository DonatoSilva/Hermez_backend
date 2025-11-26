from django.urls import reverse
from rest_framework.test import APITestCase
from users.models import User
from deliveries.models import Delivery, DeliveryCategory
from rest_framework import status
import uuid
from django.utils import timezone
import datetime

class DeliveryFiltersTest(APITestCase):
    def setUp(self):
        # usuarios
        self.client_user = User.objects.create(userid='client1', role='client')
        self.driver_user = User.objects.create(userid='driver1', role='delivery')
        self.other_user = User.objects.create(userid='client2', role='client')

        # categoría mínima
        self.cat = DeliveryCategory.objects.create(name='test', description='test')

        # deliveries:
        # - one created by client_user, assigned to driver_user, created now
        # - one created by client_user, assigned to driver_user, created in previous month
        # - one created by other_user, assigned to driver_user, created now
        now = timezone.now()
        last_month = (now - datetime.timedelta(days=40))

        self.d1 = Delivery.objects.create(
            client=self.client_user,
            delivery_person=self.driver_user,
            pickup_address='a',
            delivery_address='b',
            category=self.cat,
            final_price=100,
        )
        self.d1.created_at = now
        self.d1.save(update_fields=['created_at'])

        self.d2 = Delivery.objects.create(
            client=self.client_user,
            delivery_person=self.driver_user,
            pickup_address='c',
            delivery_address='d',
            category=self.cat,
            final_price=50,
        )
        self.d2.created_at = last_month
        self.d2.save(update_fields=['created_at'])

        self.d3 = Delivery.objects.create(
            client=self.other_user,
            delivery_person=self.driver_user,
            pickup_address='x',
            delivery_address='y',
            category=self.cat,
            final_price=20,
        )
        self.d3.created_at = now
        self.d3.save(update_fields=['created_at'])

        # endpoints
        self.list_url = '/deliveries/api/'

    def auth(self, user):
        # Simple auth: force authenticate by setting client.force_authenticate
        # but APITestCase client has force_authenticate on APIClient instance
        self.client.force_authenticate(user)

    def test_default_lists_client_deliveries(self):
        self.auth(self.client_user)
        resp = self.client.get(self.list_url)
        assert resp.status_code == status.HTTP_200_OK
        ids = {item['id'] for item in resp.json()}
        assert str(self.d1.id) in ids
        assert str(self.d2.id) in ids
        assert str(self.d3.id) not in ids

    def test_filter_by_delivery_person(self):
        self.auth(self.driver_user)
        resp = self.client.get(self.list_url + '?filter_by=delivery_person')
        assert resp.status_code == status.HTTP_200_OK
        ids = {item['id'] for item in resp.json()}
        # driver assigned to d1,d2,d3
        assert str(self.d1.id) in ids
        assert str(self.d2.id) in ids
        assert str(self.d3.id) in ids

    def test_filter_by_month_defaults_current_year(self):
        self.auth(self.client_user)
        now = timezone.now()
        resp = self.client.get(f"{self.list_url}?month={now.month}")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item['id'] for item in resp.json()}
        # only d1 is in current month for client_user
        assert str(self.d1.id) in ids
        assert str(self.d2.id) not in ids

    def test_filter_by_month_and_year(self):
        self.auth(self.client_user)
        # pick month/year of d2 (last_month)
        lm = self.d2.created_at
        resp = self.client.get(f"{self.list_url}?month={lm.month}&year={lm.year}")
        assert resp.status_code == status.HTTP_200_OK
        ids = {item['id'] for item in resp.json()}
        assert str(self.d2.id) in ids
        assert str(self.d1.id) not in ids

    def test_driver_can_access_detail_history(self):
        # access /<pk>/history/ as driver (delivery_person)
        url = f"/deliveries/api/{self.d1.id}/history/"
        self.auth(self.driver_user)
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.json()
        assert 'delivery' in payload and 'history' in payload

    def test_non_related_user_cannot_access_other_detail(self):
        # other_user (not client nor driver) cannot access client_user's delivery detail
        url = f"/deliveries/api/{self.d1.id}/"
        self.auth(self.other_user)
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
