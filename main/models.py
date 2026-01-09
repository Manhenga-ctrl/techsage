from django.db import models

class EcoCashTransaction(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    customer_msisdn = models.CharField(max_length=12)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    package = models.CharField(max_length=50)  
    currency = models.CharField(max_length=10, default="USD")
    source_reference = models.CharField(max_length=64, unique=True)
    response = models.TextField()
    status_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.customer_msisdn} - {self.package}"




class Transaction(models.Model):
    customer_msisdn = models.CharField(max_length=12)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    package = models.CharField(max_length=50)  # e.g., 1GB, 5GB, 10GB, Unlimited
    currency = models.CharField(max_length=10, default="USD")
    source_reference = models.CharField(max_length=100, unique=True, primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50 ,default="NULL")


    def __str__(self):
        return f"{self.customer_msisdn} - {self.package} - {self.amount} {self.currency}"

class Voucher(models.Model):
    voucher_code = models.CharField(max_length=100, unique=True)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    package=models.CharField(max_length=50)

    def __str__(self):
        return self.voucher_code
    

# models.py

class Package(models.Model):
    package = models.CharField(max_length=50)      
    value = models.CharField(max_length=20)   
    amount = models.DecimalField(max_digits=8, decimal_places=2)  # price
    created_at = models.DateTimeField(null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.package} - {self.amount}"
