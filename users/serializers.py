from rest_framework import serializers
from .models import User, UserRating

class UserSerializer(serializers.ModelSerializer):
    current_vehicle = serializers.SerializerMethodField(read_only=True)
    current_vehicle_id = serializers.PrimaryKeyRelatedField(
        source='current_vehicle',
        queryset=User.objects.none(),  # Se actualizará en __init__
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = User
        fields = ('userid', 'username', 'first_name', 'last_name', 'email', 'image_url', 'gender', 'phone', 'age', 'role', 'is_online', 'is_available', 'current_vehicle', 'current_vehicle_id')
        read_only_fields = ('userid', 'email', 'image_url')
    
    def get_current_vehicle(self, obj):
        """Retorna toda la información del vehículo"""
        if obj.current_vehicle:
            from vehicles.serializers import VehicleSerializer
            return VehicleSerializer(obj.current_vehicle).data
        return None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importar aquí para evitar import circular
        from vehicles.models import Vehicle
        self.fields['current_vehicle_id'].queryset = Vehicle.objects.all()

class UserRatingSerializer(serializers.ModelSerializer):
    ratee = UserSerializer(read_only=True)
    rater = UserSerializer(read_only=True)

    class Meta:
        model = UserRating
        fields = ('id', 'ratee', 'rater', 'rating', 'comment', 'created_at')
