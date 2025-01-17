import streamlit as st
from datetime import datetime
from datetime import date
from time import ctime
import pandas as pd
import os
import numpy as np
#from nsepython import *
import time
import threading
#from MOFSLOPENAPI import MOFSLOPENAPI
import MOFSLOPENAPI
import traceback
import requests
import pyotp as tp

# Initialize the Motilal API instance with the necessary parameters
# Ensure that MOFSLOPENAPI.py is in the same directory or properly installed as a package

#Initialize the Motilal API instance


# App Key, Username, and Password inputs
'''
app_key = "aUaqEi7n34vMkUDb"#st.sidebar.text_input("App Key")
userid = "BGRKA1206"#st.sidebar.text_input("UserID")
password = "UBEST4321"#st.sidebar.text_input("Password", type="password")
dob_input = st.sidebar.date_input("Date of Birth")
dob = "27/08/1990"  # Convert to dd/mm/yyyy format

totp_key = "F44KBI5I2P4ZGVZOPDOK7UBCLZPNGTW5"
totp=tp.TOTP(totp_key).now()

'''

# App Key, Username, and Password inputs
app_key = "3x5BxErcP7Ks13Rx"#st.sidebar.text_input("App Key")
userid = "BGRKA1202"#st.sidebar.text_input("UserID")
password = "Ch@pper1"#st.sidebar.text_input("Password", type="password")
dob_input = st.sidebar.date_input("Date of Birth")
dob = "20/04/1949"  # Convert to dd/mm/yyyy format

totp_key = "VXOULXLW5YT6O2ZO4MXRVWG4RCAUEFLH"
totp=tp.TOTP(totp_key).now()



uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type=["xlsx"])

Mofsl = MOFSLOPENAPI.MOFSLOPENAPI(
    f_apikey = app_key, #"3x5BxErcP7Ks13Rx",
    #f_apikey=app_key,
    f_Base_Url="https://openapi.motilaloswal.com",  # or UAT URL
    #   f_Base_Url=base_url,  # or UAT URL
    f_clientcode= userid,#"BGRKA1202",
    f_strSourceID="Web",  # Assuming it's a web environment
    f_browsername="Chrome",
    f_browserversion="91.0"
)



# Global variable to store live prices
live_prices = {}


# Function to login and start WebSocket
def login_and_start_websocket(userid, password, dob, totp, vendorinfo):
    try:
        response = Mofsl.login(userid, password, dob, totp, vendorinfo)
        if response["status"] == "SUCCESS":
            telegram_bot("Login successful! Starting WebSocket...")
        else:
            st.error(f"Login failed: {response['message']}")
            telegram_bot(f"Login failed: {response['message']}")
        return response
    except Exception as e:
        telegram_bot(f"Error during login: {e}")
        return e

# Function to update the live prices in the DataFrame
def update_live_prices(df,sleepTime):
    while True:
        for i, stock in df.iterrows():
            script_code = stock['nsesymboltoken']
            if script_code in live_prices:
                df.at[i, 'CMP'] = live_prices[script_code]
        # Display the updated DataFrame in the placeholder
        with placeholder:
            st.dataframe(df)
        time.sleep(sleepTime)



