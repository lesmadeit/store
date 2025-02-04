import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64


class MpesaC2bCredential:
    consumer_key = 'OVfR5jHsG9ydGzsKJDoGPfLzrCJauKo2zjcthScvojQrnx5U'
    consumer_secret ="QuGHi7jj1pVRieav3G3Tk6dEjLtA3uShK9oGnirhr9vxYwuN7BAeqE6nX11kHBau"
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'


class MpesaAccessToken:
    r = requests.get(MpesaC2bCredential.api_URL, auth=HTTPBasicAuth(MpesaC2bCredential.consumer_key, MpesaC2bCredential.consumer_secret))
    mpesa_access_token = json.loads(r.text)
    validated_mpesa_access_token = mpesa_access_token['access_token']



class LipanaMpesaPassword:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    business_short_code = "174379"
    passkey =  'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

    data_to_encode = business_short_code + passkey + timestamp

    #Encode data in Base64 format to generate password
    online_password = base64.b64encode(data_to_encode.encode())
    
    #Decode the Base64-encoded password into a readable string
    decode_password = online_password.decode('utf-8')

