# 🍱 HostelBites — Campus Food Delivery System

A full-stack web application designed for college campuses that enables hostel students to order food directly from the campus canteen to their hostel rooms. Built with **Python Flask**, **SQLite**, and modern responsive **HTML5/CSS3/JavaScript**.

---

## 🌟 Key Features

### 🎓 1. Student Portal
- **Student Authentication:** Secure registration and login using student Roll Number/Email, Room Number, Hostel Block, and hashed passwords (`werkzeug.security`).
- **Interactive Food Catalog:**
  - Categorized browsing: *Snacks & Quick Bites*, *Meals & Biryani*, *Rolls & Sandwiches*, *Beverages & Shakes*, *Late Night Specials*.
  - Veg 🟢 / Non-Veg 🔴 indicators.
  - Live search bar and dietary filter toggles.
  - Preparation times and student ratings.
- **Dynamic Cart & Room Checkout:**
  - Add to tray, quantity stepper (`+` / `-`), auto-calculated subtotal, and free delivery thresholds.
  - Pre-filled hostel block and room number from student profile.
  - Room delivery instructions (e.g., *"Knock twice"*, *"Call when at hostel gate"*).
  - Flexible Payment Options: **Cash on Delivery (COD)** (preselected) and **UPI / QR Code Scan**.
- **Live Order Tracking:**
  - Visual status progress stepper: `Placed` ➔ `Preparing` ➔ `Out for Delivery` ➔ `Delivered`.
  - Order history with complete itemized breakdown.

### 👨‍🍳 2. Canteen Admin Dashboard
- **Kitchen Operations Center:**
  - Live view of incoming student orders sorted by newest first.
  - Filter orders by status (`Placed`, `Preparing`, `Out for delivery`, `Delivered`, `Cancelled`).
  - Instant status updater dropdown for canteen chefs and delivery boys.
- **Real-Time Key Performance Metrics (KPIs):**
  - Total Orders, Total Revenue (₹), Active Kitchen Orders, and Completed Room Deliveries.
- **Menu Management System:**
  - Add new canteen dishes with price, category, veg/non-veg flag, prep time, and image URL.
  - Edit existing dish prices and details.
  - One-click stock toggle (**In Stock** / **Sold Out**).
  - Delete discontinued items.

---

## 🛠️ Technology Stack

| Layer | Technology | Reason for Choice |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+ Fetch API) | Clean, responsive, lightweight, zero build-step overhead |
| **Backend** | Python 3, Flask 3.1.3 | Fast routing, lightweight WSGI server, native Python integration |
| **Database** | SQLite 3 | Serverless, zero-config relational database ideal for local & college demos |
| **Security** | Werkzeug Security | Secure password hashing (`scrypt` / `pbkdf2`) |
| **Styling** | Custom CSS3 Design System | Responsive grid, warm foodie theme, mobile-friendly navigation |

---

## 📁 Project Structure

```text
hostel bites/
├── app.py                     # Main Flask Application, API endpoints & controllers
├── database.py                # Database schema, table creation & sample menu seeder
├── requirements.txt           # Python dependencies
├── test_app.py                # Automated unit & integration test suite (7 tests)
├── README.md                  # Project documentation & viva guide
├── static/
│   ├── css/
│   │   └── style.css          # Modern UI stylesheet with variables & responsive styles
│   └── js/
│       ├── main.js            # Client-side cart API, quantities, toasts & UPI modal
│       └── admin.js           # Admin modal controllers & table search filter
└── templates/
    ├── base.html              # Layout shell (Navbar, badge counters, alerts, footer)
    ├── index.html             # Homepage: Hero, categories, search, dishes grid
    ├── login.html             # Student login page
    ├── register.html          # Student registration page (Roll No, Hostel, Room)
    ├── cart.html              # Tray & room checkout with COD / UPI options
    ├── order_success.html     # Celebratory order placed screen with direct tracker link
    ├── orders.html            # My Orders page with interactive mini-steppers
    ├── track.html             # Dedicated live order tracking page with milestones
    └── admin/
        ├── login.html         # Canteen staff admin login
        ├── dashboard.html     # Live incoming orders, status updater & revenue KPIs
        └── menu_manage.html   # Add, edit, delete & toggle stock for menu items
```

---

## 🚀 How to Run Locally

### 1. Prerequisites
- Python 3.10+ installed on your computer.

### 2. Setup & Installation
Open VS Code terminal inside the `hostel bites` folder:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database and seed sample menu & demo accounts
python database.py

# 3. Start the Flask server
python app.py
```

### 3. Open in Browser
Navigate to:
```text
http://127.0.0.1:5000
```

---

## 🔑 Demo Credentials for Testing / Viva Evaluation

| Role | Username / Identifier | Password | Access URL |
| :--- | :--- | :--- | :--- |
| **Demo Student** | `22CS0101` (or `rahul.cse@college.edu`) | `student123` | `http://127.0.0.1:5000/login` |
| **Canteen Admin** | `admin` | `admin123` | `http://127.0.0.1:5000/admin/login` |

*(You can also register any new student directly via the **Sign Up** button!)*

---

## 🧪 Running Automated Tests

Run the test suite to verify all endpoints, database operations, and user flows:
```bash
python test_app.py
```
Expected output:
```text
Ran 7 tests in ~1.0s
OK
```

---

## 💡 Recommended College Viva Questions & Answers

1. **Why choose SQLite over MySQL or PostgreSQL for this project?**
   - *Answer:* SQLite is serverless, self-contained, and file-based. It requires no separate database daemon installation, making it ideal for college project demonstrations and lightweight campus applications while still adhering strictly to ACID properties.
2. **How is password security handled?**
   - *Answer:* Passwords are never stored in plain text. They are hashed using Werkzeug's cryptographic hashing algorithms (`generate_password_hash` and `check_password_hash`), preventing credential exposure even in database dumps.
3. **How does the Cart system work?**
   - *Answer:* The cart is stored in the user's server-side secure Flask session (`session['cart']`). When a student clicks "+ Add to Tray", an asynchronous Fetch API request updates the session dictionary without triggering a full page reload, ensuring snappy performance.
4. **How does the Order Status Stepper transition?**
   - *Answer:* Each order record in the database maintains a `status` field (`Placed` ➔ `Preparing` ➔ `Out for delivery` ➔ `Delivered`). When the canteen admin updates the status on the Admin Dashboard, the student's live tracking view reflects the active stage dynamically.

---

## 🌐 Deploying Online (Render / PythonAnywhere)

To deploy on **Render**:
1. Push this repository to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com).
3. Set:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python database.py`
   - **Start Command:** `gunicorn app:app` (or `python app.py`)
