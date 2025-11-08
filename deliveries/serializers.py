from rest_framework import serializers
from .models import DeliveryCategory, DeliveryQuote, DeliveryOffer
from users.serializers import UserSerializer
from addresses.serializers import AddressSerializer
from users.models import User
from addresses.models import Address
from vehicles.models import VehicleType

class DeliveryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCategory
        fields = '__all__'


class DeliveryQuoteSerializer(serializers.ModelSerializer):
    """Serializer para cotizaciones de entrega con campos de solo lectura"""
    client = UserSerializer(read_only=True)
    pickup_address = AddressSerializer(read_only=True)
    delivery_address = AddressSerializer(read_only=True)
    category = serializers.StringRelatedField(read_only=True)
    
    # Campos para escritura
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='client', 
        write_only=True
    )
    pickup_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), 
        source='pickup_address', 
        write_only=True
    )
    delivery_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), 
        source='delivery_address', 
        write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryCategory.objects.all(), 
        source='category', 
        write_only=True
    )

    class Meta:
        model = DeliveryQuote
        fields = [
            'id', 'client', 'pickup_address', 'delivery_address', 'category',
            'description', 'estimated_weight', 'estimated_size', 'client_price',
            'status', 'expires_at', 'is_active', 'created_at', 'updated_at',
            'client_id', 'pickup_address_id', 'delivery_address_id', 'category_id'
        ]
        read_only_fields = ['status', 'is_active', 'created_at', 'updated_at']

    def validate(self, data):
        """Validación personalizada para la cotización"""
        if data.get('client_price') <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a cero")
        
        # Validar que pickup y delivery sean direcciones diferentes
        pickup_address = data.get('pickup_address')
        delivery_address = data.get('delivery_address')
        
        if pickup_address and delivery_address and pickup_address.id == delivery_address.id:
            raise serializers.ValidationError("Las direcciones de recogida y entrega deben ser diferentes")
        
        return data


class DeliverySerializer(serializers.ModelSerializer):
    """Serializer para domicilios permanentes"""
    client = UserSerializer(read_only=True)
    delivery_person = UserSerializer(read_only=True)
    pickup_address = AddressSerializer(read_only=True)
    delivery_address = AddressSerializer(read_only=True)
    category = serializers.StringRelatedField(read_only=True)
    
    # Campos para escritura
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='client', 
        write_only=True
    )
    delivery_person_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='delivery_person', 
        write_only=True,
        required=False
    )
    pickup_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), 
        source='pickup_address', 
        write_only=True
    )
    delivery_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), 
        source='delivery_address', 
        write_only=True
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryCategory.objects.all(), 
        source='category', 
        write_only=True
    )

    class Meta:
        model = Delivery
        fields = [
            'id', 'client', 'delivery_person', 'pickup_address', 'delivery_address', 'category',
            'description', 'estimated_weight', 'estimated_size', 'final_price', 'status',
            'created_at', 'updated_at', 'completed_at', 'cancelled_at',
            'client_id', 'delivery_person_id', 'pickup_address_id', 'delivery_address_id', 'category_id'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'completed_at', 'cancelled_at']

    def validate(self, data):
        """Validación personalizada para el domicilio"""
        if data.get('final_price') <= 0:
            raise serializers.ValidationError("El precio final debe ser mayor a cero")
        
        # Validar que pickup y delivery sean direcciones diferentes
        pickup_address = data.get('pickup_address')
        delivery_address = data.get('delivery_address')
        
        if pickup_address and delivery_address and pickup_address.id == delivery_address.id:
            raise serializers.ValidationError("Las direcciones de recogida y entrega deben ser diferentes")
        
        return data


class DeliveryHistorySerializer(serializers.ModelSerializer):
    """Serializer para historial de domicilios"""
    quote = DeliveryQuoteSerializer(read_only=True)
    delivery = DeliverySerializer(read_only=True)
    changed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = DeliveryHistory
        fields = [
            'id', 'quote', 'delivery', 'event_type', 'description', 
            'changed_by', 'created_at'
        ]
        read_only_fields = ['created_at']


class DeliveryOfferSerializer(serializers.ModelSerializer):
    """Serializer para ofertas de domiciliarios"""
    delivery_person = UserSerializer(read_only=True)
    quote = DeliveryQuoteSerializer(read_only=True)
    vehicle_type = serializers.StringRelatedField(read_only=True)
    
    # Campos para escritura
    delivery_person_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='delivery_person', 
        write_only=True
    )
    quote_id = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryQuote.objects.all(), 
        source='quote', 
        write_only=True
    )
    vehicle_type_id = serializers.PrimaryKeyRelatedField(
        queryset=VehicleType.objects.all(),
        source='vehicle_type',
        write_only=True,
        required=False
    )

    class Meta:
        model = DeliveryOffer
        fields = [
            'id', 'delivery_person', 'quote', 'proposed_price', 
            'estimated_delivery_time', 'vehicle_type', 'status',
            'expires_at', 'is_active', 'created_at', 'updated_at',
            'delivery_person_id', 'quote_id', 'vehicle_type_id'
        ]
        read_only_fields = ['status', 'is_active', 'created_at', 'updated_at']

    def validate(self, data):
        """Validación personalizada para la oferta"""
        if data.get('proposed_price') <= 0:
            raise serializers.ValidationError("El precio propuesto debe ser mayor a cero")
        
        # Validar que el domiciliario no sea el mismo cliente
        delivery_person = data.get('delivery_person')
        quote = data.get('quote')
        
        if delivery_person and quote and delivery_person.id == quote.client.id:
            raise serializers.ValidationError("El domiciliario no puede ser el mismo cliente")
        
        return data