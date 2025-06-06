from flask import Flask, render_template, request, redirect, url_for, flash,session
from models import db, User, Product, Order,Wishlist, Cart,WarehouseRequest,Wishlist,OrderItem
from flask_login import login_user, current_user,LoginManager,logout_user, login_required
from werkzeug.security import generate_password_hash,check_password_hash
from flask_migrate import Migrate
import os
from flask import send_from_directory
from flask import send_file
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'

app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Initialize the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if not authenticated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         # Process the form data
#         pass
#     return render_template('register.html')  # Ensure the file is in the templates folder


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        role = request.form['role']

        # Validate passwords match
        if password != confirm_password:
            flash("Passwords do not match", 'danger')
            return redirect(url_for('register'))

        # Hash the password
        password_hash = generate_password_hash(password)

        # Create a new user instance
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            first_name=first_name,
            last_name=last_name,
            account_status='active'
        )

        try:
            # Add the new user to the database
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!", 'success')
            return redirect(url_for('login'))  # Redirect to login page after successful registration
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/')
def home():
    try:
        # Initialize variables for users who are not logged in
        current_user_data = None
        user_role = None
        is_premium = None
        membership_status = None
        profile_picture = "default-profile-picture.jpg"  # Default picture if no user is logged in
        team_members = []  # Default empty list for team
        clients = []  # Default empty list for clients
        
        # If the user is logged in, fetch the user data
        if current_user.is_authenticated:
            current_user_data = current_user
            user_role = current_user.role
            is_premium = current_user.premium
            membership_status = current_user.membership_status
            profile_picture = current_user.profile_picture or "default-profile-picture.jpg"  # Use default if no profile picture is set

            # Add users to "team" section if the user is an owner
            if user_role == 'owner':
                team_members = [
                    {'name': 'Parveen Anand', 'role': 'Lead Designer', 'img': 'assets/img/team/1.jpg'},
                    {'name': 'Diana Petersen', 'role': 'Lead Marketer', 'img': 'assets/img/team/2.jpg'},
                    {'name': 'Larry Parker', 'role': 'Lead Developer', 'img': 'assets/img/team/3.jpg'}
                ]
            # Add logos to "clients" section if the user is a seller
            if user_role == 'seller':
                clients = [
                    {'logo': 'assets/img/logos/microsoft.svg', 'link': '#!'},
                    {'logo': 'assets/img/logos/google.svg', 'link': '#!'},
                    {'logo': 'assets/img/logos/facebook.svg', 'link': '#!'},
                    {'logo': 'assets/img/logos/ibm.svg', 'link': '#!'}
                ]

        # Render the page for all users (logged in or not)
        return render_template('index.html', 
                               current_user=current_user_data, 
                               user_role=user_role,
                               is_premium=is_premium, 
                               membership_status=membership_status, 
                               profile_picture=profile_picture,
                               team_members=team_members,  # Pass team members data
                               clients=clients)  # Pass clients data

    except Exception as e:
        app.logger.error(f"Error rendering index page: {e}")
        return "An error occurred while rendering the page.", 500




@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    app.logger.debug("Logout route accessed")  # Add this line
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

from datetime import datetime, timedelta
from sqlalchemy import func, extract

