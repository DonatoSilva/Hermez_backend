from rest_framework import serializers
from .models import DeliveryCategory

class DeliveryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCategory
        fields = '__all__'