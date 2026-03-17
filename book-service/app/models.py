from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, null=True, default="")

    @property
    def stock_status(self):
        return "In Stock" if self.stock > 0 else "Out of Stock"

    def __str__(self):
        return self.title