from rest_framework import serializers
from .models import Vehicle, VehicleType
from deliveries.serializers import DeliveryCategorySerializer


class VehicleTypeSerializer(serializers.ModelSerializer):
    delivery_categories = DeliveryCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = VehicleType
        fields = '__all__'


class VehicleSerializer(serializers.ModelSerializer):
    type = VehicleTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=VehicleType.objects.all(),
        source='type',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Vehicle
        fields = (
            'vehicleId',
            'userId',
            'type',
            'type_id',
            'brand',
            'model',
            'year',
            'licensePlate',
            'vin',
            'color',
            'driverLicenseStatus',
            'registrationCardStatus',
            'insurancePolicyStatus',
            'criminalRecordStatus',
            'isVerified',
            'verificationNotes',
        )
        read_only_fields = ('userId', 'vehicleId')