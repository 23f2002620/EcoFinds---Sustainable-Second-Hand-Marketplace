import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_bcrypt import Bcrypt
from email_validator import validate_email, EmailNotValidError
from datetime import datetime

# --- App setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecofinds.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_pic = db.Column(db.String(255), default="https://via.placeholder.com/150")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    year = db.Column(db.String(10))
    dimensions = db.Column(db.String(100))
    weight = db.Column(db.String(50))
    material = db.Column(db.String(50))
    color = db.Column(db.String(50))
    original_packaging = db.Column(db.Boolean, default=False)
    manual_included = db.Column(db.Boolean, default=False)
    working_desc = db.Column(db.Text)
    image_url = db.Column(db.String(255), default="https://via.placeholder.com/200")
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    seller = db.relationship('User', backref='products')
    status = db.Column(db.String(20), default="Available")

# In your models section
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product')


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user = db.relationship('User', backref='purchases')
    product = db.relationship('Product')

# --- Login manager ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes: Auth ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        display_name = request.form['display_name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm']
        # Validation
        try:
            validate_email(email)
        except EmailNotValidError:
            flash("Invalid email address", "danger")
            return render_template('signup.html')
        if not display_name or not email or not password or not confirm:
            flash("All fields required.", "danger")
            return render_template('signup.html')
        if User.query.filter((User.email==email)|(User.display_name==display_name)).first():
            flash("Email or display name already exists.", "danger")
            return render_template('signup.html')
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template('signup.html')
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template('signup.html')
        # Create user
        user = User(display_name=display_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_name = request.form['email_or_name'].strip()
        password = request.form['password']
        user = User.query.filter(
            (User.email==email_or_name)|(User.display_name==email_or_name)
        ).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for('login'))

# --- Routes: Dashboard/Profile ---
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        display_name = request.form['display_name'].strip()
        email = request.form['email'].strip().lower()
        # Validation
        if not display_name or not email:
            flash("Fields cannot be empty.", "danger")
        elif User.query.filter(User.display_name==display_name, User.id!=current_user.id).first():
            flash("Display name already taken.", "danger")
        elif User.query.filter(User.email==email, User.id!=current_user.id).first():
            flash("Email already taken.", "danger")
        else:
            current_user.display_name = display_name
            current_user.email = email
            db.session.commit()
            flash("Profile updated.", "success")
    return render_template('dashboard.html')

# --- Routes: Product CRUD ---
@app.route('/my_listings')
@login_required
def my_listings():
    products = Product.query.filter_by(seller_id=current_user.id).all()
    return render_template('my_listings.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    categories = ["Books", "Electronics", "Clothing", "Furniture", "Other"]
    if request.method == 'POST':
        p = Product(
            title=request.form['title'],
            category=request.form['category'],
            description=request.form['description'],
            price=float(request.form['price']),
            condition=request.form.get('condition'),
            brand=request.form.get('brand'),
            model=request.form.get('model'),
            year=request.form.get('year'),
            dimensions=request.form.get('dimensions'),
            weight=request.form.get('weight'),
            material=request.form.get('material'),
            color=request.form.get('color'),
            original_packaging=bool(request.form.get('original_packaging')),
            manual_included=bool(request.form.get('manual_included')),
            working_desc=request.form.get('working_desc'),
            image_url=request.form.get('image_url') or "https://via.placeholder.com/200",
            seller_id=current_user.id
        )
        db.session.add(p)
        db.session.commit()
        flash("Product added!", "success")
        return redirect(url_for('my_listings'))
    return render_template('add_product.html', categories=categories)

# Add to cart
@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id, 
        product_id=product_id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id
        )
        db.session.add(cart_item)
    
    db.session.commit()
    return redirect(url_for('cart'))

# Remove from cart
@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # Get current user's cart items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    # Process checkout (e.g., create order, charge payment, clear cart)
    # Example:
    for item in cart_items:
        purchase = Purchase(
            user_id=current_user.id,
            product_id=item.product_id
        )
        db.session.add(purchase)
        db.session.delete(item)
    
    db.session.commit()
    flash('Checkout successful!', 'success')
    return redirect(url_for('my_purchases'))


@app.route('/edit_product/<int:pid>', methods=['GET', 'POST'])
@login_required
def edit_product(pid):
    product = Product.query.get_or_404(pid)
    if product.seller_id != current_user.id:
        abort(403)
    categories = ["Books", "Electronics", "Clothing", "Furniture", "Other"]
    if request.method == 'POST':
        product.title = request.form['title']
        product.category = request.form['category']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.condition = request.form.get('condition')
        product.brand = request.form.get('brand')
        product.model = request.form.get('model')
        product.year = request.form.get('year')
        product.dimensions = request.form.get('dimensions')
        product.weight = request.form.get('weight')
        product.material = request.form.get('material')
        product.color = request.form.get('color')
        product.original_packaging = bool(request.form.get('original_packaging'))
        product.manual_included = bool(request.form.get('manual_included'))
        product.working_desc = request.form.get('working_desc')
        product.image_url = request.form.get('image_url') or "https://via.placeholder.com/200"
        db.session.commit()
        flash("Product updated!", "success")
        return redirect(url_for('my_listings'))
    return render_template('edit_product.html', product=product, categories=categories)

@app.route('/delete_product/<int:pid>')
@login_required
def delete_product(pid):
    product = Product.query.get_or_404(pid)
    if product.seller_id == current_user.id:
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "info")
    return redirect(url_for('my_listings'))

# --- Routes: Purchases ---
@app.route('/buy/<int:pid>')
@login_required
def buy(pid):
    product = Product.query.get_or_404(pid)
    if product.status != "Available" or product.seller_id == current_user.id:
        flash("Not available for purchase.", "danger")
        return redirect(url_for('browse'))
    product.status = "Sold"
    purchase = Purchase(user_id=current_user.id, product_id=product.id)
    db.session.add(purchase)
    db.session.commit()
    flash("Purchased!", "success")
    return redirect(url_for('my_purchases'))

@app.route('/my_purchases')
@login_required
def my_purchases():
    purchases = Purchase.query.filter_by(user_id=current_user.id).all()
    return render_template('my_purchases.html', purchases=purchases)

# --- Routes: Product Browsing ---
@app.route('/')
@app.route('/browse')
def browse():
    q = request.args.get('q', '').strip()
    cat = request.args.get('category', '')
    products = Product.query.filter_by(status="Available")
    if q:
        products = products.filter(Product.title.ilike(f'%{q}%'))
    if cat:
        products = products.filter_by(category=cat)
    products = products.all()
    categories = ["Books", "Electronics", "Clothing", "Furniture", "Other"]
    return render_template('browse.html', products=products, categories=categories, q=q, cat=cat)

@app.route('/product/<int:pid>')
def product_detail(pid):
    product = Product.query.get_or_404(pid)
    return render_template('product_detail.html', product=product)

# Add this to your routes in app.py
@app.route('/cart')
@login_required  # If login is required
def cart():
    # Get cart items for the current user
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    # Calculate total
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total)


# --- DB Init ---
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")

if __name__ == "__main__":
    if not os.path.exists("ecofinds.db"):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
