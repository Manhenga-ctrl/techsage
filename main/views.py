
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import EcoCashPayment
from decouple import config
from django.utils import timezone
import time
from .models import Package, Transaction,Voucher, EcoCashTransaction
from django.db import transaction
import csv
import io
from django.shortcuts import render
from .forms import VoucherUploadForm
from .models import Voucher
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count



ECOCASH_STATUS_URL=config("ECOCASH_STATUS_URL")
API_KEY=config("API_KEY")



payment_processor = EcoCashPayment()


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")  
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")






def get_voucher_by_package(package):
    """
    Fetch one unused voucher for a package and mark it as used.
    """
    

    with transaction.atomic():
        # Lock the first unused voucher for this package
        voucher = (
            Voucher.objects
            .select_for_update()       # lock row to prevent race conditions
            .filter(package=package, used=False)
            .first()
        )

        if voucher is None:
            return None

        # Mark voucher as used
        voucher.used = True
        voucher.save(update_fields=["used"])

        return voucher.voucher_code


# View to render payment page

def payment_page(request):

    packages= Package.objects.all()
    return render(request, "payment.html",{"packages": packages})

@csrf_exempt
def api_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)
    

    customer_msisdn = data.get("customerMsisdn")
    package = data.get("package")

   
    
    try:
        amount = Package.objects.values_list("amount", flat=True).get(package=package)
    except Package.DoesNotExist:
        amount = None
    
    
     
    customer_msisdn=str(customer_msisdn)
    customer_msisdn=customer_msisdn[1:]
    customer_msisdn="263"+str(customer_msisdn)
     
    if not customer_msisdn or not package:
        return JsonResponse({"error": "Missing fields"}, status=400)

    if not customer_msisdn.startswith("263") or len(customer_msisdn) != 12:
        return JsonResponse({"error": "Invalid phone number"}, status=400)

    result = payment_processor.make_payment(
        customer_msisdn,
        float(amount),
        package
    )

# Retrieve voucher based on package

    time.sleep(30)  
    

     
    try:
        status = Transaction.objects.values_list("status", flat=True).get(customer_msisdn=customer_msisdn)
    except Transaction.DoesNotExist:
        status = None
    
    

  # Wait for 30 seconds before checking status
    Voucher = get_voucher_by_package(package)
    

    if status=="SUCCESS":

            voucher = Voucher
        

    if status=="NULL" or status=="PENDING":
         voucher = "Payment is still being processed. Please wait."


    

    response_data = {
        "success": True,
        "message": "Payment request sent successfully",
        "voucher": voucher 
    }
    result = {**result, **response_data}
    return JsonResponse(result)



@login_required(login_url="login")
def upload_vouchers(request):
    message = ""
    packages= Package.objects.all()
    if request.method == "POST":
        form = VoucherUploadForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = request.FILES['csv_file']

            if not csv_file.name.endswith('.csv'):
                message = "Please upload a CSV file."
            else:
                data = csv_file.read().decode('utf-8')
                io_string = io.StringIO(data)
                reader = csv.DictReader(io_string)
                for row in reader:
                 Voucher.objects.get_or_create(
            voucher_code=row['VOUCHER_CODE'].strip(),
            defaults={
                'package': row['PACKAGES'].strip()
            }
        )

                message = "Vouchers uploaded successfully!"

    else:
        form = VoucherUploadForm()

    return render(request, 'form.html', {
        'form': form,
        'message': message
        
    })


login_required(login_url="login")
def package_list(request):
    packages= Package.objects.all()
    
    return render(request, 'package_list.html', {'packages': packages})



@login_required(login_url="login")
def voucher_list(request):
    packages= Package.objects.all()
    vouchers = Voucher.objects.all().order_by('used')  
    return render(request, 'voucher_list.html', {'vouchers': vouchers, 'packages': packages})

@login_required(login_url="login")
def delete_package(request, package_id):
    package = get_object_or_404(Package, id=package_id)
    package.delete()
    messages.success(request, f"Package {package.package} deleted successfully.")
    return redirect('package_list')

@login_required(login_url="login")
def delete_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    voucher.delete()
    messages.success(request, f"Voucher {voucher.voucher_code} deleted successfully.")
    return redirect('voucher_list')

@login_required(login_url="login")
def transaction_list(request):
    packages= Package.objects.all()
    transactions = EcoCashTransaction.objects.all().order_by('-timestamp')  
    return render(request, 'transaction_list.html', {'transactions': transactions, 'packages': packages})

@login_required(login_url="login")
def delete_transaction(request, source_reference):
    if request.method == "POST":
        transaction = get_object_or_404(
            EcoCashTransaction,
            source_reference=source_reference
        )
        transaction.delete()
        return redirect("transaction_list")

    # Prevent delete via GET
    return redirect("transaction_list")



@login_required(login_url="login")
def dashboard(request):
    
    return render(request, "dashboard.html")



def logout_view(request):
    logout(request)
    return redirect("login")



def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(request, "Account created successfully")
        return redirect('login')

    return render(request, 'register.html')


#Dashboard view
@login_required(login_url="login")
def dashboard(request):
    # Transactions
    total_transactions = Transaction.objects.count()
    total_revenue = Transaction.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    successful_transactions = Transaction.objects.filter(
        status__iexact='SUCCESS'
    ).count()

    failed_transactions = Transaction.objects.exclude(
        status__iexact='SUCCESS'
    ).count()

    # Vouchers
    total_vouchers = Voucher.objects.count()
    used_vouchers = Voucher.objects.filter(used=True).count()
    unused_vouchers = Voucher.objects.filter(used=False).count()

    # Packages
    total_packages = Package.objects.count()

    # Recent activity
    recent_transactions = Transaction.objects.order_by('-timestamp')[:10]
    recent_ecocash = EcoCashTransaction.objects.order_by('-timestamp')[:10]

    context = {
        'total_transactions': total_transactions,
        'successful_transactions': successful_transactions,
        'failed_transactions': failed_transactions,
        'total_revenue': total_revenue,

        'total_vouchers': total_vouchers,
        'used_vouchers': used_vouchers,
        'unused_vouchers': unused_vouchers,

        'total_packages': total_packages,

        'recent_transactions': recent_transactions,
        'recent_ecocash': recent_ecocash,
    }

    return render(request, 'dashboard.html', context)





@login_required(login_url="login")

def create_package(request):
    if request.method == "POST":
        package = request.POST.get('package')
        value = request.POST.get('value')
        amount = request.POST.get('amount')

        # Check if package already exists
        if Package.objects.filter(package=package).exists():
            messages.error(request, "Package already exists")
            return redirect('create_package')

        Package.objects.create(
            package=package,
            value=value,
            amount=amount,
            created_at=timezone.now()
        )

        messages.success(request, "Package created successfully")
        return redirect('package_list')  # change if needed

    return render(request, 'create_package.html')

