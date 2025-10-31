from django.db import models
from django.utils.crypto import get_random_string
import uuid

class User(models.Model):
    userid = models.CharField(primary_key=True, editable=True, default=f"user_{get_random_string(12)}", blank=True)
    gender = models.CharField(max_length=6, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    phone = models.CharField(max_length=10)
    age = models.IntegerField()

    def __str__(self):
        return f"User {self.userid}"

class UserRating(models.Model):
    userRatingId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rating = models.IntegerField()
    comment = models.TextField()
    
    class Meta:
        db_table = 'user_rating'

    def __str__(self):
        return f"Rating {self.userRatingId} - Score: {self.rating}"
