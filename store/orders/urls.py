from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.payment_method, name='payment_method'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),
   
    path('payments/', views.payments, name='payments'),
    path('order_completed/', views.order_completed, name='order_complete'),


    path('access/token', views.getAccessToken, name='get_mpesa_access_token'),
    path('online/lipa', views.lipa_na_mpesa, name='lipa_na_mpesa'),
    path('query/', views.query_stk_push_status, name='query_stk_push_status'),



     # Register, confirmation, validation and callback urls
    path('c2b/register', views.register_urls, name="register_mpesa_validation"),
    path('c2b/confirmation', views.confirmation, name="confirmation"),
    path('c2b/validation', views.validation, name="validation"),
    path('c2b/callback', views.call_back, name="call_back"),


]