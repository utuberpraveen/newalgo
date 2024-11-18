import threading
from time import sleep
from app.models.stock_data import StockData
from app.bot.api_client import get_current_price

class TradingBot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.is_running = False

    def start(self):
        self.is_running = True
        threading.Thread(target=self.run).start()

    def stop(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            stocks = StockData.query.filter_by(user_id=self.user_id).all()
            for stock in stocks:
                current_price = get_current_price(stock.stock_symbol)
                if current_price <= stock.buy_price:
                    print(f"Buying {stock.stock_symbol}")
                elif current_price >= stock.sell_price:
                    print(f"Selling {stock.stock_symbol}")
            sleep(10)  # Poll every 10 seconds
