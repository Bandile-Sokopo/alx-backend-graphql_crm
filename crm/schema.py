import graphene
from crm.models import Customer, Order, Product
from crm.models import Product

class Query(graphene.ObjectType):
    total_customers = graphene.Int()
    total_orders = graphene.Int()
    total_revenue = graphene.Float()

    def resolve_total_customers(root, info):
        return Customer.objects.count()

    def resolve_total_orders(root, info):
        return Order.objects.count()

    def resolve_total_revenue(root, info):
        return sum(order.total_amount for order in Order.objects.all())


class UpdateLowStockProducts(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(graphene.String)

    def mutate(self, info):
        updated = []
        low_stock_products = Product.objects.filter(stock__lt=10)

        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(f"{product.name} (new stock: {product.stock})")

        message = (
            f"Updated {len(updated)} low-stock products."
            if updated else "No low-stock products found."
        )

        return UpdateLowStockProducts(success=True, message=message, updated_products=updated)


class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
