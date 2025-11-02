#!/bin/bash
count=$(./manage.py shell -c "from crm.models import Customer; \
from django.utils import timezone; import datetime; \
cutoff = timezone.now() - datetime.timedelta(days=365); \
deleted, _ = Customer.objects.filter(orders__isnull=True, \
last_order_date__lt=cutoff).delete(); print(deleted)")
echo "$(date '+%Y-%m-%d %H:%M:%S') Deleted $count inactive customers" \
>> /tmp/customer_cleanup_log.txt
