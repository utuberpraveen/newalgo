# app/utils/file_utils.py

import os
from werkzeug.utils import secure_filename
from flask import current_app, flash
import pandas as pd
from app.extensions import db
from app.models import StockData

def allowed_file(filename):
    allowed_extensions = {'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file_and_parse_data(file, user_id):
    # Check if the file is allowed
    if not allowed_file(file.filename):
        flash("File type not allowed. Please upload an Excel file.", "danger")
        return False

    # Create a user-specific directory for uploads if it doesn't exist
    user_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)

    # Save the file to the user's folder
    filename = secure_filename(file.filename)
    file_path = os.path.join(user_folder, filename)
    file.save(file_path)

    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path)

        # Validate the necessary columns
        required_columns = [
            'scripname', 'CMP', 'buy_price', 'ATH', 'How_Far', 'stop_loss', 
            'Highest_Price', 'total_shares', 'SL Point', '10%', '20%', '30%', 
            'Investment', 'SL', 'Ready to Lose', 'nsesymboltoken', 'tp1', 
            'tp2', 'tp3', 'trailing_sl', '52_w_high', 'which_strategy', 'trade_status'
        ]
        
        if not all(col in df.columns for col in required_columns):
            flash("Invalid file format. Missing required columns.", "danger")
            return False

        # Save each row to the StockData table
        for _, row in df.iterrows():
            new_stock = StockData(
                user_id=user_id,
                stock_symbol=row['scripname'],
                ath=row['ATH'],
                buy_price=row['buy_price'],
                sell_price=row['CMP'],  # Assuming CMP is considered as the current price
                quantity=row['total_shares'],
                stop_loss=row['stop_loss'],
                highest_price=row['Highest_Price'],
                sl_point=row['SL Point'],
                ten_percent=row['10%'],
                twenty_percent=row['20%'],
                thirty_percent=row['30%'],
                investment=row['Investment'],
                sl=row['SL'],
                ready_to_lose=row['Ready to Lose'],
                nsesymboltoken=row['nsesymboltoken'],
                tp1=row['tp1'],
                tp2=row['tp2'],
                tp3=row['tp3'],
                trailing_sl=row['trailing_sl'],
                fifty_two_week_high=row['52_w_high'],
                which_strategy=row['which_strategy'],
                trade_status=row['trade_status']
            )
            db.session.add(new_stock)

        # Commit the transaction
        db.session.commit()
        flash("Stock data uploaded and saved successfully!", "success")
        return True

    except Exception as e:
        flash(f"Error processing file: {e}", "danger")
        db.session.rollback()
        return False