def get_total_stocks(clientcode,stocks_df): #Mofsl, clientcode):
    holding_stocks = []

    # Get Holdings
    print("--------------------------------Func GetHolding--------------------------------")
    total_holdings_df = pd.DataFrame(Mofsl.GetDPHolding(clientcode)['data'])
    total_holdings_df.to_csv("total_holdings_df.csv")

    if not total_holdings_df.empty:
        total_holdings_df["scripname"] = total_holdings_df["scripname"].apply(lambda x: x.split()[0])
        holding_stocks.extend(total_holdings_df["scripname"].tolist())
        #total_holdings_df.rename(columns={'bsesymboltoken': 'nsesymboltoken'}, inplace=True)
    else:
        print("No Holding Positions/Stocks")

    # Get Positions
    print("--------------------------------Func GetPosition--------------------------------")
    total_positions_df = pd.DataFrame(Mofsl.GetPosition(clientcode)['data'])
    total_positions_df.to_csv("total_positions_df.csv")
    

    if not total_positions_df.empty:
        print("Contains Positions (not empty)")
        total_positions_df.rename(columns={'symbol': 'scripname', 'symboltoken': 'nsesymboltoken'}, inplace=True)
        total_positions_df["scripname"] = total_positions_df["scripname"].apply(lambda x: x.split()[0])
        total_positions_df["positionquantity"] = total_positions_df["buyquantity"] - total_positions_df["sellquantity"]
        total_positions_df["positionbuyavg"] = total_positions_df.apply(
            lambda x: (x["buyamount"] - x["sellamount"]) / x['positionquantity'] if x['positionquantity'] > 0 else 0, axis=1)
        total_positions_df["positionsellavg"] = total_positions_df.apply(
            lambda x: (x["buyamount"] - x["sellamount"]) / x['positionquantity'] if x['positionquantity'] < 0 else 0, axis=1)

        #what if holdings is empty
        print(f'total_positions_df : {total_positions_df["scripname"].unique()}')
        print(f'total_holdings_df : {total_holdings_df["scripname"].unique()}')
        if total_holdings_df.empty:
            combined_df = total_positions_df.copy()
            combined_df[["dpquantity","blockedquantity","buyavgprice"]] = 0
        else:
            combined_df = pd.merge(total_positions_df, total_holdings_df, how="outer", on=["nsesymboltoken","scripname"])
            
            
        # Merge Holdings and Positions
        #combined_df = pd.merge(total_positions_df, total_holdings_df, on=["nsesymboltoken", "scripname"], how="outer")
        combined_df.to_csv("merge before.csv")
        print("stocks_df") #,stocks_df.columns)

        combined_df = pd.merge(stocks_df, combined_df , how="left", on=["nsesymboltoken","scripname"])
        combined_df.to_csv("merge merge.csv")
        
        combined_df.fillna(0, inplace=True)
        combined_df["remainingqty"] = combined_df["dpquantity"] + combined_df["positionquantity"]
        
        
        
        # Calculate remaining quantities and current average price
        combined_df.to_csv("merge after.csv")

        combined_df = combined_df[["scripname", "nsesymboltoken", "total_shares", "dpquantity","blockedquantity", "positionquantity", 
                                     "buy_price", "buyavgprice", "positionbuyavg", "stop_loss", "trailing_sl", 
                                     "tp1", "tp2", "tp3","current_tp", "positionsellavg", "remainingqty","CMP","high","52w_high"]]#,"low"]]

        print("positions and holding loop passed")
        combined_df.to_csv("P_H.csv")
        return combined_df

    else:
        print("No Positions Entered/Exited today")
        if not total_holdings_df.empty:
            combined_df = total_holdings_df.copy()
            #print("Length : ",len(stocks_df),len(combined_df))

            #print("\ncombined_df columns : ",combined_df.columns,"\nstocks df columns : ",stocks_df.columns)
            combined_df = pd.merge(stocks_df, combined_df, how="left", on=["nsesymboltoken","scripname"])
            combined_df["remainingqty"] = combined_df["dpquantity"]
            combined_df["positionquantity"] = combined_df["positionbuyavg"] = combined_df["positionsellavg"] = 0
            combined_df.fillna(0, inplace=True)
            combined_df = combined_df[["scripname", "nsesymboltoken", "total_shares", "dpquantity","blockedquantity", "positionquantity", 
                                        "buy_price", "buyavgprice", "positionbuyavg", "stop_loss", "trailing_sl", 
                                        "tp1", "tp2", "tp3", "current_tp","positionsellavg", "remainingqty","CMP","high","52w_high"]]#,"low"]]
            #print(combined_df)
            print("holdings loop passed")
            return combined_df
        else:
            combined_df = pd.DataFrame(columns = ["scripname", "nsesymboltoken", "total_shares", "dpquantity","blockedquantity", "positionquantity", 
                                     "buy_price", "buyavgprice", "positionbuyavg", "stop_loss", "trailing_sl", 
                                     "tp1", "tp2", "tp3","current_tp", "positionsellavg", "remainingqty","CMP","high","52w_high"])
            print(combined_df)
            return combined_df

    return pd.DataFrame()  # Return an empty DataFrame if there are no holdings or positions

