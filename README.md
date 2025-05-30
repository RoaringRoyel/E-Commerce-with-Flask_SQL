# Shoe Resale E-commerce Platform - Functional Requirement Document (FRD)
## 📋 Modules Overview

### 🔐 Module 0: Login & User Management
Handles user authentication and authorization for all roles.

**Functionalities:**
- User Registration
- Multiple User Login and Logout
- Password Reset

---

### 🛍️ Module 1: Buyer Portal & Shopping Cart
Allows buyers to browse, filter, and purchase shoes easily.

**Functionalities:**
- **Account Management:** Create, edit, and manage buyer profiles.
- **Product Uploading:** Sellers/Admins upload shoes with Name, Brand, Category, Price, etc.
- **Product Details Page:** View product descriptions, images, and condition.
- **Product Browsing & Filtering:** Filter by category, size, price, and brand.
- **Search:** Search shoes by name and category.
- **Wishlist:** Buyers can save products for later viewing (only for purchased products).
- **Add to Cart:** Add from wishlist or directly to cart with full view capability.

---

### 📈 Module 2: Buyer & Seller Dashboard
Interface for both sellers and buyers to manage products and purchases.

**Functionalities:**
- **Seller Product Management:** Upload and manage product listings.
- **Product Evaluation Request:** Send shoes for admin evaluation.
- **Buyer Orders:** View purchase history.
- **Wishlist Integration:** Buyers access saved items.
- **Cart Management:** Add/view cart items with product info.

---

### 🛠️ Module 3: Admin Panel & Product Evaluation
Used by the HQ team to evaluate and approve products and manage users.

**Functionalities:**
- **Product Approval:** Admin must approve uploaded products and purchase requests.
- **Highest Seller View:** Admin dashboard displays top sellers.
- **Sorting & Searching:** Full product list access with sort/search options.
- **Update Quantity:** Admins can update order quantities.
- **Admin Control:** Manage seller and buyer profiles.

---

### 💳 Module 4: Transaction & Payment System
Manages all payments and transaction-related processes.

**Functionalities:**
- **Secure Payment Gateway:** Supports credit card, debit card, PayPal, Bkash, etc.
- **Service Fee Deduction:** Automatically deducts 16.9% fee from sales.
- **Transaction History:** Viewable by both buyers and sellers.
- **Ride Cost Integration:** Adds delivery cost to final price.
- **Seller Payment Distribution:** Pays sellers post-fee and delivery deduction.

---

## 📌 Project Goals

The main objective of this platform is to create a structured, reliable, and secure system for reselling shoes through a buyer-seller-admin marketplace model with strong backend evaluation, payment, and inventory control.

