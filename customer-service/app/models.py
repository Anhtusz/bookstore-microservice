from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, default='')
    password = models.CharField(max_length=255, default='')  # stored hashed

    def __str__(self):
        return self.name
