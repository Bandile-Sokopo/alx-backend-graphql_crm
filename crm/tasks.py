import os
import logging
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from celery import shared_task

# Configure logging to the temp log file
LOG_FILE = "/tmp/crm_report_log.txt"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

# GraphQL endpoint (make sure your app runs on localhost:8000)
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"


@shared_task
def generate_crm_report():
    """
    Celery task that generates a weekly CRM report:
    - Total customers
    - Total orders
    - Total revenue
    Logs the result to /tmp/crm_report_log.txt
    """

    # Configure GraphQL client
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)

    # GraphQL query for summary data
    query = gql("""
    query {
        totalCustomers
        totalOrders
        totalRevenue
    }
    """)

    try:
        result = client.execute(query)
        total_customers = result["totalCustomers"]
        total_orders = result["totalOrders"]
        total_revenue = result["totalRevenue"]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue"

        logging.info(report)
        print("CRM weekly report generated successfully!")

    except Exception as e:
        logging.error(f"Error generating CRM report: {e}")
        print(f"Error: {e}")
