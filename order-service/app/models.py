from django.db import models

class Order(models.Model):
    STATUS_CHOICES = (
        ('WAITING_CONFIRMATION', 'Waiting Confirmation'),
        ('SHIPPING', 'Shipping'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    
    PAYMENT_METHODS = (
        ('BANK', 'Bank Transfer'),
        ('COD', 'Cash on Delivery'),
    )

    customer_id = models.IntegerField()
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='WAITING_CONFIRMATION')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='COD')
    
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_address = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Order {self.id} for Customer {self.customer_id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book_id = models.IntegerField()
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x Book {self.book_id} (Order {self.order.id})"
