from rest_framework import serializers
from django.db.models import Avg, Count
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
    # Campos de rating: promedio y cantidad
    rating_average = serializers.SerializerMethodField(read_only=True)
    rating_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'userid', 'username', 'first_name', 'last_name', 'email', 'image_url',
            'gender', 'phone', 'age', 'role', 'is_online', 'is_available',
            'current_vehicle', 'current_vehicle_id',
            'rating_average', 'rating_count',
        )
        read_only_fields = ('userid', 'email', 'image_url')
    
    def get_current_vehicle(self, obj):
        """Retorna toda la información del vehículo"""
        if obj.current_vehicle:
            from vehicles.serializers import VehicleSerializer
            return VehicleSerializer(obj.current_vehicle).data
        return None
    
    def get_rating_average(self, obj):
        """Retorna el promedio de ratings recibidos (0-10), o null si no tiene."""
        result = obj.received_ratings.aggregate(avg=Avg('rating'))
        avg = result.get('avg')
        return round(avg, 2) if avg is not None else None
    
    def get_rating_count(self, obj):
        """Retorna la cantidad de ratings recibidos."""
        return obj.received_ratings.count()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importar aquí para evitar import circular
        from vehicles.models import Vehicle
        self.fields['current_vehicle_id'].queryset = Vehicle.objects.all()

class UserRatingSerializer(serializers.ModelSerializer):
    # Lectura: datos completos del usuario
    ratee = UserSerializer(read_only=True)
    rater = UserSerializer(read_only=True)
    # Escritura: solo el ID del usuario a calificar
    ratee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='ratee',
        write_only=True,
    )

    class Meta:
        model = UserRating
        fields = ('id', 'ratee', 'ratee_id', 'rater', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'rater', 'created_at')
    
    def create(self, validated_data):
        # Asignar automáticamente el rater desde el usuario autenticado
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['rater'] = request.user
        return super().create(validated_data)
