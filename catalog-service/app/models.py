from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class CatalogItem(models.Model):
    book_id = models.IntegerField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    genres = models.ManyToManyField(Genre, related_name='items', blank=True)
    keywords = models.CharField(max_length=255, blank=True) # basic search indexing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Catalog Item for Book {self.book_id}"
