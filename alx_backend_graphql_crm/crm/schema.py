import graphene
from graphene_django import DjangoObjectType
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
import re
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import F

from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


from .models import Customer, Product, Order


# -----------------------
# GraphQL Object Types
# -----------------------

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")


# -----------------------
# Helper validation functions
# -----------------------

def validate_phone_number(phone):
    """Ensure phone number matches +1234567890 or 123-456-7890."""
    if not phone:
        return
    pattern = r'^(\+?\d{7,15}|[0-9\-\s]{7,20})$'
    if not re.match(pattern, phone):
        raise ValueError("Invalid phone number format. Use +1234567890 or 123-456-7890.")


def validate_unique_email(email):
    """Ensure email format is valid and unique."""
    try:
        validate_email(email)
    except DjangoValidationError:
        raise ValueError("Invalid email format.")
    if Customer.objects.filter(email__iexact=email).exists():
        raise ValueError("Email already exists.")


# -----------------------
# CreateCustomer Mutation
# -----------------------

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, name, email, phone=None):
        try:
            validate_unique_email(email)
            validate_phone_number(phone)
            customer = Customer.objects.create(name=name.strip(), email=email.strip(), phone=phone)
            return CreateCustomer(customer=customer, message="Customer created successfully!", success=True)
        except ValueError as e:
            return CreateCustomer(message=str(e), success=False)
        except IntegrityError:
            return CreateCustomer(message="Email already exists.", success=False)


# -----------------------
# BulkCreateCustomers Mutation
# -----------------------

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(CustomerInput, required=True)

    created_customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success = graphene.Boolean()

    def mutate(self, info, customers):
        created_customers = []
        errors = []

        with transaction.atomic():
            for index, data in enumerate(customers):
                savepoint = transaction.savepoint()
                try:
                    validate_unique_email(data.email)
                    validate_phone_number(data.phone)
                    customer = Customer.objects.create(
                        name=data.name.strip(),
                        email=data.email.strip(),
                        phone=(data.phone or "").strip()
                    )
                    created_customers.append(customer)
                    transaction.savepoint_commit(savepoint)
                except Exception as e:
                    errors.append(f"Record {index + 1}: {str(e)}")
                    transaction.savepoint_rollback(savepoint)

        success = len(errors) == 0
        return BulkCreateCustomers(created_customers=created_customers, errors=errors, success=success)


# -----------------------
# CreateProduct Mutation
# -----------------------

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, name, price, stock=0):
        try:
            if price <= 0:
                raise ValueError("Price must be a positive value.")
            if stock < 0:
                raise ValueError("Stock cannot be negative.")

            product = Product.objects.create(
                name=name.strip(),
                price=Decimal(str(price)),
                stock=stock
            )
            return CreateProduct(product=product, message="Product created successfully!", success=True)
        except ValueError as e:
            return CreateProduct(message=str(e), success=False)
        except Exception as e:
            return CreateProduct(message=f"Error creating product: {e}", success=False)


# -----------------------
# CreateOrder Mutation
# -----------------------

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            # Validate customer
            try:
                customer = Customer.objects.get(pk=customer_id)
            except Customer.DoesNotExist:
                raise ValueError("Invalid customer ID.")

            if not product_ids:
                raise ValueError("At least one product ID must be provided.")

            # Validate products
            products = []
            invalid_ids = []
            for pid in product_ids:
                try:
                    products.append(Product.objects.get(pk=pid))
                except Product.DoesNotExist:
                    invalid_ids.append(pid)

            if invalid_ids:
                raise ValueError(f"Invalid product IDs: {invalid_ids}")

            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    order_date=order_date or timezone.now()
                )
                order.products.set(products)
                total_amount = sum(p.price for p in products)
                order.total_amount = total_amount
                order.save()

            return CreateOrder(order=order, message="Order created successfully!", success=True)

        except ValueError as e:
            return CreateOrder(message=str(e), success=False)
        except Exception as e:
            return CreateOrder(message=f"Error creating order: {str(e)}", success=False)


# -----------------------
# Root Query and Mutation
# -----------------------

class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.prefetch_related('products').all()


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# -----------------------
# Object Types (Relay-compatible)
# -----------------------

class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# -----------------------
# Enhanced Query Class
# -----------------------

class Query(graphene.ObjectType):
    customer = graphene.relay.Node.Field(CustomerNode)
    all_customers = DjangoFilterConnectionField(CustomerNode, order_by=graphene.String())

    product = graphene.relay.Node.Field(ProductNode)
    all_products = DjangoFilterConnectionField(ProductNode, order_by=graphene.String())

    order = graphene.relay.Node.Field(OrderNode)
    all_orders = DjangoFilterConnectionField(OrderNode, order_by=graphene.String())

    def resolve_all_customers(self, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            try:
                qs = qs.order_by(order_by)
            except Exception:
                pass
        return qs

    def resolve_all_products(self, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            try:
                qs = qs.order_by(order_by)
            except Exception:
                pass
        return qs

    def resolve_all_orders(self, info, order_by=None, **kwargs):
        qs = Order.objects.all().prefetch_related("products", "customer")
        if order_by:
            try:
                qs = qs.order_by(order_by)
            except Exception:
                pass
        return qs
