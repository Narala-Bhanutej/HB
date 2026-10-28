import os
import random
import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hostelbites-super-secret-key-2026")

# Hostels available for delivery
HOSTEL_BLOCKS = [
    "Hostel Block A (Boys)",
    "Hostel Block B (Boys)",
    "Hostel Block C (Boys)",
    "Hostel Block D (Girls)",
    "Hostel Block E (Girls)",
    "PG & Research Scholar Hostel"
]

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to proceed.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Admin login required.", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to inject cart count & user into all templates
@app.context_processor
def inject_global_data():
    cart = session.get("cart", {})
    cart_count = sum(item["quantity"] for item in cart.values())
    return {
        "cart_count": cart_count,
        "current_user_name": session.get("user_name"),
        "is_student_logged_in": "user_id" in session,
        "is_admin_logged_in": "admin_id" in session,
        "HOSTEL_BLOCKS": HOSTEL_BLOCKS
    }

# ==================== STUDENT AUTH ROUTES ====================

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        hostel_block = request.form.get("hostel_block", "").strip()
        room_no = request.form.get("room_no", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([name, roll_no, email, phone, hostel_block, room_no, password]):
            flash("All fields are required!", "danger")
            return render_template("register.html", hostels=HOSTEL_BLOCKS)

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template("register.html", hostels=HOSTEL_BLOCKS)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing roll no or email
        cursor.execute("SELECT id FROM users WHERE roll_no = ? OR email = ?", (roll_no, email))
        if cursor.fetchone():
            conn.close()
            flash("Student with this Roll Number or Email already exists!", "danger")
            return render_template("register.html", hostels=HOSTEL_BLOCKS)

        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (name, roll_no, email, phone, hostel_block, room_no, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, roll_no, email, phone, hostel_block, room_no, password_hash))
        conn.commit()

        # Fetch newly created user ID
        cursor.execute("SELECT id FROM users WHERE roll_no = ?", (roll_no,))
        new_user = cursor.fetchone()
        conn.close()

        # Auto login
        session["user_id"] = new_user["id"]
        session["user_name"] = name
        session["user_roll"] = roll_no
        session["user_hostel"] = hostel_block
        session["user_room"] = room_no
        session["user_phone"] = phone

        flash(f"Welcome to Hostel Bites, {name}! Your account has been registered.", "success")
        return redirect(url_for("index"))

    return render_template("register.html", hostels=HOSTEL_BLOCKS)

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip() # Roll No or Email
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Please enter both Roll No/Email and Password.", "warning")
            return render_template("login.html")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE roll_no = ? OR email = ?",
            (identifier.upper(), identifier.lower())
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_roll"] = user["roll_no"]
            session["user_hostel"] = user["hostel_block"]
            session["user_room"] = user["room_no"]
            session["user_phone"] = user["phone"]
            flash(f"Welcome back, {user['name']}!", "success")

            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        else:
            flash("Invalid credentials. Please verify your Roll Number/Email and Password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_roll", None)
    session.pop("user_hostel", None)
    session.pop("user_room", None)
    session.pop("user_phone", None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("index"))

# ==================== PUBLIC / MENU ROUTES ====================

@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    selected_category = request.args.get("category", "All")
    search_query = request.args.get("search", "").strip()
    dietary_filter = request.args.get("diet", "all") # 'veg', 'nonveg', 'all'

    # Fetch unique categories
    cursor.execute("SELECT DISTINCT category FROM menu_items ORDER BY category")
    categories = [row["category"] for row in cursor.fetchall()]

    query = "SELECT * FROM menu_items WHERE 1=1"
    params = []

    if selected_category and selected_category != "All":
        query += " AND category = ?"
        params.append(selected_category)

    if search_query:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if dietary_filter == "veg":
        query += " AND is_veg = 1"
    elif dietary_filter == "nonveg":
        query += " AND is_veg = 0"

    query += " ORDER BY is_available DESC, category ASC, id ASC"
    cursor.execute(query, params)
    items = cursor.fetchall()

    # Also fetch top recommended / popular items
    cursor.execute("SELECT * FROM menu_items WHERE is_available = 1 ORDER BY rating DESC LIMIT 4")
    featured_items = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        items=items,
        categories=categories,
        selected_category=selected_category,
        search_query=search_query,
        dietary_filter=dietary_filter,
        featured_items=featured_items
    )

# ==================== CART & CHECKOUT ====================

@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    subtotal = sum(item["price"] * item["quantity"] for item in cart.values())
    delivery_fee = 10.0 if (subtotal > 0 and subtotal < 150) else 0.0
    total = subtotal + delivery_fee

    # User profile prefill if logged in
    user_info = {
        "name": session.get("user_name", ""),
        "hostel": session.get("user_hostel", HOSTEL_BLOCKS[0]),
        "room": session.get("user_room", ""),
        "phone": session.get("user_phone", "")
    }

    return render_template(
        "cart.html",
        cart=cart,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        user_info=user_info,
        hostels=HOSTEL_BLOCKS
    )

