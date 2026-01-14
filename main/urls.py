from django.urls import path
from . import views

urlpatterns = [
    path("account/", views.account, name="account"),
    path("", views.payment_page),
    path("login/", views.login_view, name="login"),
    path("api/payment/", views.api_payment),
      path('upload-vouchers/', views.upload_vouchers, name='upload_vouchers'),
      path('dashboard/', views.dashboard, name='dashboard'),
      path("logout/", views.logout_view, name="logout"),
      path("register/", views.register, name="register"),
        path('packages/', views.package_list, name='package_list'),
        path('delete-package/<int:package_id>/', views.delete_package, name='delete_package'),
      path('vouchers/', views.voucher_list, name='voucher_list'),
       path('delete-voucher/<int:voucher_id>/', views.delete_voucher, name='delete_voucher'),
        path('packages/create/', views.create_package, name='create_package'),
       path('transactions/', views.transaction_list, name='transaction_list'),
       path('delete-transaction/<str:source_reference>/', views.delete_transaction, name='delete_transaction')]