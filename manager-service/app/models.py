from django.db import models

class StoreAnalytics(models.Model):
    date = models.DateField(auto_now_add=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_orders = models.IntegerField(default=0)

    def __str__(self):
        return f"Analytics for {self.date}"
