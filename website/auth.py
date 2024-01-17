from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, render_template, redirect, url_for, request, flash, session, abort
from flask_bcrypt import bcrypt
from passlib.hash import sha256_crypt
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, TextAreaField, validators
from .models import Testimonial, User, Newsletter, Callback, Cart
from . import ADMIN_EMAIL, db, is_admin

auth = Blueprint('auth', __name__)


# User Login
@auth.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        email = form.email.data
        password_entered = form.password.data
        
        user = User.query.filter_by(email=email).first()
        if user and sha256_crypt.verify(password_entered, user.password):
            session["logged_in"] = True
            session["email"] = email
            flash("You have successfully logged in...", "success")
            return redirect(url_for("views.index"))  
        else:
            flash("Username or password is incorrect!", "danger")
            return redirect(url_for("auth.login"))  
    return render_template("login.html", form=form)


# User Register
@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("You have been successfully registered...", "success")
        return redirect(url_for("auth.login"))  
    return render_template("login.html", form=form)

       
# User Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page!", "danger")
            return redirect(url_for("auth.login"))
    return decorated_function 
    
      
  # User Login Form
class LoginForm(Form):
    email = StringField("Email")
    password = PasswordField("Password")   
    
    
# User Register Form
class RegisterForm(Form):
    name = StringField("Name and Surname", validators=[validators.Length(min=4, max=25)])
    email = StringField("E-Mail", validators=[validators.Email(message="Please Enter a Valid Email Address...")])
    password = PasswordField("Password", validators=[
        validators.DataRequired(message="Please Enter a Password..."),
        validators.EqualTo(fieldname="confirm", message="Entered Passwords Do Not Match...")
    ])
    confirm = PasswordField("Verify Password")
    
    
# Subscriber Button
@auth.route('/subscribe', methods=['POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form.get('email')

        if email:
            existing_subscriber = Newsletter.query.filter_by(email=email).first()

            if existing_subscriber:
                flash('You are already subscribed!', 'info')
            else:
                new_subscriber = Newsletter(email=email)
                db.session.add(new_subscriber)
                db.session.commit()
                flash('Subscription successful! Thank you for subscribing.', 'success')

        else:
            flash('Email address is required!', 'danger')

    return redirect(url_for('views.index'))


# Callback Function
@auth.route('/request-callback', methods=['POST'])
def request_callback():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        message = request.form.get('message')

        # Yeni bir Callback objesi oluşturup veritabanına kaydediyoruz
        new_callback = Callback(full_name=full_name, phone_number=phone_number, email=email, message=message)
        db.session.add(new_callback)
        db.session.commit()

        flash('Your request has been submitted. We will contact you soon.', 'success')
        return redirect(url_for('views.index'))

    flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('views.index'))



@auth.route("/logout")
def logout():
    session.clear()
    flash("Logged out succesfully...", "success")
    return redirect(url_for("views.index"))


@auth.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()

    # Veritabanına eklemek için yeni bir CartItem oluşturun
    cart_item = Cart(name=data['name'],image_path=data.get('imagePath'), image_url=data.get('imageUrl'), price=data['price'])

    try:
        # Veritabanına ekleyin ve değişiklikleri kaydedin
        db.session.add(cart_item)
        db.session.commit()
        flash('Product added cart succesfully', 'success')
    except Exception as e:
        # Hata durumunda geri dönün
        db.session.rollback()
        flash(f'Hata: {str(e)}', 'error')

    finally:
        # Her durumda veritabanı oturumunu kapatın
        db.session.close()

    return redirect(url_for('views.cart'))  # Yönlendireceğiniz sayfanın adını belirtin


@auth.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()

    # Sileceğimiz ürünü belirleyin, örneğin isme göre
    item_to_remove = Cart.query.filter_by(name=data['name']).first()

    if item_to_remove:
        try:
            # Veritabanından ürünü silin
            db.session.delete(item_to_remove)
            db.session.commit()

            # Başarılı bir şekilde silindiğine dair bir flash mesaj ekleyin
            flash('Product removed from cart successfully', 'success')
            return jsonify({'message': 'Product removed from cart successfully'})
        except Exception as e:
            # Hata durumunda geri dönün
            db.session.rollback()

            # Hata mesajını flash ile ekleyin
            flash(f'Error: {str(e)}', 'error')
            return jsonify({'error': str(e)}), 500
        finally:
            # Her durumda veritabanı oturumunu kapatın
            db.session.close()
    else:
        # Ürün bulunamazsa flash ile bir hata mesajı ekleyin
        flash('Product not found in cart', 'error')
        return jsonify({'error': 'Product not found in cart'}), 404
    
    
    
   #Testimonial Add
@auth.route('/add_testimonial', methods=['POST'])
def add_testimonial():
    client_name = request.form['client_name']
    profession = request.form['profession']
    comment = request.form['comment']

    new_testimonial = Testimonial(client_name=client_name, profession=profession, comment=comment)
    db.session.add(new_testimonial)
    db.session.commit()

    return redirect(url_for('views.testimonial'))



# Create or edit users in the admin panel
@auth.route('/create_or_edit_user', methods=['POST'])
def create_or_edit_user():
    if not is_admin():
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('admin.index'))