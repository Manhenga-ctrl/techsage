import uuid
import requests
from .models import EcoCashTransaction,Transaction
from decouple import config



ECOCASH_API_URL=config("ECOCASH_API_URL")
API_KEY=config("API_KEY")


class EcoCashPayment:

    def generate_reference(self):
        return str(uuid.uuid4())

    

    def make_payment(self, customer_msisdn, amount, package, currency="USD"):
        reference = self.generate_reference()

        payload = {
            "customerMsisdn": customer_msisdn,
            "amount": amount,
            "reason": package, 
            "currency": currency,
            "sourceReference": reference
        }

        headers = {
            "X-API-KEY": API_KEY,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                ECOCASH_API_URL,
                json=payload,
                headers=headers,
                timeout=60
            )

            EcoCashTransaction.objects.create(
                customer_msisdn=customer_msisdn,
                amount=amount,
                package=package,  # ✅ stored as package
                currency=currency,
                source_reference=reference,
                response=response.text,
                status_code=response.status_code
            )
            
        
            
            Transaction.objects.filter(customer_msisdn=customer_msisdn).delete()

# Create new transaction
            Transaction.objects.create(
    customer_msisdn=customer_msisdn,
    amount=amount,
    package=package,
    currency=currency,
    source_reference=reference
)





            return {
                "success": response.status_code == 200,
                "reference": reference
            }
    
        except Exception as e:
            EcoCashTransaction.objects.create(
                customer_msisdn=customer_msisdn,
                amount=amount,
                package=package,
                currency=currency,
                source_reference=reference,
                response=str(e),
                status_code="ERROR"
            )

            return {"success": False, "error": str(e)}
