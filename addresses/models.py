from django.db import models
import uuid

class Address(models.Model):
	addressId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	userId = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='addresses')
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=255, blank=True)
	type = models.CharField(max_length=20, choices=[('casa', 'Casa'), ('trabajo', 'Trabajo'), ('edificio', 'Edificio')])
	address = models.CharField(max_length=100)
	city = models.CharField(max_length=50)

	def __str__(self):
		return f"{self.address}, {self.city}"

