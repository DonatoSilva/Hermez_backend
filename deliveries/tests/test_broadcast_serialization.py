import pytest
import asyncio
import uuid
from rest_framework.test import APIClient
from users.models import User
from deliveries.models import DeliveryCategory, DeliveryQuote, DeliveryOffer

@pytest.mark.django_db
def test_reject_offer_broadcasts_serializable_payload(monkeypatch):
    # Crear datos base
    client_user = User.objects.create(userid="user_client", role="client")
    driver = User.objects.create(userid="user_driver", role="delivery")
    category = DeliveryCategory.objects.create(name="TestCat")

    quote = DeliveryQuote.objects.create(
        client=client_user,
        pickup_address="Origen",
        delivery_address="Destino",
        category=category,
        client_price=10000.00,
    )

    offer = DeliveryOffer.objects.create(
        delivery_person=driver,
        quote=quote,
        proposed_price=12000.00,
    )

    captured = []

    class FakeChannelLayer:
        async def group_send(self, group_name, message):
            # Store a deep copy of message for inspection
            captured.append((group_name, message))
            return None

    # Patch get_channel_layer used inside deliveries.services.expiration
    monkeypatch.setattr('deliveries.services.expiration.get_channel_layer', lambda: FakeChannelLayer())

    api_client = APIClient()
    api_client.force_authenticate(user=client_user)

    url = f"/deliveries/api/offers/{offer.id}/reject/"
    resp = api_client.post(url, {}, format='json')

    assert resp.status_code == 200
    # We expect at least one broadcast call captured
    assert len(captured) >= 1

    # Helper: assert no UUID objects remain in payload
    def assert_no_uuid(obj):
        if isinstance(obj, uuid.UUID):
            pytest.fail("Found raw UUID in payload")
        if isinstance(obj, dict):
            for v in obj.values():
                assert_no_uuid(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                assert_no_uuid(v)

    # Inspect messages
    for group_name, message in captured:
        # message should be a dict with 'type' and 'data'
        assert isinstance(message, dict)
        # check data portion
        data = message.get('data')
        assert_no_uuid(data)
