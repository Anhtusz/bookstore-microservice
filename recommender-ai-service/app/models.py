from django.db import models

class Recommendation(models.Model):
    book_id = models.IntegerField(unique=True)
    recommended_book_ids = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendations for Book {self.book_id}"
