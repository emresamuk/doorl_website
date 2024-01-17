from flask import Flask, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_babel import Babel
from functools import wraps
from wtforms import BooleanField

db = SQLAlchemy()
DB_NAME = "doorl.db"

# Admin e-posta adresini belirle
ADMIN_EMAIL = "emresamuk6869@gmail.com"


def is_admin():
    # Giriş yapan kullanıcının admin olup olmadığını kontrol et
    return "email" in session and session["email"] == ADMIN_EMAIL

# Define the login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page!", "danger")
            return redirect(url_for("auth.login"))
    return decorated_function

# Define a custom ModelView with login_required applied to methods
class CustomModelView(ModelView):
    @staticmethod
    def check_login():
        if "logged_in" in session:
            return True
        else:
            flash("Please login to view this page!", "danger")
            return False

    def is_accessible(self):
        return self.check_login() and super(CustomModelView, self).is_accessible()

    def inaccessible_callback(self, name, **kwargs):
        if not self.check_login():
            return redirect(url_for("auth.login"))
        return super(CustomModelView, self).inaccessible_callback(name, **kwargs)

    form_extra_fields = {
        'is_admin': BooleanField('Admin'),
    }

    def is_accessible(self):
        return bool(is_admin()) and super(CustomModelView, self).is_accessible()


# Define the create_database function
def create_database(app):
    app.app_context().push()

    if not path.exists('website/' + DB_NAME):
        db.create_all()
        print('Created Database!')

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'samukow'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    babel = Babel(app)
    
    admin = Admin(app, name='Doorl Admin Panel', template_mode='bootstrap4')

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Product, Newsletter, Callback, Cart, Testimonial
    
    # Use CustomModelView instead of ModelView
    admin.add_view(CustomModelView(User, db.session))
    admin.add_view(CustomModelView(Product, db.session))
    admin.add_view(CustomModelView(Callback, db.session))
    admin.add_view(CustomModelView(Newsletter, db.session))
    admin.add_view(CustomModelView(Cart, db.session))
    admin.add_view(CustomModelView(Testimonial, db.session))

    # Call create_database outside of create_app
    create_database(app)

    return app