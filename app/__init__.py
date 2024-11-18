from flask import Flask, redirect, url_for
from app.extensions import db, login_manager
from app.auth.routes import auth_bp
from app.views.dashboard import dashboard_bp
from app.models.user import User  # Import your User model
from app.config import Config
from flask_dance.contrib.google import make_google_blueprint
import os
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate = Migrate(app, db)  # Initialize Flask-Migrate here
    login_manager.init_app(app)
    
    #UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']

    # # Create the uploads folder if it doesn't exist
    # if not os.path.exists(UPLOAD_FOLDER):
    #     os.makedirs(UPLOAD_FOLDER)

    # Register Blueprints
    app.register_blueprint(auth_bp)         # Authentication routes
    app.register_blueprint(dashboard_bp)     # Dashboard routes

    # Google OAuth Blueprint
    google_bp = make_google_blueprint(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        redirect_to="auth.google_login",
        scope=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]
    )
    app.register_blueprint(google_bp, url_prefix="")

    # Redirect root to login page if unauthenticated
    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    # Add user_loader to load user from session
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Load user by ID, using your User model

    with app.app_context():
        db.create_all()

    return app
