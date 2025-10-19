from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from decimal import Decimal

phone_validator = RegexValidator(
    regex=r'^(\+?\d{7,15}|[0-9\-\s]{7,20})$',
    message='Phone must be in format +1234567890 or 123-456-7890'
)

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True, null=True, validators=[phone_validator])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} <{self.email}>"

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.price})"

class Order(models.Model):
    customer = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    def calculate_total(self):
        total = sum([p.price for p in self.products.all()])
        self.total_amount = total
        return total

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
