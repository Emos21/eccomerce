import os
import requests
from django.shortcuts import render
from django.http import HttpResponse
from .models import Product

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})



def checkout(request):
    if request.method == 'POST':
        total_amount = 0
        
        # Retrieve M-Pesa credentials from environment variables
        consumer_key = os.environ.get('MPESA_CONSUMER_KEY')
        consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET')
        api_password = os.environ.get('MPESA_PASSWORD')

        # Loop through each product and calculate total amount
        for product in Product.objects.all():
            quantity_key = f'product_{product.id}_quantity'
            price_key = f'product_{product.id}_price'
            
            quantity = int(request.POST.get(quantity_key, 0))
            price = float(request.POST.get(price_key, 0))
            
            total_amount += quantity * price

        # Construct M-Pesa access token URL
        access_token_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

        # Make request to generate access token
        response = requests.get(access_token_url, auth=(consumer_key, consumer_secret))

        if response.status_code == 200:
            access_token = response.json()['access_token']

            # Construct M-Pesa STK push URL
            stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

            # Set request headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Set request payload
            payload = {
                'BusinessShortCode': '174379',
                'Password': api_password,
                'Timestamp': 'YOUR_TIMESTAMP',
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': total_amount,
                'PartyA': 716294465,
                'PartyB': 'YOUR_PAYBILL_NUMBER',
                'PhoneNumber': 716294465,
                'CallBackURL': 'YOUR_CALLBACK_URL',
                'AccountReference': 'YOUR_ACCOUNT_REFERENCE',
                'TransactionDesc': 'Payment for products'
            }

            # Make request to initiate STK push
            response = requests.post(stk_push_url, json=payload, headers=headers)

            if response.status_code == 200:
                # Payment initiated successfully
                return HttpResponse('Payment initiated successfully. Check your phone for M-Pesa prompt.')
            else:
                # Failed to initiate payment
                return HttpResponse('Failed to initiate payment. Please try again.')
        else:
            # Failed to generate access token
            return HttpResponse('Failed to generate access token. Please try again.')

    # If request method is not POST, render the checkout form
    products = Product.objects.all()
    return render(request, 'checkout.html', {'products': products})