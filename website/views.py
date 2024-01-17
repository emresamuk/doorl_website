from sqlalchemy import or_
from flask import Blueprint, flash, redirect, render_template, session, url_for,request, jsonify
from .auth import login_required
from .models import Product, Cart, Testimonial, User
from . import db

views = Blueprint('views', __name__)

def get_testimonials_from_database():
    testimonials = Testimonial.query.all()
    return testimonials

@views.route('/')
def home():
    testimonials = get_testimonials_from_database()
    return render_template("index.html",testimonials=testimonials)

@views.route('/index')
def index():
    testimonials = get_testimonials_from_database()
    return render_template("index.html",testimonials=testimonials)

@views.route('/about')
def about():
    return render_template("about.html")

@views.route('/contact')
def contact():
    return render_template("contact.html")

@views.route('/products')
def products():
    products = Product.query.all()
    return render_template("products.html", products=products)

@views.route("/profile")
@login_required
def profile():
    # Şu anki oturum açmış kullanıcının e-posta adresini al
    email = session.get("email")

    # Veritabanından kullanıcıyı bul
    user = User.query.filter_by(email=email).first()

    if user:
        # Kullanıcının adını ve e-posta adresini al
        user_name = user.name
        user_email = user.email

        return render_template("profile.html", user_name=user_name, user_email=user_email)
    else:
        flash("Kullanıcı bulunamadı.", "danger")
        return redirect(url_for("views.index"))

@views.route('/cart')
def cart():
    cart_items = Cart.query.all()
    return render_template("cart.html", cart_items = cart_items)


@views.route("/testimonial")
def testimonial():
    testimonials = Testimonial.query.order_by(Testimonial.timestamp.desc()).limit(5).all()
    return render_template('testimonial.html', testimonials=testimonials)


@views.route('/search_products')
def search_products():
    term = request.args.get('term', '')
    matching_products = Product.query.filter(Product.name.ilike(f"%{term}%")).all()
    serialized_products = [{'name': product.name, 'price': product.price, 'image_url': product.image_url} for product in matching_products]
    return jsonify(serialized_products)