from rest_framework import serializers
from .models import User, UserRating

class UserSerializer(serializers.ModelSerializer):
    current_vehicle = serializers.StringRelatedField(read_only=True)
    current_vehicle_id = serializers.PrimaryKeyRelatedField(
        source='current_vehicle',
        queryset=User.objects.none(),  # Se actualizará en __init__
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = User
        fields = ('userid', 'gender', 'phone', 'age', 'role', 'is_online', 'is_available', 'current_vehicle', 'current_vehicle_id')
        read_only_fields = ('userid',)
    
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
        fields = ('id', 'ratee', 'rater', 'rating', 'comment')
