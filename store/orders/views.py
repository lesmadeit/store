import json
import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse
from django.contrib import messages


from cart.models import CartItem, Cart
from cart.views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from shop.models import Product

import requests
from requests.auth import HTTPBasicAuth
import json
from .mpesa_credentials import MpesaAccessToken, LipanaMpesaPassword
from django.views.decorators.csrf import csrf_exempt
from . models import MpesaPayment


@login_required(login_url='accounts:login')
def payment_method(request):
    return render(request, 'shop/orders/payment_method.html')


@login_required(login_url= 'accounts:login')
def checkout(request, total_price=0, quantity=0, cart_items=None):
    
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total_price += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        total = total_price
        
    except ObjectDoesNotExist:
        pass #just ignore

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user #Assign the current user
            order.total_price = total_price
            order.save()
            return redirect("orders:payment") #Redirect to the payment page
    else:
        form = OrderForm()

    
    context = {
        'total_price': total_price,
        'quantity': quantity,
        'cart_items': cart_items,
        'form': form, #pass form to the template
    }
    return render(request, 'shop/orders/checkout/checkout.html', context)


@login_required(login_url= 'accounts:login')
def payment(request, total=0, quantity=0):
    current_user = request.user
    
    # if the cart count less than 0 , redirect to shop page 
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0 :
        return redirect('shop:shop')
    
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    

    

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # shop all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.county = form.cleaned_data['county']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = total
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()





            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'order_total': total,
            }
            return render(request, 'shop/orders/checkout/payment_received_email.html', context)
        else:
            messages.error(request, "Please correct the errors below and try again.")
            return render(request, 'shop/orders/checkout/checkout.html', {'form': form, 'cart_items': cart_items, 'order_total': total})
    
    else:
        return redirect('shop:shop')
    
'''def confirm_payment(request):
    return render(request, 'shop/orders/checkout/payment_received_email.html')'''

    

def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        status = body['status'],
        amount_paid = order.order_total,
    )

    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()
    
    #move the cart item to OrderProduct table
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # add variation to OrderProduct table
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()


    

    # Send order number and transaction id back to sendDate method via JavaResponse
    data = {
        'order_number': order.order_number,
        'transID' : payment.payment_id,
    }
    return JsonResponse(data)


def order_completed(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)


        payment = Payment.objects.filter(payment_id=transID).latest('id')

        subtotall = 0
        for i in ordered_products:
            subtotall += i.product_price * i.quantity
        subtotal = round(subtotall, 2)
        

        context = {
            'order':order,
            'ordered_products': ordered_products,
            'order_number' : order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'shop/orders/order_completed/order_completed.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('shop:shop')
    

checkout_request_id_global = None

def getAccessToken(request):
    consumer_key = 'OVfR5jHsG9ydGzsKJDoGPfLzrCJauKo2zjcthScvojQrnx5U'
    consumer_secret = 'QuGHi7jj1pVRieav3G3Tk6dEjLtA3uShK9oGnirhr9vxYwuN7BAeqE6nX11kHBau'
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    mpesa_access_token = json.loads(r.text)
    validated_mpesa_access_token = mpesa_access_token['access_token']
    
    return HttpResponse(validated_mpesa_access_token)


checkout_request_id_global = None
@csrf_exempt
def lipa_na_mpesa(request):
    global checkout_request_id_global

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = data.get("amount")
            phone = data.get("phone")

            if not amount or not phone:
                return JsonResponse({"error": "Phone number and amount are required"}, status=400)



            access_token = MpesaAccessToken.validated_mpesa_access_token
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            headers = {"Authorization": "Bearer %s" % access_token}
            payload = {
                "BusinessShortCode": LipanaMpesaPassword.business_short_code,
                "Password": LipanaMpesaPassword.decode_password,
                "Timestamp": LipanaMpesaPassword.timestamp,
                "TransactionType": "CustomerPayBillOnline", #CustomerBuyGoodsOnline(for buy goods)
                "Amount": amount,
                "PartyA": phone,
                "PartyB": LipanaMpesaPassword.business_short_code,
                "PhoneNumber": phone,
                "CallBackURL": "https://8155579dab07.ngrok-free.app/orders/query/",
                "AccountReference": "Leslie",
                "TransactionDesc": "Testing stk push"
            }

            response = requests.post(api_url, json=payload, headers=headers)
            response_data = response.json()  # Convert response text to a dictionary
            checkout_request_id_global = response_data.get("CheckoutRequestID")
            print("CheckoutRequestID:", checkout_request_id_global)
            return JsonResponse({"message": "STK Push initiated", "CheckoutRequestID": checkout_request_id_global}) 
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    return HttpResponse("Invalid request method", status=400)


#call back that i used
@csrf_exempt
def query_stk_push_status(request):
    print("Request URL:", request.get_full_path())
    print("Request Body:", request.body)
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse JSON request
            checkout_request_id = data.get("checkout")  # Frontend polling
            if not checkout_request_id:
                # Check for M-Pesa callback format
                if "Body" in data and "stkCallback" in data["Body"]:
                    callback_data = data["Body"]["stkCallback"]
                    print("M-Pesa Callback Data:", callback_data)
                    # Process callback if needed (e.g., save to database)
                    return HttpResponse("Callback received", status=200)
                print("Error: No CheckoutRequestID provided in request body")
                return HttpResponse("No CheckoutRequestID provided.", status=400)

            access_token = MpesaAccessToken.validated_mpesa_access_token
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer %s" % access_token
            }
            payload = {
                "BusinessShortCode": LipanaMpesaPassword.business_short_code,
                "Password": LipanaMpesaPassword.decode_password,
                "Timestamp": LipanaMpesaPassword.timestamp,
                "CheckoutRequestID": checkout_request_id,
            }
            api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
            response = requests.post(api_url, json=payload, headers=headers)
            print("M-Pesa API Response Status:", response.status_code)
            print("M-Pesa API Response Text:", response.text)
            response_data = response.json()
            print("Query Response:", response_data)
            return HttpResponse(json.dumps(response_data, indent=4), content_type="application/json")
        except json.JSONDecodeError as e:
            print("JSON Decode Error:", str(e))
            return HttpResponse("Invalid JSON format", status=400)
        except Exception as e:
            print("Unexpected Error:", str(e))
            return HttpResponse(f"Server error: {str(e)}", status=500)
    else:
        print("Invalid request method:", request.method)
        return HttpResponse("Invalid request method", status=405)