@app.route('/seller/dashboard', methods=['GET'])
@login_required
def seller_dashboard():
    app.logger.debug(f"Session Data: {session}")
    app.logger.debug(f"Current User: {current_user.id}, Is Authenticated: {current_user.is_authenticated}")
    
    if current_user.role != 'seller':
        flash('Access denied! You must be a seller.', 'danger')
        return redirect(url_for('home'))

    # Fetch seller's products
    products = Product.query.filter_by(owner_id=current_user.id).all()
    updated = False

    # Add order_count and wishlist_count for each product
    for product in products:
        # Count orders for each product via the OrderItem table
        product.order_count = db.session.query(OrderItem).join(Order).filter(OrderItem.product_id == product.id, Order.status == 'pending').count()
        product.wishlist_count = Wishlist.query.filter_by(product_id=product.id).count()

        # Price reduction and auction logic
        if product.upload_time and product.original_price:
            time_in_warehouse = datetime.utcnow() - product.upload_time
            if time_in_warehouse > timedelta(days=90):  # over 3 months
                weeks_over = (time_in_warehouse.days - 90) // 7
                total_deduction = weeks_over * 100
                new_price = max(product.original_price - total_deduction, 0)
                percentage_loss = ((product.original_price - new_price) / product.original_price) * 100

                if product.price != new_price:
                    product.price = new_price
                    updated = True

                if percentage_loss >= 9 and not product.is_auctioned:
                    product.is_auctioned = True
                    updated = True

    if updated:
        db.session.commit()

    # Fetch pending orders for this seller's products
    product_ids = [p.id for p in products]
    orders = Order.query.filter(OrderItem.product_id.in_(product_ids), Order.status == 'pending').all()

    # Calculate monthly earnings and order count
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    monthly_data = (
    db.session.query(func.sum(OrderItem.total_price), func.count(OrderItem.id))
    .join(Order)
    .join(Product)
    .filter(
        Product.owner_id == current_user.id,
        Order.status == 'delivered',
        extract('month', Order.order_date) == current_month,
        extract('year', Order.order_date) == current_year
    )
    .first()
    )


    monthly_earning = monthly_data[0] or 0
    monthly_sales_count = monthly_data[1] or 0

    return render_template(
        'seller_dashboard.html',
        products=products,
        orders=orders,
        monthly_earning=monthly_earning,
        monthly_sales_count=monthly_sales_count
    )

@app.route('/seller/inventory_permission', methods=['GET'])
@login_required
def inventory_permission():
    if current_user.role != 'seller':
        flash('You must be a seller to access this feature.', 'danger')
        return redirect(url_for('home'))

    # Check if the seller has exceeded their inventory limit
    inventory_limit = 100  # Example limit
    if current_user.storage_count >= inventory_limit:
        flash('You have reached your inventory limit! Please contact the admin.', 'warning')
    else:
        flash(f'You can add {inventory_limit - current_user.storage_count} more products to your inventory.', 'info')

    return redirect(url_for('seller_dashboard'))



from datetime import datetime
from flask import request
from werkzeug.utils import secure_filename

