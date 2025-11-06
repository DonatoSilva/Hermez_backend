from rest_framework import serializers
from .models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'addressId',
            'userId',
            'name',
            'description',
            'address',
            'city',
            'type'
        )
        read_only_fields = ('userId',)
