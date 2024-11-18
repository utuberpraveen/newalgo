from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user, logout_user
from app.models.broker_info import BrokerInfo
from app.bot.api_client import initialize_motilal_api

dashboard_bp = Blueprint("dashboard", __name__)

# Dashboard view route
@dashboard_bp.route("/dashboard")
@login_required
def dashboard_view():
    print("in dashboard view")
    broker_user_id = session.get("broker_user_id")
    app_key = session.get("app_key")

    print("broker_user_id : ",broker_user_id)
    print("app_key : ",app_key)

    # Initialize the Motilal API instance for the current user
    motilal_api = initialize_motilal_api(broker_user_id, app_key)
    # Pass user information to template

    # Set the stored AuthToken if available
    auth_token = session.get('auth_token')
    if auth_token:
        motilal_api.m_strMOFSLToken = auth_token
    else:
        flash("Auth token not found. Please log in to your broker again.", "danger")
        return redirect(url_for("auth.broker_login"))

    amount_available = motilal_api.GetReportMarginSummary(broker_user_id)["data"][0]
    print("User  broker_user_id : ",broker_user_id)
    print("Total amount Available : ",amount_available["amount"])
    return render_template("dashboard.html", user_name=current_user.name, 
                           user_email=current_user.email,
                           balance =amount_available["amount"], 
                           broker_user_id=broker_user_id)

# File upload route
@dashboard_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_file():
    if request.method == "POST":
        # Handle file upload logic (placeholder)
        flash("File uploaded successfully!", "success")
        return redirect(url_for("dashboard.dashboard_view"))
    return render_template("upload.html")

# Log out route
@dashboard_bp.route("/logout")
@login_required
def logout():
    logout_user()  # Log the user out
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))  # Redirect to login page
