import requests
from MOFSLOPENAPI import MOFSLOPENAPI

# def get_current_price(stock_symbol):
#     # Replace this with the actual API endpoint and key
#     response = requests.get(f"https://api.example.com/price/{stock_symbol}")
#     data = response.json()
#     return data["price"]
# app/bot/api_client.py
from MOFSLOPENAPI import MOFSLOPENAPI

def initialize_motilal_api(user_id, app_key):
    motilal_api = MOFSLOPENAPI(
        f_apikey=app_key,
        f_Base_Url="https://openapi.motilaloswal.com",
        f_clientcode=user_id,
        f_strSourceID="Web",
        f_browsername="Chrome",
        f_browserversion="91.0"
    )
    return motilal_api