#trailing stop loss
def calculate_trailing_sl(row):
    # Extract necessary values for clarity
    stop_loss = row["stop_loss"]
    total_shares = row["total_shares"]
    remaining_qty = row["remainingqty"]
    cmp = row["CMP"]
    tp1 = row["tp1"]
    tp2 = row["tp2"]
    tp3 = row["tp3"]
    last_tp = tp3 * 1.20
    high = 0
    buy_price = row["buy_price"]
    

    # Check if the total shares match the remaining quantity
    if total_shares == remaining_qty:
        return stop_loss,tp1
    else:
        high = row["high"] if row["high"] > row["52w_high"] else row["52w_high"]
    
    # Evaluate conditions for the trailing stop loss
    
    if (cmp >= tp1 or tp1 <= high) and cmp < tp2:
        return buy_price,tp2
    elif (cmp >= tp2 or tp2 <= high) and cmp < tp3:
        return tp1,tp3
    elif (cmp >= tp3 or tp3 <= high):
        return tp2,last_tp
    else:
        return stop_loss,tp1


#orderplacing function
def place_order(scriptname,symboltoken,direction,shares_count,execution_price,order_type):

    order_type = 'STOPLOSS' if order_type.lower() == 'limit' else 'MARKET'
    price = round(execution_price * 1.005,2) if order_type.lower() == 'limit' else 0
    trigger_price = execution_price if order_type.lower() == 'limit' else 0

        
    Orderinfo = {
            "clientcode":clientcode,
            "exchange":"NSE",
             "symboltoken": symboltoken,
             "buyorsell": direction ,
             "ordertype": order_type,
             #LIMIT (OT) - GTD (OD) -> DD-MMM-YYYY(GTD)
             #MARKET (OT) - DAY (OD) - none(GTD)
             "producttype":"DELIVERY",
             "orderduration":"DAY",
             "price": price,
             "triggerprice": trigger_price,
             "quantityinlot":int(shares_count),
             "disclosedquantity":0,
             "amoorder":"N",
             "algoid":"",
             "goodtilldate":"",
             "tag":" "
        }
        #Mofsl.PlaceOrder(Orderinfo)
    #print(Orderinfo)
    try:
        trade_output = Mofsl.PlaceOrder(Orderinfo)
        Orderinfo["scriptname"] = str(scriptname)
        telegram_bot(str(Orderinfo))
        telegram_bot(str(trade_output))
        #print(trade_output)
    except Exception as e :
        #print(e)
        telegram_bot(f"Error while place_order :  \n {traceback.format_exc()}\n")


# Sidebar: User login input form
st.sidebar.title("Login to Stock Tracker")
st.title("Stock Filter")



#totp = st.sidebar.text_input("TOTP")
environment = st.sidebar.radio("Select Environment", ("Live", "UAT"))
base_url = "https://openapi.motilaloswaluat.com"
if environment == "Live":
    base_url = "https://openapi.motilaloswal.com"
placeOrder = st.sidebar.radio("Place Order", ("Yes", "No"))
sleepTime = st.sidebar.number_input("Sleep", min_value=10, max_value=60, value=15, step=1)
clientcode=""

# Placeholder for displaying the DataFrame
placeholder = st.empty()

def old_sl():
    df["trailing_sl"] = df.apply(lambda x : x["stop_loss"] if x['total_shares'] == x['remainingqty'] else
                                                                            (x["tp1"] if (x["CMP"]>=x["tp2"] or x["tp2"] <= x["high"]) and x["CMP"] < x["tp3"] else
                                                                              (x["buy_price"] if (x["CMP"]>=x["tp1"] or x["tp1"] <= x["high"]) and x["CMP"] < x["tp2"]  else
                                                                               x["tp2"])), axis=1)

