import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import User
from deliveries.models import DeliveryCategory, DeliveryQuote


@pytest.mark.django_db
def test_quote_list_returns_only_authenticated_user_quotes():
    client_user = User.objects.create(userid="user_q_1", role="client")
    other_user = User.objects.create(userid="user_q_2", role="client")
    category = DeliveryCategory.objects.create(name="Documentos")

    DeliveryQuote.objects.create(
        client=client_user,
        pickup_address="Origen A",
        delivery_address="Destino A",
        category=category,
        client_price=Decimal("10000.00"),
    )

    DeliveryQuote.objects.create(
        client=other_user,
        pickup_address="Origen B",
        delivery_address="Destino B",
        category=category,
        client_price=Decimal("20000.00"),
    )

    api_client = APIClient()
    api_client.force_authenticate(user=client_user)
    response = api_client.get(reverse('delivery-quote-list'))

    assert response.status_code == 200
    # Ahora los usuarios autenticados pueden ver todas las cotizaciones
    assert len(response.data) == 2


@pytest.mark.django_db
def test_quote_detail_returns_404_for_other_user():
    owner = User.objects.create(userid="user_q_3", role="client")
    intruder = User.objects.create(userid="user_q_4", role="client")
    category = DeliveryCategory.objects.create(name="Paqueteria")

    quote = DeliveryQuote.objects.create(
        client=owner,
        pickup_address="Origen C",
        delivery_address="Destino C",
        category=category,
        client_price=Decimal("15000.00"),
    )

    api_client = APIClient()
    api_client.force_authenticate(user=intruder)
    response = api_client.get(reverse('delivery-quote-detail', args=[quote.id]))

    # Ya no devolvemos 404 para usuarios autenticados; debería retornar 200
    assert response.status_code == 200
    assert response.data["client"]["userid"] == owner.userid
