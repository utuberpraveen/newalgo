from app.extensions import db

class StockData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stock_symbol = db.Column(db.String(20), nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    ath = db.Column(db.Float, nullable=False)  # ATH (All-time High)
    how_far = db.Column(db.Float, nullable=False)  # How Far (percentage)
    stop_loss = db.Column(db.Float, nullable=False)
    highest_price = db.Column(db.Float, nullable=False)
    total_shares = db.Column(db.Integer, nullable=False)
    sl_point = db.Column(db.Float, nullable=False)
    ten_percent = db.Column(db.Float, nullable=False)  # 10%
    twenty_percent = db.Column(db.Float, nullable=False)  # 20%
    thirty_percent = db.Column(db.Float, nullable=False)  # 30%
    investment = db.Column(db.Float, nullable=False)
    sl = db.Column(db.String(50), nullable=False)
    ready_to_lose = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.String(100), nullable=False)
    nsesymboltoken = db.Column(db.String(100), nullable=False)
    tp1 = db.Column(db.Float, nullable=False)
    tp2 = db.Column(db.Float, nullable=False)
    tp3 = db.Column(db.Float, nullable=False)
    trailing_sl = db.Column(db.Float, nullable=False)
    fifty_two_w_high = db.Column(db.Float, nullable=False)
    which_strategy = db.Column(db.String(100), nullable=False)
    trade_status = db.Column(db.String(50), nullable=False)

    # Foreign key relation to user for easy retrieval
    user = db.relationship("User", backref="stocks")
