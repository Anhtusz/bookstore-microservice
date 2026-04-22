from django.db import models


class Recommendation(models.Model):
    book_id = models.IntegerField(unique=True)
    recommended_book_ids = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendations for Book {self.book_id}"


class BehaviorEvent(models.Model):
    ACTION_CHOICES = [
        ('view', 'View'),
        ('click', 'Click'),
        ('add_to_cart', 'Add to Cart'),
        ('purchase', 'Purchase'),
        ('remove_cart', 'Remove Cart'),
        ('search', 'Search'),
        ('review', 'Review'),
    ]

    user_id = models.IntegerField(db_index=True)
    product_id = models.IntegerField(db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    session_id = models.CharField(max_length=64, blank=True, default='')
    synced_to_neo4j = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['user_id', 'timestamp']
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['synced_to_neo4j']),
        ]

    def __str__(self):
        return f"User {self.user_id} → {self.action} → Product {self.product_id}"
