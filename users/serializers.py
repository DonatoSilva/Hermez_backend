from rest_framework import serializers
from .models import User, UserRating

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('userid', 'gender', 'phone', 'age', 'role', 'isActive')
        read_only_fields = ('userid',)

class UserRatingSerializer(serializers.ModelSerializer):
    ratee = UserSerializer(read_only=True)
    rater = UserSerializer(read_only=True)

    class Meta:
        model = UserRating
        fields = ('id', 'ratee', 'rater', 'rating', 'comment')
