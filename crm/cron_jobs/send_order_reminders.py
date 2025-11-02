#!/usr/bin/env python3
import logging
import os
from datetime import datetime, timedelta

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Setup logging
logging.basicConfig(
    filename="/tmp/order_reminders_log.txt",
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

# GraphQL client setup
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    use_json=True,
)
client = Client(transport=transport, fetch_schema_from_transport=True)

# Build the query for orders in the last 7 days
query = gql("""
query GetRecentOrders($since: DateTime!) {
  orders(filter: {orderDate_gte: $since}) {
    id
    customer {
      email
    }
  }
}
""")

def main():
    since_dt = datetime.utcnow() - timedelta(days=7)
    variables = {"since": since_dt.isoformat()}
    result = client.execute(query, variable_values=variables)
    orders = result.get("orders", [])

    for order in orders:
        order_id = order["id"]
        email = order["customer"]["email"]
        logging.info(f"Reminder for order {order_id}, customer {email}")

    print("Order reminders processed!")

if __name__ == "__main__":
    main()