@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json() or {}
    item_id = str(data.get("item_id"))
    quantity = int(data.get("quantity", 1))

    if not item_id:
        return jsonify({"success": False, "message": "Item ID required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()

    if not item:
        return jsonify({"success": False, "message": "Item not found"}), 404

    if not item["is_available"]:
        return jsonify({"success": False, "message": "Sorry, this item is currently sold out!"}), 400

    cart = session.get("cart", {})
    if item_id in cart:
        cart[item_id]["quantity"] += quantity
    else:
        cart[item_id] = {
            "id": item["id"],
            "name": item["name"],
            "price": float(item["price"]),
            "image_url": item["image_url"],
            "is_veg": item["is_veg"],
            "quantity": quantity
        }

    session["cart"] = cart
    session.modified = True

    total_count = sum(i["quantity"] for i in cart.values())
    subtotal = sum(i["price"] * i["quantity"] for i in cart.values())

    return jsonify({
        "success": True,
        "message": f"{item['name']} added to cart!",
        "cart_count": total_count,
        "subtotal": subtotal
    })

@app.route("/api/cart/update", methods=["POST"])
def update_cart_item():
    data = request.get_json() or {}
    item_id = str(data.get("item_id"))
    change = int(data.get("change", 0))

    cart = session.get("cart", {})
    if item_id in cart:
        new_qty = cart[item_id]["quantity"] + change
        if new_qty <= 0:
            cart.pop(item_id)
        else:
            cart[item_id]["quantity"] = new_qty

        session["cart"] = cart
        session.modified = True

    subtotal = sum(i["price"] * i["quantity"] for i in cart.values())
    delivery_fee = 10.0 if (subtotal > 0 and subtotal < 150) else 0.0
    total = subtotal + delivery_fee
    cart_count = sum(i["quantity"] for i in cart.values())

    return jsonify({
        "success": True,
        "cart_count": cart_count,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "item_qty": cart.get(item_id, {}).get("quantity", 0)
    })

@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    data = request.get_json() or {}
    item_id = str(data.get("item_id"))

    cart = session.get("cart", {})
    if item_id in cart:
        cart.pop(item_id)
        session["cart"] = cart
        session.modified = True

    subtotal = sum(i["price"] * i["quantity"] for i in cart.values())
    delivery_fee = 10.0 if (subtotal > 0 and subtotal < 150) else 0.0
    total = subtotal + delivery_fee
    cart_count = sum(i["quantity"] for i in cart.values())

    return jsonify({
        "success": True,
        "cart_count": cart_count,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total
    })

@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty! Add some delicious canteen bites first.", "warning")
        return redirect(url_for("index"))

    hostel_block = request.form.get("hostel_block", "").strip()
    room_no = request.form.get("room_no", "").strip()
    phone = request.form.get("phone", "").strip()
    delivery_notes = request.form.get("delivery_notes", "").strip()
    payment_method = request.form.get("payment_method", "Cash on Delivery")

    if not hostel_block or not room_no or not phone:
        flash("Please provide hostel, room number, and phone number for delivery.", "danger")
        return redirect(url_for("view_cart"))

    subtotal = sum(item["price"] * item["quantity"] for item in cart.values())
    delivery_fee = 10.0 if (subtotal > 0 and subtotal < 150) else 0.0
    total_amount = subtotal + delivery_fee

    # Generate a unique readable Order Number e.g. HB-8429
    order_number = f"HB-{datetime.datetime.now().strftime('%m%d')}-{random.randint(1000, 9999)}"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (
            order_number, user_id, hostel_block, room_no, phone,
            delivery_notes, payment_method, subtotal, delivery_fee, total_amount, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Placed')
    """, (
        order_number, session["user_id"], hostel_block, room_no, phone,
        delivery_notes, payment_method, subtotal, delivery_fee, total_amount
    ))
    order_id = cursor.lastrowid

    # Insert items
    for item in cart.values():
        cursor.execute("""
            INSERT INTO order_items (order_id, menu_item_id, item_name, item_price, quantity, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            order_id, item["id"], item["name"], item["price"],
            item["quantity"], item["price"] * item["quantity"]
        ))

    conn.commit()
    conn.close()

    # Clear session cart
    session["cart"] = {}
    session.modified = True

    return redirect(url_for("order_success", order_number=order_number))

@app.route("/order-success/<order_number>")
@login_required
def order_success(order_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders WHERE order_number = ? AND user_id = ?
    """, (order_number, session["user_id"]))
    order = cursor.fetchone()

    if not order:
        conn.close()
        flash("Order not found.", "warning")
        return redirect(url_for("index"))

    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
    items = cursor.fetchall()
    conn.close()

    return render_template("order_success.html", order=order, items=items)

# ==================== ORDER TRACKING ====================

@app.route("/my-orders")
@login_required
def my_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))
    orders = cursor.fetchall()

    detailed_orders = []
    for order in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
        items = cursor.fetchall()
        detailed_orders.append({
            "order": order,
            "order_items": items
        })

    conn.close()
    return render_template("orders.html", orders=detailed_orders)

@app.route("/track/<order_number>")
def track_order(order_number):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,))
    order = cursor.fetchone()

    if not order:
        conn.close()
        flash("Order number not found.", "danger")
        return redirect(url_for("index"))

    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
    items = cursor.fetchall()

    cursor.execute("SELECT name, roll_no FROM users WHERE id = ?", (order["user_id"],))
    student = cursor.fetchone()
    conn.close()

    # Status index for stepper (0: Placed, 1: Preparing, 2: Out for delivery, 3: Delivered)
    status_map = {
        "Placed": 1,
        "Preparing": 2,
        "Out for delivery": 3,
        "Delivered": 4,
        "Cancelled": -1
    }
    current_step = status_map.get(order["status"], 1)

    return render_template(
        "track.html",
        order=order,
        items=items,
        student=student,
        current_step=current_step
    )

# ==================== ADMIN DASHBOARD ====================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            flash("Welcome to Canteen Management Admin Portal!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin username or password.", "danger")

    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    status_filter = request.args.get("status", "All")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Metrics
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'Cancelled'")
    total_revenue = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Placed', 'Preparing', 'Out for delivery')")
    active_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Delivered'")
    delivered_orders = cursor.fetchone()[0]

    # Fetch Orders with student details
    query = """
        SELECT o.*, u.name as student_name, u.roll_no as student_roll
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE 1=1
    """
    params = []
    if status_filter != "All":
        query += " AND o.status = ?"
        params.append(status_filter)

    query += " ORDER BY o.created_at DESC"
    cursor.execute(query, params)
    raw_orders = cursor.fetchall()

    orders_list = []
    for order in raw_orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
        items = cursor.fetchall()
        orders_list.append({
            "order": order,
            "order_items": items
        })

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        total_revenue=total_revenue,
        active_orders=active_orders,
        delivered_orders=delivered_orders,
        orders=orders_list,
        status_filter=status_filter
    )

@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    new_status = request.form.get("status")
    allowed_statuses = ["Placed", "Preparing", "Out for delivery", "Delivered", "Cancelled"]

    if new_status in allowed_statuses:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE orders
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, order_id))
        conn.commit()
        conn.close()
        flash(f"Order #{order_id} status updated to {new_status}.", "success")
    else:
        flash("Invalid status update.", "danger")

    return redirect(request.referrer or url_for("admin_dashboard"))

@app.route("/admin/menu")
@admin_required
def admin_menu():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu_items ORDER BY category, id DESC")
    menu_items = cursor.fetchall()

    cursor.execute("SELECT DISTINCT category FROM menu_items ORDER BY category")
    categories = [row["category"] for row in cursor.fetchall()]
    conn.close()

    return render_template("admin/menu_manage.html", menu_items=menu_items, categories=categories)

@app.route("/admin/menu/add", methods=["POST"])
@admin_required
def add_menu_item():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = float(request.form.get("price", 0))
    description = request.form.get("description", "").strip()
    is_veg = 1 if request.form.get("is_veg") == "1" else 0
    prep_time = request.form.get("prep_time", "15 min").strip()
    image_url = request.form.get("image_url", "").strip()

    if not image_url:
        image_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO menu_items (name, category, price, description, is_veg, is_available, prep_time, image_url)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
    """, (name, category, price, description, is_veg, prep_time, image_url))
    conn.commit()
    conn.close()

    flash(f"Item '{name}' added to menu successfully!", "success")
    return redirect(url_for("admin_menu"))

@app.route("/admin/menu/<int:item_id>/edit", methods=["POST"])
@admin_required
def edit_menu_item(item_id):
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = float(request.form.get("price", 0))
    description = request.form.get("description", "").strip()
    is_veg = 1 if request.form.get("is_veg") == "1" else 0
    prep_time = request.form.get("prep_time", "15 min").strip()
    image_url = request.form.get("image_url", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE menu_items
        SET name = ?, category = ?, price = ?, description = ?, is_veg = ?, prep_time = ?, image_url = ?
        WHERE id = ?
    """, (name, category, price, description, is_veg, prep_time, image_url, item_id))
    conn.commit()
    conn.close()

    flash(f"Menu item '{name}' updated successfully!", "success")
    return redirect(url_for("admin_menu"))

@app.route("/admin/menu/<int:item_id>/toggle-stock", methods=["POST"])
@admin_required
def toggle_item_stock(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_available, name FROM menu_items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if item:
        new_status = 0 if item["is_available"] else 1
        cursor.execute("UPDATE menu_items SET is_available = ? WHERE id = ?", (new_status, item_id))
        conn.commit()
        status_text = "In Stock" if new_status == 1 else "Out of Stock"
        flash(f"'{item['name']}' marked as {status_text}.", "info")
    conn.close()
    return redirect(url_for("admin_menu"))

@app.route("/admin/menu/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_menu_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Menu item deleted successfully.", "warning")
    return redirect(url_for("admin_menu"))

if __name__ == "__main__":
    init_db()
    print("Hostel Bites server starting on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
