import os
import logging
from flask import Blueprint, redirect, url_for, flash, render_template, request, session
from flask_dance.contrib.google import google
from flask_login import login_user, logout_user, login_required, current_user
import pandas as pd
from werkzeug.utils import secure_filename
from app.models.stock_data import StockData
from app.models.user import User
from app.extensions import db
from werkzeug.security import check_password_hash, generate_password_hash
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from app.models.broker_info import BrokerInfo
from app.bot.api_client import initialize_motilal_api

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

# User Login Routes
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("auth.broker_info"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    
    return render_template("login.html")

@auth_bp.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if resp.ok:
            user_info = resp.json()
            email = user_info.get("email")
            name = user_info.get("name")
            
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(email=email, password=generate_password_hash("default_password"), name=name)
                db.session.add(user)
                db.session.commit()

            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("auth.broker_info"))
        else:
            flash("Failed to fetch user info from Google.", "danger")
    except TokenExpiredError:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("google.login"))

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# Step 1: Broker Selection
@auth_bp.route("/broker_info", methods=["GET", "POST"])
@login_required
def broker_info():
    if request.method == "POST":
        broker = request.form.get("broker")
        if broker == "motilal":
            return redirect(url_for("auth.collect_broker_info"))
        else:
            flash("Unsupported broker selected.", "danger")
            return redirect(url_for("auth.broker_info"))

    return render_template("broker_info.html")


# Step 2: Collect Broker Credentials (if missing)
@auth_bp.route("/collect_broker_info", methods=["GET", "POST"])
@login_required
def collect_broker_info():
    broker_info = BrokerInfo.query.filter_by(user_id=current_user.id).first()

    # Check if broker info already exists
    if broker_info:
        flash("Broker information already exists.", "info")
        return redirect(url_for("auth.broker_login"))

    # Collect new broker info if not available
    if request.method == "POST":
        app_key = request.form['app_key']
        dob = request.form['dob']
        password = request.form['password']
        broker_user_id = request.form['broker_user_id']

        # Store broker info in the database
        new_broker_info = BrokerInfo(app_key=app_key, dob=dob, password=password, user_id=current_user.id,broker_user_id=broker_user_id)
        db.session.add(new_broker_info)
        db.session.commit()

        flash("Broker information saved successfully.", "success")
        return redirect(url_for("auth.broker_login"))

    return render_template("collect_broker_info.html")


# Step 3: Broker Login with TOTP
@auth_bp.route("/broker_login", methods=["GET", "POST"])
@login_required
def broker_login():
    broker_info = BrokerInfo.query.filter_by(user_id=current_user.id).first()
    if not broker_info:
        flash("Please provide broker information first.", "warning")
        return redirect(url_for("auth.collect_broker_info"))

    if request.method == "POST":
        totp = request.form['totp']
        vendor_id = ""
        # Initialize the Motilal API instance for the current user
        motilal_api = initialize_motilal_api(broker_info.broker_user_id, broker_info.app_key)
        # Attempt login with the provided TOTP
        login_response = motilal_api.login(broker_info.broker_user_id, broker_info.password, broker_info.dob,totp,broker_info.broker_user_id)
        print("Login Response : ",login_response)
        if login_response.get('status') == 'SUCCESS':
            # Pass user information to template
            session['auth_token'] = login_response['AuthToken']
            session['broker_user_id'] = broker_info.broker_user_id
            session['user_id'] = current_user.id
            session['app_key'] = broker_info.app_key
            flash("Login successful.", "success")
            print("Login successful and calling dashboard view")
            return redirect(url_for("dashboard.dashboard_view"))
        else:
            flash("Login failed. Please check your TOTP and try again.", "danger")

    # Pass broker_user_id to the template directly
    return render_template("broker_login.html", broker_user_id=broker_info.broker_user_id)

@auth_bp.route("/upload_stock_data", methods=["GET", "POST"])
@login_required
def upload_stock_data():
    if request.method == "POST":
        # Check if the file part is present in the request
        if 'file' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)

        file = request.files['file']

        # If no file is selected
        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(request.url)

        # Call utility function to save file and parse data
        if save_file_and_parse_data(file, user_id=current_user.id):
            return redirect(url_for('auth.view_stock_data'))
        else:
            return redirect(request.url)

    return render_template("upload_stock_data.html")

@auth_bp.route("/view_stock_data")
@login_required
def view_stock_data():
    # Retrieve the stock data for the current user
    user_stock_data = StockData.query.filter_by(user_id=current_user.id).all()
    return render_template("view_stock_data.html", stocks=user_stock_data)
