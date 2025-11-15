import pytest
from django.db.utils import IntegrityError
from django.db.models.deletion import ProtectedError
from users.models import User
from vehicles.models import Vehicle, VehicleType


@pytest.mark.django_db
def test_create_vehicle_defaults():
    user = User.objects.create(userid="user_v1", role="delivery")
    vt = VehicleType.objects.create(name="Moto")
    v = Vehicle.objects.create(
        userId=user,
        type=vt,
        brand="Yamaha",
        model="FZ",
        year=2020,
        licensePlate="ABC123",
        vin="1HGCM82633A004352",
        color="Negro",
    )
    assert v.vehicleId is not None
    assert v.isVerified is False


@pytest.mark.django_db
def test_unique_license_plate():
    user = User.objects.create(userid="user_v2", role="delivery")
    vt = VehicleType.objects.create(name="Carro")
    Vehicle.objects.create(
        userId=user,
        type=vt,
        brand="Toyota",
        model="Corolla",
        year=2018,
        licensePlate="XYZ789",
        vin="2HGCM82633A004353",
        color="Blanco",
    )
    with pytest.raises(IntegrityError):
        Vehicle.objects.create(
            userId=user,
            type=vt,
            brand="Toyota",
            model="Yaris",
            year=2019,
            licensePlate="XYZ789",
            vin="3HGCM82633A004354",
            color="Rojo",
        )


@pytest.mark.django_db
def test_unique_vin():
    user = User.objects.create(userid="user_v3", role="delivery")
    vt = VehicleType.objects.create(name="Camioneta")
    Vehicle.objects.create(
        userId=user,
        type=vt,
        brand="Ford",
        model="Ranger",
        year=2021,
        licensePlate="DEF456",
        vin="4HGCM82633A004355",
        color="Azul",
    )
    with pytest.raises(IntegrityError):
        Vehicle.objects.create(
            userId=user,
            type=vt,
            brand="Ford",
            model="Bronco",
            year=2022,
            licensePlate="GHI012",
            vin="4HGCM82633A004355",
            color="Verde",
        )


@pytest.mark.django_db
def test_vehicle_type_protect_delete():
    user = User.objects.create(userid="user_v4", role="delivery")
    vt = VehicleType.objects.create(name="Bicicleta")
    Vehicle.objects.create(
        userId=user,
        type=vt,
        brand="GW",
        model="Alloy",
        year=2017,
        licensePlate="JKL345",
        vin="5HGCM82633A004356",
        color="Gris",
    )
    with pytest.raises(ProtectedError):
        vt.delete()


@pytest.mark.django_db
def test_user_vehicles_related_name():
    user = User.objects.create(userid="user_v5", role="delivery")
    vt = VehicleType.objects.create(name="Scooter")
    Vehicle.objects.create(
        userId=user,
        type=vt,
        brand="Honda",
        model="Dio",
        year=2016,
        licensePlate="MNO678",
        vin="6HGCM82633A004357",
        color="Amarillo",
    )
    Vehicle.objects.create(
        userId=user,
        type=vt,
        brand="Honda",
        model="Activa",
        year=2015,
        licensePlate="PQR901",
        vin="7HGCM82633A004358",
        color="Blanco",
    )
    assert user.vehicles.count() == 2