def telegram_bot(message):
    print(message)
    bot_token="8130189298:AAF9plnRt_LSf92CsTRWJk0xoWPZZDL0yng"
    chatID= -1002245043401 #private telegram bot channel
    apiURL=f'https://api.telegram.org/bot{bot_token}/sendmessage'
    #self.print_output(f'apiURL : {apiURL} message : {message}')
    
    try:
        response = requests.post(apiURL,{'chat_id':chatID,'text': message })
        print(f'Bot_response : {response}')
    except Exception as e:
        print(f'Bot Error Message :  \n {traceback.format_exc()}\n')
    

#telegram_bot("Hello")
# Login Button
if st.sidebar.button("Login"):


    print(app_key)
    print(base_url)


    # Log the login info for debugging purposes
    print(f"Login Info: {userid}, {password}, {dob}, {totp}")
    if uploaded_file:
        try:
            columns_to_read = ['scripname', 'CMP', 'buy_price', 'total_shares', 'nsesymboltoken',"52w_high"]  #'stop_loss' 6 ,'tp1' 10,'tp2' 20,'tp3' 30,'trailing_sl'] #, 'ATH',
            df = pd.read_excel(uploaded_file, usecols=columns_to_read)
            print("excel read")
            df['scripname'] = df['scripname'].str.upper() 
            df = df.dropna(subset=['nsesymboltoken', 'scripname'])#subset=['nsesymboltoken', 'scripname'])
            df = df.drop_duplicates(subset=['scripname','nsesymboltoken'],keep = 'first' )
            df['nsesymboltoken'] = df['nsesymboltoken'].astype(int)
            df['total_shares'] = df['total_shares'].astype(int)
            df['buy_price'] = df['buy_price'].astype(float)
            df['52w_high'] = df['52w_high'].astype(float)
            df['stop_loss'] = df['buy_price'] * 0.94
            df['tp1'] = df['buy_price'] * 1.10
            df['tp2'] = df['buy_price'] * 1.20
            df['tp3'] = df['buy_price'] * 1.30
            df["remainingqty"] = 0
            df["current_tp"] = df['52w_high'].copy() #df['buy_price'] * 1.50
            df["trailing_sl"] = df['stop_loss']
            df.to_excel("Excel.xlsx")

            #print(f"Excel uploaded successfully: {df.columns}")
            telegram_bot(f"Excel uploaded successfully")
            print(df.columns)
            #stock_script_codes = df['nsesymboltoken'].tolist()

            # Start WebSocket connection
            
            try:
 
                login_message = Mofsl.login(userid, password, dob, totp, userid)
                status = login_message['status']
            
        
                if status == "SUCCESS":
                    st.success("Logged in successfully, WebSocket connection started!")
                    telegram_bot(f"Logged in success,\n\nWebSocket connection starts : {str(ctime())}")
                    start_time = int(time.time())
                    
                    #st.dataframe(df)

                    # # GetReportMarginSummary 
                    print("--------------------------------GetReportMarginSummary--------------------------------")
                    #Mofsl.GetReportMarginSummary(clientcode)
                    amount_available = Mofsl.GetReportMarginSummary(clientcode)["data"][0]
                    st.write("Total amount Available : ",amount_available["amount"])
                    print("Total amount Available : ",amount_available["amount"])
                    scripts = pd.unique(df['nsesymboltoken']).tolist()
                    print("--------------------------------scripts--------------------------------",scripts)
                    print("--------------------------------GetHoldings--------------------------------")
                    holding_stocks = []
                    shares_not_to_buy = []
                    shares_bought_today = []
                    total_holdings_df = pd.DataFrame(Mofsl.GetDPHolding(clientcode)['data'])
                    #st.write("total_holdings_df :", total_holdings_df)
                    # # GetPosition 
                    print("--------------------------------GetPosition--------------------------------")
                    # Mofsl.GetPosition(clientcode)
                    total_positions_df = pd.DataFrame(Mofsl.GetPosition(clientcode)['data'])
                    #st.write("total_position_df :",total_positions_df)

                    print("-------------------------------Total Holding---------------------------------")
                    #total_stocks = get_total_stocks(userid,df)
                    st.write("Total Holdings :")
                    total_holdings = st.empty()
                    #holding_stocks = pd.unique(total_stocks[total_stocks['remainingqty']>0]['scripname']).tolist()
                    print("--------------------------------GettingLtp--------------------------------")
                    # Create a placeholder for the DataFrame in the Streamlit UI
                    #total_holdings = st.empty()
                    totaldf_time_holder = st.empty()
                    st.write("Open Orders Dataframe :")
                    open_order_df_placeholder = st.empty()
                    open_order_df_time_holder = st.empty()
                    st.write("Sell Dataframe(Stocks near or at trailing_sl/Partial close) :")
                    selldf_placeholder = st.empty()
                    selldf_time_holder = st.empty()
                    st.write("Buy Dataframe(Stocks near or at buy_price)  :")
                    buydf_placeholder = st.empty()
                    buydf_time_holder = st.empty()
                    
                    print(scripts)

                    #df = pd.DataFrame(total_stocks)
                    
                    columns_to_read = columns_to_read + ['remainingqty','high','stop_loss','tp1','tp2','tp3','trailing_sl','current_tp'] #,"low"]

                    # Start the while loop for continuous updates
                    while True:
                        #print("--------------------------------Entering While scripts--------------------------------", scripts)
                        # Extract the latest price data for all scripts in a single pass
                        extracted_data = []
                        print("LTP price update starts : ",str(ctime()))
                        
                        #st.empty()
                        try:
                            for script in scripts:
                                LTPData = {
                                    "clientcode": clientcode,
                                    "exchange": "NSE",
                                    "scripcode": script
                                }
                                try:
                                    # Fetch quote data from the API
                                    quote = Mofsl.GetLtp(LTPData)["data"]
                                    # print("########### Quote#####")
                                    # print(quote)
                                except Exception as e:
                                    st.error(f"Error while getting LTP etc the : {e}")
                                
                                # Extract relevant data
                                scripcode = quote['scripcode']
                                current_price = quote['ltp'] / 100  # Convert ltp to CMP
                                high = quote['high']/100
                                low = quote['low']/100
                                
                                # Append the data to the list for DataFrame construction
                                extracted_data.append({
                                    "nsesymboltoken": scripcode,  
                                    "CMP": current_price, # Store directly as 'CMP'
                                    "high": high,
                                    #"low": low
                                })
                            
                            #print(extracted_data)
                            print("##### extracted done####")
                        except Exception as e :
                            telegram_bot(f"LTP update failed : {e}")

                        try:
                            # Since we're already using 'CMP' in ltp_df, we can directly update df
                            #df.update(ltp_df.set_index('nsesymboltoken'))  # Update df's 'CMP'
                            #currentTime = datetime.now().strftime('%H:%M:%S')
                            totaldf_time_holder.markdown("%s" % str(ctime()))
                            #st.write("Last Updated Time :", ctime())
                            for cmp in extracted_data:
                                sCode = cmp['nsesymboltoken']
                                sCMP = cmp['CMP']
                                sHigh = cmp['high']
                                #sLow = cmp['low']
                                df.loc[df['nsesymboltoken'] == sCode, 'CMP'] = sCMP
                                df.loc[df['nsesymboltoken'] == sCode, 'high'] = sHigh
                                #df.loc[df['nsesymboltoken'] == sCode, 'low'] = sLow

                            # Update the DataFrame in the Streamlit UI using the placeholder
                            # print("###### final df#####")
                            # print(df)
                            print("Before checking : ",holding_stocks)

                            df[["trailing_sl","current_tp"]] = df.apply(calculate_trailing_sl, axis=1,result_type='expand')
                            print("Before updated ln 420") #,df.columns)

                            df.to_csv("Df live.csv")
                            total_stocks = get_total_stocks(userid,df[columns_to_read])
                            
                            df = pd.DataFrame(total_stocks)

                            #print("Updateddf columns")
                            #print(df.columns)
                        
                            holding_stocks = pd.unique(total_stocks[total_stocks['remainingqty']>0]['scripname']).tolist()

                            print(f"\nTrading management stcoks : {holding_stocks}\n")
                            
                            if len(holding_stocks)>0 :

                                
                                def myround(x, base=1):
                                    return base * round(x/base)

                                #sell_df = df[df["scripname"].str.contains("|".join(holding_stocks))]
                                print("Holdings")
                                #print(df.columns)
                                #print(df[df['remainingqty']>0])
                                #print("Df")

                                df["% up"] = ((df["CMP"]-df["buy_price"])/df["buy_price"])*100
                                holdings_df = df[df['remainingqty']>0]

                                columns_reorder = ["scripname","total_shares", "dpquantity","blockedquantity", "positionquantity", 
                                     "buy_price", "buyavgprice", "positionbuyavg","trailing_sl", 
                                     "current_tp", "positionsellavg","CMP","% up","high","52w_high"]


                                total_holdings.dataframe(holdings_df[columns_reorder])

                                #trailing_sl_df = total_stocks[["nsesymboltoken","scripname","remainingqty"]].copy()
                                
                    
                                #sell_df = pd.merge(df, trailing_sl_df, how="inner", on=["nsesymboltoken","scripname"])

                                #print("after displaying holdings: ",len(df))
                                sell_df = df[df["scripname"].str.contains("|".join(holding_stocks))]   #holding stocks

                                #sell_df.to_csv("Sell.csv")
                                #df.to_csv("df.csv")

                                print("Getting df for tp and sl")
                                tp1_df = sell_df.query('tp1 <= CMP and remainingqty==total_shares')
                                sell_df = sell_df.query('CMP <= trailing_sl') # or low < trailing_sl')

                                #print(df["CMP"])

                                sell_df =pd.concat([sell_df,tp1_df])

                                #print(sell_df)

                                #print(len(df))
                                
                                if not sell_df.empty :
                                    sell_df["Shares_to_sell"] = sell_df.apply(lambda x : myround(x["remainingqty"] / 2) if x['total_shares'] == x['remainingqty'] and x['tp1']<=x['CMP'] else x["remainingqty"], axis=1)
                                    if placeOrder.lower() == 'yes':
                                        sell_df.apply(lambda x: place_order(x["scripname"],x["nsesymboltoken"], "SELL", x["Shares_to_sell"], 0 ,'MARKET'), axis=1) # 0 indicates market order/current price
                                    sell_df.to_csv("sell.csv")
                                    #shares_not_to_buy = shares_not_to_buy + sell_df['scripname'].unique()
                                    selldf_placeholder.dataframe(sell_df)
                                else:
                                    print(f"None to sell, sold today : {shares_not_to_buy}")
                                    selldf_placeholder.dataframe(pd.DataFrame())
                                #    df[["trailing_sl","current_tp"]] = df.apply(calculate_trailing_sl, axis=1)

                                #for stop loss hit stocks
                                
                                selldf_time_holder.markdown("%s" % str(ctime()))
                                
                                    
                                
                            else:
                                print("No holding section, None to sell")
                                total_holdings.dataframe(pd.DataFrame())
                                
                                selldf_time_holder.markdown("%s" % str(ctime()))
                                selldf_placeholder.dataframe(pd.DataFrame())

                            try:
                                orderbook = pd.DataFrame(Mofsl.GetOrderBook(userid)['data'])
                                shares_not_to_buy = orderbook[(orderbook["series"]=="EQ") & (orderbook["orderstatus"]=="Traded") & (orderbook["buyorsell"]=="SELL")]['symbol'].unique()
                                shares_not_to_buy = [s.strip(' EQ') for s in shares_not_to_buy]

                                shares_bought_today = orderbook[(orderbook["series"]=="EQ") & (orderbook["orderstatus"].str.contains("|".join(["Traded", "Confirm"]))) & (orderbook["buyorsell"]=="BUY")]['symbol'].unique()
                                shares_bought_today = [s.strip(' EQ') for s in shares_bought_today]
                                orderbook.to_csv("OrderBook.csv")
                                orderbook = orderbook[orderbook["orderstatus"] == "Confirm"][['symboltoken','symbol','ordertype','orderstatus','buyorsell','triggerprice','price','totalqtyremaining','orderqty','qtytradedtoday']]
                                open_order_df_placeholder.dataframe(orderbook)
                                open_order_df_time_holder.markdown("%s" % str(ctime()))


                                #tradebook = pd.DataFrame(Mofsl.GetTradeBook(userid)['data'])
                                #tradebook.to_csv("Tradebook.csv")
                            except:
                                print("No Orders Placed today")
                                open_order_df_placeholder.dataframe(pd.DataFrame())
                                open_order_df_time_holder.markdown("%s" % str(ctime()))

                            list_of_stocks = list(set(holding_stocks + shares_not_to_buy))
                            print("list_of_stocks : ", list_of_stocks)
                                
                            buy_df = df[~df["scripname"].str.contains("|".join(list_of_stocks))]
                            buy_df = buy_df[(buy_df["CMP"] >= buy_df["buy_price"] * 0.98 ) & (buy_df["CMP"] <= (buy_df["buy_price"]*1.005))]
                            buy_df['Order_type'] = buy_df.apply(lambda x : 'MARKET' if x["CMP"] >= x["buy_price"] else 'LIMIT',axis = 1)
                    
                            buy_df["Percentage"] = (buy_df["CMP"]-buy_df["buy_price"])/100 #df.apply(lambda x: ( if x["CMP"] >= x["buy_price"] else )
                
                            #for new buys in stocks
                            #st.write("Stocks getting buy signal")
                            
                            if len(buy_df)>0:
                                print("Got df for buy")
                                buy_df.to_csv("buy.csv")
                                buydf_placeholder.dataframe(buy_df)
                                if placeOrder.lower() == 'yes':
                                    buy_df.apply(lambda x: place_order(x["scripname"],x["nsesymboltoken"], "BUY", x["total_shares"], x['buy_price'] ,x['Order_type']), axis=1)

                            else:
                                print("No stocks for Buy")
                                print(f"None to buy, bought today : {shares_bought_today}")
                                print(f"placeOrder : {placeOrder}")
                                if placeOrder.lower() == 'yes':
                                    print("Will Place order")
                                else:
                                    print("Will not Place order")
                                buydf_placeholder.dataframe(pd.DataFrame())

                            buydf_time_holder.markdown("%s" % str(ctime()))
                            # This will now update in place with the new 'df'
                            
                            #df[["trailing_sl","current_tp"]] = df.apply(calculate_trailing_sl, axis=1)
                            #df.to_csv("after trailing sl modification.csv") #based on cmp

                            #print(df.columns)
                            #df = df[columns_to_read + ["remainingqty"]]
                            #print(df.columns)

                            #display_current_stocks = get_total_stocks(userid,df[columns_to_read])
                            #st.write("holdings with updated stocks")
                            #data_placeholder.dataframe(display_current_stocks)

                            
                            #holding_stocks
                            print("webconnection ends")
                            end_time = int(time.time())

                            diff = end_time - start_time

                            if diff > 1800:
                                telegram_bot("All okay ,No issue so far")
                                start_time = end_time
                            else:
                                print(f"Difference is less, {diff}")
                            
                        except Exception as e:
                            st.error(f"Error while merging etc the :  \n {traceback.format_exc()}\n")
                            telegram_bot(f"Error while merging etc the :  \n {traceback.format_exc()}\n")
                        time.sleep(sleepTime)
                        
            except Exception as e:
                st.error(f"Error starting the WebSocket connection:  \n {traceback.format_exc()}\n")
                telegram_bot(f"Error starting the WebSocket connection:  \n {traceback.format_exc()}\n")
                

        except Exception as e:
            st.error(f"Error processing the Excel file:  \n {traceback.format_exc()}\n")
            telegram_bot(f"Error processing the Excel file:  \n {traceback.format_exc()}\n")
    else:
        st.info("Please upload an Excel file.")
        telegram_bot("Please upload an Excel file.")
else:
    st.write("Please upload the Excel file and login")
    telegram_bot("Please upload the Excel file and login")



