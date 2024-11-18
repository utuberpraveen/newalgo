import pandas as pd
from app.models.stock_data import StockData

def parse_excel(file, user_id):
    data = pd.read_excel(file)
    stock_data_list = []
    for _, row in data.iterrows():
        stock = StockData(
            user_id=user_id,
            stock_symbol=row["Stock Symbol"],
            buy_price=row["Target Buy Price"],
            sell_price=row["Target Sell Price"],
            quantity=row["Quantity"],
            stop_loss=row["Stop-Loss Price"]
        )
        stock_data_list.append(stock)
    return stock_data_list
