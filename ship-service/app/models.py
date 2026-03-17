from django.db import models

class Shipment(models.Model):
    STATUS_CHOICES = (
        ('PREPARING', 'Preparing'),
        ('SHIPPED', 'Shipped'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
    )

    order_id = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PREPARING')
    tracking_number = models.CharField(max_length=50, blank=True)
    shipping_label_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shipment {self.id} for Order {self.order_id} - {self.status}"
