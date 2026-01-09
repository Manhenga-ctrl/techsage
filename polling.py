import os
import django
import requests
import time
import logging
from django.db.models import Q
from decouple import config
from django.utils import timezone
from datetime import timedelta

# ----------------------
# Setup Django
# ----------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "techsage.settings") 
django.setup()

from main.models import Transaction 

MAX_AGE_SECONDS = 45

API_URL = config("API_URL")
API_KEY = config("API_KEY")
POLL_INTERVAL = 5  # seconds

HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------------
# DATABASE FUNCTIONS
# ----------------------
def get_pending_transactions():
    """
    Fetch all transactions not marked as SUCCESS
    """
    return list(
        Transaction.objects
        .filter(Q(status__isnull=True) | ~Q(status='SUCCESS'))
        .order_by('timestamp')
        .values_list('customer_msisdn', 'source_reference', 'package')
    )


def update_transaction_status(source_reference, status):
    """
    Update transaction status using source_reference
    """
    transaction = Transaction.objects.filter(source_reference=source_reference).first()
    
    
    if not transaction:
        logging.warning("No transaction found for source_reference: %s", source_reference)
        return

    transaction.status = status
    transaction.save()
    logging.info("Updated transaction %s → %s", source_reference, status)


# ----------------------
# ECOCASH STATUS CHECK
# ----------------------
def check_ecocash_status(transaction):
    customer_msisdn, source_reference, package = transaction

    payload = {
        "sourceMobileNumber": customer_msisdn,
        "sourceReference": source_reference
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logging.error("API error for %s: %s", source_reference, e)
        return

    status = data.get("status")

    if status == "SUCCESS":
        logging.info("SUCCESS: %s", source_reference)

        if package == "1GB":
            logging.info("Deliver BASIC package")
        elif package == "5GB":
            logging.info("Deliver STANDARD package")
        elif package == "unlimited":
            logging.info("Deliver PREMIUM package")
        else:
            logging.warning("Unknown package: %s", package)

        update_transaction_status(source_reference, "SUCCESS")

    elif status == "PENDING":
        logging.info("PENDING: %s", source_reference)

    else:
        logging.warning("FAILED/UNKNOWN: %s → %s", source_reference, status)
        update_transaction_status(source_reference, status or "FAILED")





def delete_expired_transactions():
    """
    Delete transactions older than 40 seconds
    that are NOT SUCCESS
    """
    expiry_time = timezone.now() - timedelta(seconds=MAX_AGE_SECONDS)

    expired = Transaction.objects.filter(
        Q(status__isnull=True) | ~Q(status='SUCCESS'),
        timestamp__lte=expiry_time
    )

    count = expired.count()
    if count > 0:
        expired.delete()
        logging.warning("Deleted %s expired transactions", count)



# ----------------------
# POLLING LOOP
# ----------------------
if __name__ == "__main__":
    logging.info("EcoCash polling started (every %s seconds)", POLL_INTERVAL)

    while True:
        try:
            delete_expired_transactions() 
            pending_transactions = get_pending_transactions()

            if not pending_transactions:
                logging.info("No pending transactions")
            else:
                for tx in pending_transactions:
                    check_ecocash_status(tx)

        except Exception as e:
            logging.error("Polling error: %s", e)

        time.sleep(POLL_INTERVAL)
