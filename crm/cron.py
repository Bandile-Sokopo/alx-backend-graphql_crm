import logging
from datetime import datetime
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
except ImportError:
    Client = None

def log_crm_heartbeat():
    """Logs a heartbeat message every 5 minutes to confirm CRM health."""
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{timestamp} CRM is alive\n"

    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(log_message)

    if Client:
        try:
            transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", use_json=True)
            client = Client(transport=transport, fetch_schema_from_transport=False)
            query = gql("{ hello }")
            result = client.execute(query)
            with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
                log_file.write(f"{timestamp} GraphQL check: {result}\n")
        except Exception as e:
            with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
                log_file.write(f"{timestamp} GraphQL error: {e}\n")
import logging
from datetime import datetime

try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
except ImportError:
    Client = None

def log_crm_heartbeat():
    """Logs a heartbeat message every 5 minutes to confirm CRM health."""
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{timestamp} CRM is alive\n"

    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(log_message)

    if Client:
        try:
            transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", use_json=True)
            client = Client(transport=transport, fetch_schema_from_transport=False)
            query = gql("{ hello }")
            result = client.execute(query)
            with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
                log_file.write(f"{timestamp} GraphQL check: {result}\n")
        except Exception as e:
            with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
                log_file.write(f"{timestamp} GraphQL error: {e}\n")


def update_low_stock():
    """Executes GraphQL mutation to restock low-stock products and logs results."""
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_file = "/tmp/low_stock_updates_log.txt"

    try:
        # Set up the GraphQL client
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=False,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=False)

        # Define mutation
        mutation = gql("""
            mutation {
                updateLowStockProducts {
                    message
                    updatedProducts {
                        id
                        name
                        stock
                    }
                }
            }
        """)

        # Execute mutation
        result = client.execute(mutation)

        # Extract results
        message = result["updateLowStockProducts"]["message"]
        updated = result["updateLowStockProducts"]["updatedProducts"]

        with open(log_file, "a") as f:
            f.write(f"\n[{timestamp}] {message}\n")
            for p in updated:
                f.write(f" - {p['name']} restocked to {p['stock']} units\n")

    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"\n[{timestamp}] Error updating low stock: {e}\n")