@csrf_exempt
def register_urls(request):
    access_token = MpesaAccessToken.validated_mpesa_access_token
    api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    headers = {"Authorization": "Bearer %s" % access_token}
    options = {"ShortCode": LipanaMpesaPassword.business_short_code,
               "ResponseType": "Completed",
               "ConfirmationURL": "https://3981-154-159-252-126.ngrok-free.app/orders/c2b/confirmation",
               "ValidationURL": "https://3981-154-159-252-126.ngrok-free.app/orders/c2b/validation"}
    response = requests.post(api_url, json=options, headers=headers)

    return HttpResponse(response.text)



@csrf_exempt
def call_back(request):
    """Handles the STK Push callback response from Safaricom."""

    # Decode the incoming JSON request body
    mpesa_body = request.body.decode('utf-8')
    

    try:
         # Convert JSON string into a dictionary
        mpesa_response = json.loads(mpesa_body)

        # Extract the ResultCode and CheckoutRequestID
        result_code = mpesa_response['Body']['stkCallback']['ResultCode']
        checkout_request_id = mpesa_response['Body']['stkCallback']['CheckoutRequestID']
        result_desc = mpesa_response['Body']['stkCallback']['ResultDesc']

        # If transaction was successful (ResultCode == 0)
        if result_code == 0:
            # Extract necessary transaction details
            callback_metadata = mpesa_response['Body']['stkCallback']['CallbackMetadata']['Item']

            # Initialize variables
            amount = transaction_id = phone_number = None

            # Iterate through the callback metadata to extract values
            for item in callback_metadata:
                if item['Name'] == "Amount":
                    amount = item['Value']
                elif item['Name'] == "MpesaReceiptNumber":
                    transaction_id = item['Value']
                elif item['Name'] == "PhoneNumber":
                    phone_number = item['Value']

            # Save transaction details to database
            payment = MpesaPayment(
                phone_number=phone_number,
                amount=amount,
                description=transaction_id,
                reference=checkout_request_id,
                type="STK Push Payment",
            )
            payment.save()

            response_message = "Payment processed successfully."
        else:
            response_message = f"Transaction failed: {result_desc}"

    except Exception as e:
        # Handle any unexpected errors
        response_message = f"Error processing callback: {str(e)}"
        result_code = 1  # Indicating failure

    # Respond to Safaricom with the appropriate response
    return JsonResponse({
        "ResultCode": result_code,
        "ResultDesc": response_message
    })



@csrf_exempt
def validation(request):
    """Validates the STK Push transaction response and returns an appropriate message."""

    try:
        # Decode and parse the incoming JSON request body
        mpesa_body = request.body.decode('utf-8')
        mpesa_response = json.loads(mpesa_body)

        # Extract the response code and result code
        response_code = mpesa_response.get("ResponseCode", 1)  # Default to 1 if missing
        result_code = mpesa_response.get("ResultCode", None)
        result_desc = mpesa_response.get("ResultDesc", "")

        # Initialize default response message
        message = "Transaction validation failed."

        if response_code == 0:
            # Check the ResultCode
            if result_code == 1037:
                message = "Timeout: User cannot be reached."
            elif result_code == 1032:
                # Check the Result Description
                if result_desc == "The service request is processed successfully.":
                    message = result_desc
                else:
                    message = "Request cancelled by user."
        else:
            response_code = 1  # If response_code is not 0, set it to 1

    except Exception as e:
        message = f"Error processing validation: {str(e)}"
        response_code = 1  # Ensure failure is indicated

    # Return JSON response to Safaricom
    return JsonResponse({
        "ResultCode": response_code,
        "ResultDesc": message
    })



@csrf_exempt

def confirmation(request):
    mpesa_body = request.body.decode('utf-8')
    mpesa_payment = json.loads(mpesa_body)

    payment = MpesaPayment(
        first_name=mpesa_payment['FirstName'],
        last_name=mpesa_payment['LastName'],
        middle_name=mpesa_payment['MiddleName'],
        description=mpesa_payment['TransID'],
        phone_number=mpesa_payment['MSISDN'],
        amount=mpesa_payment['TransAmount'],
        reference=mpesa_payment['BillRefNumber'],
        organization_balance=mpesa_payment['OrgAccountBalance'],
        type=mpesa_payment['TransactionType'],
    )
    payment.save()

    context = {
        "ResultCode": 0,
        "ResultDesc": "Accepted"
    }













