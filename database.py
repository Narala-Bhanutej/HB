import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_NAME = "hostel_bites.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table (Students)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            hostel_block TEXT NOT NULL,
            room_no TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Admin Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Menu Items Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            is_veg INTEGER DEFAULT 1,
            is_available INTEGER DEFAULT 1,
            prep_time TEXT DEFAULT '15-20 min',
            image_url TEXT,
            rating REAL DEFAULT 4.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Orders Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            hostel_block TEXT NOT NULL,
            room_no TEXT NOT NULL,
            phone TEXT NOT NULL,
            delivery_notes TEXT,
            payment_method TEXT NOT NULL,
            subtotal REAL NOT NULL,
            delivery_fee REAL DEFAULT 10.0,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Order Items Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER,
            item_name TEXT NOT NULL,
            item_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        )
    """)

    conn.commit()

    # Seed Admin if not exists
    cursor.execute("SELECT * FROM admins WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        admin_pass_hash = generate_password_hash("admin123")
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ("admin", admin_pass_hash))
        conn.commit()

    # Seed Demo Student if not exists
    cursor.execute("SELECT * FROM users WHERE roll_no = ?", ("22CS0101",))
    if not cursor.fetchone():
        student_pass_hash = generate_password_hash("student123")
        cursor.execute("""
            INSERT INTO users (name, roll_no, email, phone, hostel_block, room_no, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Rahul Sharma",
            "22CS0101",
            "rahul.cse@college.edu",
            "9876543210",
            "Hostel Block B (Boys)",
            "304",
            student_pass_hash
        ))
        conn.commit()

    # Seed Menu Items if empty
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_menu(cursor)
        conn.commit()

    conn.close()
    print("Database initialized successfully!")

def seed_menu(cursor):
    sample_items = [
        # Snacks & Quick Bites
        (
            "Cheese Maggi Supreme",
            "Snacks & Quick Bites",
            50.0,
            "Classic 2-minute canteen Maggi loaded with melted mozzarella, sweet corn & peri-peri spice.",
            1, 1, "10-12 min",
            "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=600&q=80",
            4.8
        ),
        (
            "Crispy Veg Samosa (2 Pcs)",
            "Snacks & Quick Bites",
            30.0,
            "Golden fried flaky crust stuffed with spicy mashed potato and peas, served with mint & tamarind chutney.",
            1, 1, "5-10 min",
            "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80",
            4.6
        ),
        (
            "Peri Peri French Fries",
            "Snacks & Quick Bites",
            70.0,
            "Hot, crispy salted potato fries dusted with fiery peri peri seasoning, served with garlic mayo dip.",
            1, 1, "12-15 min",
            "https://images.unsplash.com/photo-1576107232684-1279f3908594?auto=format&fit=crop&w=600&q=80",
            4.5
        ),
        (
            "Veg Paneer Burger",
            "Snacks & Quick Bites",
            85.0,
            "Crispy spiced paneer patty with fresh lettuce, onions, and spicy mayo inside a soft toasted bun.",
            1, 1, "15 min",
            "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80",
            4.7
        ),

        # Rolls & Sandwiches
        (
            "Paneer Tikka Roll",
            "Rolls & Sandwiches",
            90.0,
            "Smoky tandoori paneer cubes wrapped in a flaky paratha with sliced red onions and mint mayo.",
            1, 1, "15-20 min",
            "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=600&q=80",
            4.8
        ),
        (
            "Double Egg Chicken Roll",
            "Rolls & Sandwiches",
            110.0,
            "Double layered egg paratha stuffed with juicy spiced chicken chunks, green chillies & lemon juice.",
            0, 1, "15-20 min",
            "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=600&q=80",
            4.9
        ),
        (
            "Grilled Cheese & Corn Sandwich",
            "Rolls & Sandwiches",
            75.0,
            "Jumbo bread slices stuffed with sweet corn, capsicum and gooey cheese, grilled to perfection.",
            1, 1, "10-15 min",
            "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80",
            4.4
        ),

        # Meals & Biryani
        (
            "Canteen Special Chicken Biryani",
            "Meals & Biryani",
            140.0,
            "Fragrant basmati rice cooked with succulent chicken cuts and authentic spices, served with raita.",
            0, 1, "15-20 min",
            "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80",
            4.9
        ),
        (
            "Veg Dum Biryani with Salan",
            "Meals & Biryani",
            110.0,
            "Aromatic long-grain rice layered with seasoned garden veggies, paneer, and fried golden onions.",
            1, 1, "15-20 min",
            "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=600&q=80",
            4.5
        ),
        (
            "Special Thali (Roti, Dal, Sabzi, Rice)",
            "Meals & Biryani",
            100.0,
            "Homestyle wholesome meal with 3 warm Phulkas, Dal Tadka, Paneer Butter Masala, Jeera Rice & Papad.",
            1, 1, "15-20 min",
            "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=600&q=80",
            4.7
        ),
        (
            "Masala Dosa with Sambar & Chutney",
            "Meals & Biryani",
            65.0,
            "Crispy golden crepe made from fermented batter, filled with spiced potato masala and hot sambar.",
            1, 1, "10-15 min",
            "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80",
            4.6
        ),

        # Beverages & Shakes
        (
            "Thick Cold Coffee with Chocolate",
            "Beverages & Shakes",
            50.0,
            "Rich and creamy blended cold coffee drizzled with Hershey's chocolate syrup and coffee froth.",
            1, 1, "5-8 min",
            "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=600&q=80",
            4.9
        ),
        (
            "Canteen Masala Chai (Kulhad)",
            "Beverages & Shakes",
            20.0,
            "Strong brewed milk tea infused with crushed fresh ginger, cardamom and cloves. The ultimate study fuel.",
            1, 1, "5 min",
            "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80",
            4.8
        ),
        (
            "Oreo Blast Milkshake",
            "Beverages & Shakes",
            70.0,
            "Crushed crunchy Oreo cookies churned with whole milk and vanilla ice cream, topped with cookie bits.",
            1, 1, "5-10 min",
            "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=600&q=80",
            4.7
        ),

        # Late Night Specials
        (
            "Egg Bhurji with 2 Butter Pav",
            "Late Night Specials",
            60.0,
            "Spicy scrambled eggs with finely diced onions, tomatoes and green chillies served with butter toasted pav.",
            0, 1, "10-12 min",
            "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80",
            4.8
        ),
        (
            "Midnight Choco Lava Cake",
            "Late Night Specials",
            55.0,
            "Warm chocolate mini cake with a gooey, molten molten chocolate center. Perfect for late-night exams!",
            1, 1, "5-8 min",
            "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=600&q=80",
            4.9
        )
    ]

    cursor.executemany("""
        INSERT INTO menu_items (name, category, price, description, is_veg, is_available, prep_time, image_url, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_items)

if __name__ == "__main__":
    init_db()
