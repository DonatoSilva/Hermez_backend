import pytest
from django.core.exceptions import ValidationError
from users.models import User
from addresses.models import Address


@pytest.mark.django_db
def test_create_address_defaults():
    user = User.objects.create(userid="user_a1", role="client")
    addr = Address.objects.create(
        userId=user,
        name="Casa",
        description="",
        type="casa",
        address="Calle 123",
        city="Bogotá",
    )
    assert addr.addressId is not None
    assert addr.isFavorite is False


@pytest.mark.django_db
def test_address_type_choices_validation():
    user = User.objects.create(userid="user_a2", role="client")
    addr = Address(
        userId=user,
        name="Oficina",
        description="",
        type="invalido",
        address="Av 45",
        city="Medellín",
    )
    with pytest.raises(ValidationError):
        addr.full_clean()


@pytest.mark.django_db
def test_favorite_toggle_and_filter():
    user = User.objects.create(userid="user_a3", role="client")
    Address.objects.create(
        userId=user,
        name="Casa",
        description="",
        type="casa",
        address="Calle 1",
        city="Cali",
        isFavorite=True,
    )
    Address.objects.create(
        userId=user,
        name="Trabajo",
        description="",
        type="trabajo",
        address="Calle 2",
        city="Cali",
        isFavorite=False,
    )
    assert Address.objects.filter(userId=user, isFavorite=True).count() == 1


@pytest.mark.django_db
def test_user_addresses_related_name():
    user = User.objects.create(userid="user_a4", role="client")
    Address.objects.create(
        userId=user,
        name="Casa",
        description="",
        type="casa",
        address="Calle A",
        city="Bogotá",
    )
    Address.objects.create(
        userId=user,
        name="Trabajo",
        description="",
        type="trabajo",
        address="Calle B",
        city="Bogotá",
    )
    assert user.addresses.count() == 2