@app.route('/seller/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'seller':
        flash('Access denied! You must be a seller.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        size = request.form['size']
        category = request.form['category']
        brand = request.form['brand']
        stock = int(request.form['stock'])

        # Handling image upload
        image = request.files.get('image')
        image_url = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image_url = f'uploads/{filename}'
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure the directory exists
            image.save(upload_path)
            print(f"Image saved at: {upload_path}")
        else:
            print("No image uploaded or invalid file.")



        # Create a new product
        new_product = Product(
            name=name,
            description=description,
            price=price,
            original_price=price,
            size=size,
            category=category,
            brand=brand,
            owner_id=current_user.id,
            stock=stock,
            image_url=image_url
        )
        db.session.add(new_product)
        db.session.commit()

        # Update seller's storage count
        current_user.storage_count += stock
        db.session.commit()

        flash('New product added successfully!', 'success')
        return redirect(url_for('seller_dashboard'))

    return render_template('add_product.html')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'owner':
        flash('Access denied! You must be an admin.', 'danger')
        return redirect(url_for('home'))

    pending_products = Product.query.filter_by(status='pending').all()
    sellers = User.query.filter_by(role='seller').all()

    seller_stats = []
    for seller in sellers:
        # Get all order items where the product belongs to this seller
        seller_order_items = (
            OrderItem.query
            .join(Product, OrderItem.product_id == Product.id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Product.owner_id == seller.id, Order.status == 'delivered')
            .all()
        )

        total_sales = sum(item.quantity for item in seller_order_items)
        total_earnings = sum(item.total_price for item in seller_order_items)

        seller_products = Product.query.filter_by(owner_id=seller.id).all()
        total_reviews = sum(product.review_count for product in seller_products)

        seller_stats.append({
            'seller': seller,
            'total_sales': total_sales,
            'total_earnings': total_earnings,
            'total_reviews': total_reviews
        })

    ranked_sellers = sorted(seller_stats, key=lambda x: x['total_sales'], reverse=True)

    warehouse_requests = WarehouseRequest.query.filter_by(status='Pending').all()
    pending_orders = Order.query.filter_by(status='pending').all()

    return render_template('admin_dashboard.html',
                           pending_products=pending_products,
                           sellers=sellers,
                           ranked_sellers=ranked_sellers,
                           warehouse_requests=warehouse_requests,
                           pending_orders=pending_orders)


@app.route('/admin/confirm_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    if current_user.role != 'owner':
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    order = Order.query.get_or_404(order_id)
    if order.status == 'pending':
        order.status = 'delivered'
        db.session.commit()
        flash(f'Order #{order.id} confirmed as delivered.', 'success')
    else:
        flash('Order is not pending.', 'warning')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    if current_user.role != 'owner':
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    order = Order.query.get_or_404(order_id)
    if order.status == 'pending':
        for item in order.items:
            item.product.stock += item.quantity
        order.status = 'cancelled'
        db.session.commit()
        flash(f'Order #{order.id} has been cancelled. Inventory updated.', 'danger')
    else:
        flash('Order is not pending.', 'warning')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/approve/<int:product_id>', methods=['POST'])
@login_required
def approve_product(product_id):
    if current_user.role != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    product = Product.query.get_or_404(product_id)
    product.status = "approved"
    db.session.commit()

    flash('Product has been approved!', 'success')
    return redirect(url_for('admin_dashboard'))




@app.route('/admin/warehouse/approve/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    if current_user.role != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    req = WarehouseRequest.query.get_or_404(request_id)
    req.status = 'Approved'
    req.product.warehouse_status = 'In Warehouse'
    db.session.commit()

    flash('Warehouse request approved.', 'success')
    return redirect(url_for('admin_dashboard'))

##################
@app.route('/admin/warehouse/reject/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    if current_user.role != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    req = WarehouseRequest.query.get_or_404(request_id)
    req.status = 'Rejected'
    db.session.commit()

    flash('Warehouse request rejected.', 'info')
    return redirect(url_for('admin_dashboard'))

# app.py or wherever your Flask routes are defined

from flask import render_template, request
from app import db
from models import Product

@app.route('/products')
def all_products():
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'price')
    sort_order = request.args.get('sort_order', 'asc')

    # Filter products based on search query (if provided)
    products_query = Product.query
    if search_query:
        products_query = products_query.filter(Product.name.like(f'%{search_query}%'))

    # Sort products based on selected criteria
    if sort_by == 'price':
        products_query = products_query.order_by(Product.price.asc() if sort_order == 'asc' else Product.price.desc())
    elif sort_by == 'seller':
        products_query = products_query.join(User).order_by(User.username.asc() if sort_order == 'asc' else User.username.desc())
    elif sort_by == 'brand':
        products_query = products_query.order_by(Product.brand.asc() if sort_order == 'asc' else Product.brand.desc())

    # Pagination: 12 items per page
    page = request.args.get('page', 1, type=int)
    products = products_query.paginate(page=page, per_page=8, error_out=False)

    return render_template('all_products.html', products=products.items, pagination=products)




from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import app, db
from models import Product, Order, Review, Wishlist, Cart, User
@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_detail(product_id):
    # Fetch the product
    product = Product.query.get_or_404(product_id)

    # Fetch reviews for the product
    reviews = Review.query.filter_by(product_id=product.id).all()

    # Initialize variables for seller-specific data
    reviews_data = []
    ratings = []
    total_sales = 0
    orders = []
    avg_rating = 0

    # If the current user is a buyer, handle the review form submission
    if current_user.role == 'buyer' and request.method == 'POST':
        if Order.query.filter_by(product_id=product.id, buyer_id=current_user.id, status='completed').first():
            rating = request.form.get('rating')
            comment = request.form.get('review')
            new_review = Review(
                rating=rating,
                comment=comment,
                product_id=product.id,
                buyer_id=current_user.id
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Your review has been submitted!', 'success')
        else:
            flash('You can only review products you have purchased.', 'danger')
        
        return redirect(url_for('product_detail', product_id=product.id))

    # Handle seller-specific actions
    if current_user.role == 'seller' and product.owner_id == current_user.id:
        if request.method == 'POST' and 'send_to_warehouse' in request.form:
            # Logic to request the warehouse
            existing_request = WarehouseRequest.query.filter_by(product_id=product.id, seller_id=current_user.id, status='Pending').first()
            if existing_request:
                flash('You have already requested to send this product to the warehouse.', 'warning')
            else:
                warehouse_request = WarehouseRequest(
                    product_id=product.id,
                    seller_id=current_user.id,
                    status='Pending',
                    created_at=datetime.utcnow()
                )
                db.session.add(warehouse_request)
                db.session.commit()
                flash('Your request to send the product to the warehouse has been submitted.', 'success')

            return redirect(url_for('product_detail', product_id=product.id))

        # Fetch reviews, ratings, total sales, and orders for the seller's product
        reviews_data = Review.query.filter_by(product_id=product.id).all()
        ratings = [review.rating for review in reviews_data]
        
        # Query OrderItem model for total sales and orders for the seller's product
        total_sales = db.session.query(OrderItem).join(Order).filter(OrderItem.product_id == product.id, Order.status == 'completed').count()
        orders = db.session.query(Order).join(OrderItem).filter(OrderItem.product_id == product.id).all()

        # Calculate the average rating
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
    # Check if user is eligible to review this product
    eligible_to_review = False
    if current_user.is_authenticated:
        user_orders = Order.query.filter_by(buyer_id=current_user.id, status='delivered').all()
        for order in user_orders:
            order_items = OrderItem.query.filter_by(order_id=order.id, product_id=product.id).first()
            if order_items:
                eligible_to_review = True
                break

    return render_template('product_detail.html', 
                           product=product, 
                           reviews=reviews, 
                           reviews_data=reviews_data,
                           avg_rating=avg_rating, 
                           total_sales=total_sales, 
                           orders=orders, 
                           current_user=current_user,
                           eligible_to_review=eligible_to_review)
@app.route('/submit_review/<int:product_id>', methods=['POST'])
@login_required
def submit_review(product_id):
    rating = int(request.form['rating'])
    comment = request.form['comment']

    review = Review(user_id=current_user.id, product_id=product_id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()

    flash('Review submitted successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/product/<int:product_id>/request_to_warehouse', methods=['POST'])
@login_required
def request_to_warehouse(product_id):
    product = Product.query.get_or_404(product_id)

    if product.owner_id != current_user.id:
        flash('You do not have permission to request this product.', 'danger')
        return redirect(url_for('product_detail', product_id=product.id))

    if current_user.role == 'seller' and current_user.storage_count >= 5 and not current_user.premium:
        flash('Limit reached: Non-premium sellers can request only 5 items.', 'danger')
        return redirect(url_for('product_detail', product_id=product.id))

    # Check if already requested
    existing_request = WarehouseRequest.query.filter_by(product_id=product.id, seller_id=current_user.id, status='Pending').first()
    if existing_request:
        flash('You have already requested this product.', 'info')
        return redirect(url_for('product_detail', product_id=product.id))

    # Create a new warehouse request
    new_request = WarehouseRequest(product_id=product.id, seller_id=current_user.id)
    db.session.add(new_request)
    db.session.commit()

    flash('Request sent to admin for approval.', 'success')
    return redirect(url_for('product_detail', product_id=product.id))

@app.route('/admin/warehouse_requests', methods=['GET', 'POST'])
@login_required
def warehouse_requests():
    if current_user.role != 'owner':
        flash('Access denied! You must be an admin.', 'danger')
        return redirect(url_for('home'))

    # Fetch all pending warehouse requests
    requests = WarehouseRequest.query.filter_by(status='Pending').all()

    if request.method == 'POST':
        # Handle approval or rejection
        request_id = request.form.get('request_id')
        action = request.form.get('action')
        warehouse_request = WarehouseRequest.query.get(request_id)

        return redirect(url_for('warehouse_requests'))

    return render_template('admin_warehouse_requests.html', requests=requests)

@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    existing = Wishlist.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    if not existing:
        item = Wishlist(buyer_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
    return redirect(request.referrer or url_for('all_products'))


# @app.route('/cart/add/<int:product_id>', methods=['POST'])
# @login_required
# def add_to_cart(product_id):
#     item = Cart.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
#     if item:
#         item.quantity += 1
#     else:
#         item = Cart(buyer_id=current_user.id, product_id=product_id, quantity=1)
#         db.session.add(item)
#     db.session.commit()
#     return redirect(request.referrer or url_for('all_products'))

# Merged Wishlist and Cart View with Buy All, Update Quantity, Remove Options


@app.route('/wishlist-cart')
@login_required
def wishlist_cart():
    wishlist_products = [w.product for w in Wishlist.query.filter_by(buyer_id=current_user.id).all()]
    cart_items = Cart.query.filter_by(buyer_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)

    return render_template('wishlist_cart.html', 
                           wishlist_items=wishlist_products, 
                           cart_items=cart_items, 
                           total=total, 
                           address=current_user.address)

@app.route('/remove-from-wishlist/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    item = Wishlist.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Removed from wishlist', 'success')
    return redirect(url_for('wishlist_cart'))

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    item = Cart.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Removed from cart', 'success')
    return redirect(url_for('wishlist_cart'))

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    item = Cart.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = Cart(buyer_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(item)
    db.session.commit()
    flash('Added to cart', 'success')
    return redirect(url_for('wishlist_cart'))

# @app.route('/cart/add/<int:product_id>', methods=['POST'])
# @login_required
# def add_to_cart(product_id):
#     item = Cart.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
#     if item:
#         item.quantity += 1
#     else:
#         item = Cart(buyer_id=current_user.id, product_id=product_id, quantity=1)
#         db.session.add(item)
#     db.session.commit()
#     return redirect(request.referrer or url_for('all_products'))



@app.route('/update-cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    item = Cart.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    if item:
        item.quantity = max(1, quantity)
        db.session.commit()
        flash('Cart updated', 'success')
    return redirect(url_for('wishlist_cart'))


@app.route('/buy-all', methods=['POST'])
@login_required
def buy_all():
    cart_items = Cart.query.filter_by(buyer_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('wishlist_cart'))

    # Calculate total price for all items in the cart
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Create a single order for the entire cart (no product_id here)
    order = Order(
        buyer_id=current_user.id,
        status='pending',
        order_date=datetime.now(),
        total_price=total_price
    )
    db.session.add(order)
    db.session.commit()  # Commit the order so that order.id is available

    # Add order items (cart items) to the order
    for item in cart_items:
        if item.product_id is not None:  # Check if product_id is valid
            order_item = OrderItem(
                order_id=order.id,  # Link the order_id to the newly created order
                product_id=item.product_id,  # Assign the correct product_id
                quantity=item.quantity,
                total_price=item.product.price * item.quantity
            )
            db.session.add(order_item)

            # Decrease the stock by the quantity purchased
            product = Product.query.get(item.product_id)
            if product:
                product.stock -= item.quantity
                db.session.add(product)

            # Remove the item from the cart
            db.session.delete(item)
        else:
            # Log the error or handle it gracefully
            flash(f"Product with ID {item.product_id} is invalid or missing.", 'error')
    
    db.session.commit()
    flash('All items purchased successfully!', 'success')
    return redirect(url_for('wishlist_cart'))
@app.route('/product/<int:product_id>/update', methods=['GET', 'POST'])
@login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Only allow the owner to update
    if current_user.id != product.owner_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('product_detail', product_id=product.id))

    if request.method == 'POST':
        # Basic fields
        product.name = request.form['name']
        product.brand = request.form['brand']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.description = request.form['description']

        # Image (optional)
        image = request.files.get('image')
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            product.image_url = f"uploads/{filename}"

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('product_detail', product_id=product.id))

    return render_template('update_product.html', product=product)

from werkzeug.utils import secure_filename


from werkzeug.utils import secure_filename
import os

# Define a folder for saving profile pictures (make sure it's created)
PROFILE_PIC_FOLDER = 'static/profile_pics'

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_picture = request.files.get('profile_picture')

        # Update user fields
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.username = username
        current_user.email = email
        current_user.address = address
        current_user.contact_number = contact_number

        # Handle password update (only if both fields are filled and match)
        if password:
            if password == confirm_password:
                current_user.password = generate_password_hash(password)
            else:
                flash("Passwords do not match.", "danger")
                return redirect(url_for('profile'))

        # Handle profile picture upload
        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            profile_picture_url = f'uploads/{filename}'
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.profile_picture = profile_picture_url

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    # Fetch the user's orders with order items
    orders = Order.query.filter_by(buyer_id=current_user.id).all()
    
    order_details = []
    for order in orders:
        items = OrderItem.query.filter_by(order_id=order.id).all()
        order_item_details = []
        
        for item in items:
            product = Product.query.get(item.product_id)
            order_item_details.append({
                'product_name': product.name,
                'product_description': product.description,
                'product_price': product.price,
                'quantity': item.quantity,
                'total_price': item.total_price,
            })
        
        order_details.append({
            'order_id': order.id,
            'order_date': order.order_date,
            'status': order.status,
            'total_price': order.total_price,
            'items': order_item_details
        })

    return render_template('profile.html', user=current_user, order_details=order_details)


if __name__ == '__main__':
    app.run(debug=True)
