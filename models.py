from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'owner', 'buyer', 'seller'
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    membership_status = db.Column(db.String(10), nullable=True)  # 'free' or 'premium'
    account_status = db.Column(db.String(10), nullable=False, default='active')  # 'active', 'suspended', 'deleted'
    premium = db.Column(db.Boolean, default=False)  # Is the seller premium
    storage_count = db.Column(db.Integer, default=0)  # Track the number of products in the warehouse

    @property
    def is_active(self):
        return self.account_status == 'active'
    

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    upload_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="pending")  # 'pending', 'approved', 'rejected'
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # The seller
    warehouse_status = db.Column(db.String(20), default="not_stored")  # 'stored', 'not_stored'
    review_count = db.Column(db.Integer, default=0)
    total_rating = db.Column(db.Float, default=0.0)  # Total rating sum
    stock = db.Column(db.Integer, default=0)  # Number of products available to the buyer
    original_price = db.Column(db.Float, nullable=False)
    is_auctioned = db.Column(db.Boolean, default=False)
    upload_time = db.Column(db.DateTime)
    image_url = db.Column(db.String(200), nullable=True)
    # Relationship with the User table
    owner = db.relationship('User', backref=db.backref('products', lazy=True))
    
    # Relationship for reviews
    reviews = db.relationship('Review', backref='product', lazy=True)

    def average_rating(self):
        return self.total_rating / self.review_count if self.review_count > 0 else 0


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # Rating between 1-5
    comment = db.Column(db.Text)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship with User table (buyer)
    buyer = db.relationship('User', backref=db.backref('reviews', lazy=True))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="pending")  # 'pending', 'shipped', 'delivered', 'cancelled'
    order_date = db.Column(db.DateTime)
    total_price = db.Column(db.Float, nullable=False)

    # Relationships
    buyer = db.relationship('User', backref=db.backref('orders', lazy=True))
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    # Relationships
    buyer = db.relationship('User', backref=db.backref('wishlist', lazy=True))
    product = db.relationship('Product', backref=db.backref('wishlist', lazy=True))
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    # Relationships
    buyer = db.relationship('User', backref=db.backref('cart', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart', lazy=True))

class WarehouseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime)

    product = db.relationship('Product', backref='warehouse_requests')
    seller = db.relationship('User', backref='warehouse_requests')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)

    # Relationships
    order = db.relationship('Order', backref=db.backref('items', lazy=True))
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))
