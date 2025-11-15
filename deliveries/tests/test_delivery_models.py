import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from users.models import User
from deliveries.models import Delivery, DeliveryCategory
from vehicles.models import Vehicle, VehicleType


@pytest.mark.django_db
def test_create_delivery_defaults():
    client = User.objects.create(userid="user_d1", role="client")
    category = DeliveryCategory.objects.create(name="Paquetes")
    d = Delivery.objects.create(
        client=client,
        pickup_address="Bodega 1",
        delivery_address="Calle 90 # 10-10",
        category=category,
        final_price=Decimal("25000.00"),
    )
    assert d.status == "assigned"
    assert d.delivery_person is None


@pytest.mark.django_db
def test_delivery_vehicle_set_null_on_delete():
    client = User.objects.create(userid="user_d2", role="client")
    driver = User.objects.create(userid="user_d3", role="delivery")
    category = DeliveryCategory.objects.create(name="Comida")
    vt = VehicleType.objects.create(name="Moto")
    v = Vehicle.objects.create(
        userId=driver,
        type=vt,
        brand="Yamaha",
        model="FZ",
        year=2019,
        licensePlate="AAA111",
        vin="8HGCM82633A004359",
        color="Negro",
    )
    d = Delivery.objects.create(
        client=client,
        delivery_person=driver,
        pickup_address="Restaurante",
        delivery_address="Cliente",
        category=category,
        final_price=Decimal("18000.00"),
        vehicle=v,
    )
    v.delete()
    d.refresh_from_db()
    assert d.vehicle is None


@pytest.mark.django_db
def test_status_choices_validation():
    client = User.objects.create(userid="user_d4", role="client")
    category = DeliveryCategory.objects.create(name="Documentos")
    d = Delivery(
        client=client,
        pickup_address="Origen",
        delivery_address="Destino",
        category=category,
        final_price=Decimal("5000.00"),
        status="invalido",
    )
    with pytest.raises(ValidationError):
        d.full_clean()


@pytest.mark.django_db
def test_price_decimal_persistence():
    client = User.objects.create(userid="user_d5", role="client")
    category = DeliveryCategory.objects.create(name="Electrónicos")
    price = Decimal("123456.78")
    d = Delivery.objects.create(
        client=client,
        pickup_address="Almacén",
        delivery_address="Oficina",
        category=category,
        final_price=price,
    )
    assert d.final_price == price


@pytest.mark.django_db
def test_relationship_counts_client_vehicle():
    client = User.objects.create(userid="user_d6", role="client")
    driver = User.objects.create(userid="user_d7", role="delivery")
    category = DeliveryCategory.objects.create(name="Farmacia")
    vt = VehicleType.objects.create(name="Carro")
    v = Vehicle.objects.create(
        userId=driver,
        type=vt,
        brand="Toyota",
        model="Yaris",
        year=2020,
        licensePlate="BBB222",
        vin="9HGCM82633A004360",
        color="Rojo",
    )
    Delivery.objects.create(
        client=client,
        delivery_person=driver,
        pickup_address="Origen 1",
        delivery_address="Destino 1",
        category=category,
        final_price=Decimal("10000.00"),
        vehicle=v,
    )
    Delivery.objects.create(
        client=client,
        delivery_person=driver,
        pickup_address="Origen 2",
        delivery_address="Destino 2",
        category=category,
        final_price=Decimal("20000.00"),
        vehicle=v,
    )
    assert client.deliveries.count() == 2
    assert v.deliveries.count() == 2


@pytest.mark.django_db
def test_delivery_completed_at_set_on_delivered():
    client = User.objects.create(userid="user_d8", role="client")
    category = DeliveryCategory.objects.create(name="Mascotas")
    d = Delivery.objects.create(
        client=client,
        pickup_address="Origen",
        delivery_address="Destino",
        category=category,
        final_price=Decimal("30000.00"),
        status="assigned",
    )
    d.status = "delivered"
    d.save()
    assert d.completed_at is not None
    assert d.cancelled_at is None


@pytest.mark.django_db
def test_delivery_cancelled_at_set_on_cancelled():
    client = User.objects.create(userid="user_d9", role="client")
    category = DeliveryCategory.objects.create(name="Ropa")
    d = Delivery.objects.create(
        client=client,
        pickup_address="Origen",
        delivery_address="Destino",
        category=category,
        final_price=Decimal("15000.00"),
        status="assigned",
    )
    d.status = "cancelled"
    d.save()
    assert d.cancelled_at is not None
    assert d.completed_at is None