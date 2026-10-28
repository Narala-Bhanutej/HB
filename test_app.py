import unittest
from app import app
from database import init_db, get_db_connection

class HostelBitesTestCase(unittest.TestCase):
    def setUp(self):
        init_db()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_01_homepage_and_menu(self):
        """Verify homepage loads and displays canteen items"""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Hostel", res.data)
        self.assertIn(b"Bites", res.data)
        self.assertIn(b"Cheese Maggi", res.data)
        self.assertIn(b"Canteen Special Chicken Biryani", res.data)

    def test_02_student_auth(self):
        """Verify student login and session"""
        res = self.client.post("/login", data={
            "identifier": "22CS0101",
            "password": "student123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome back", res.data)

    def test_03_cart_api(self):
        """Verify adding and updating cart items"""
        with self.client:
            # Add Maggi (item ID 1)
            res = self.client.post("/api/cart/add", json={
                "item_id": 1,
                "quantity": 2
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["cart_count"], 2)

            # Update quantity (+1)
            res2 = self.client.post("/api/cart/update", json={
                "item_id": 1,
                "change": 1
            })
            self.assertEqual(res2.status_code, 200)
            data2 = res2.get_json()
            self.assertEqual(data2["cart_count"], 3)

    def test_04_full_order_flow(self):
        """Verify student login, adding to cart, placing room delivery order, and tracking"""
        with self.client:
            # Login
            self.client.post("/login", data={
                "identifier": "22CS0101",
                "password": "student123"
            })

            # Add Biryani (item ID 8)
            self.client.post("/api/cart/add", json={"item_id": 8, "quantity": 1})

            # Checkout
            res = self.client.post("/checkout", data={
                "hostel_block": "Hostel Block B (Boys)",
                "room_no": "304",
                "phone": "9876543210",
                "delivery_notes": "Call before knocking",
                "payment_method": "Cash on Delivery"
            }, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Order Successfully Placed", res.data)
            self.assertIn(b"HB-", res.data)

            # Check My Orders
            res_orders = self.client.get("/my-orders")
            self.assertEqual(res_orders.status_code, 200)
            self.assertIn(b"Hostel Block B (Boys)", res_orders.data)
            self.assertIn(b"304", res_orders.data)

    def test_05_admin_operations(self):
        """Verify admin login, dashboard, status updates and menu items"""
        with self.client:
            # Login admin
            res = self.client.post("/admin/login", data={
                "username": "admin",
                "password": "admin123"
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Canteen Kitchen & Order Operations", res.data)

            # View Dashboard
            res_dash = self.client.get("/admin/dashboard")
            self.assertEqual(res_dash.status_code, 200)
            self.assertIn(b"Total Orders", res_dash.data)

            # Update latest order status if exists
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                order_id = row["id"]
                res_status = self.client.post(f"/admin/order/{order_id}/status", data={
                    "status": "Preparing"
                }, follow_redirects=True)
                self.assertEqual(res_status.status_code, 200)

                # Check database updated
                cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
                updated_status = cursor.fetchone()["status"]
                self.assertEqual(updated_status, "Preparing")
            conn.close()

    def test_06_admin_menu_management(self):
        """Verify admin can add, edit, toggle stock, and delete menu items"""
        with self.client:
            self.client.post("/admin/login", data={"username": "admin", "password": "admin123"})

            # Add new item
            res_add = self.client.post("/admin/menu/add", data={
                "name": "Paneer Butter Fried Rice",
                "category": "Meals & Biryani",
                "price": "95",
                "description": "Wok-tossed rice with paneer cubes and mild spices.",
                "is_veg": "1",
                "prep_time": "15 min",
                "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"
            }, follow_redirects=True)
            self.assertEqual(res_add.status_code, 200)
            self.assertIn(b"Paneer Butter Fried Rice", res_add.data)

            # Get added item id
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, is_available FROM menu_items WHERE name = ?", ("Paneer Butter Fried Rice",))
            item = cursor.fetchone()
            self.assertIsNotNone(item)
            item_id = item["id"]

            # Toggle stock
            res_toggle = self.client.post(f"/admin/menu/{item_id}/toggle-stock", follow_redirects=True)
            self.assertEqual(res_toggle.status_code, 200)
            cursor.execute("SELECT is_available FROM menu_items WHERE id = ?", (item_id,))
            self.assertEqual(cursor.fetchone()["is_available"], 0)

            # Edit item
            res_edit = self.client.post(f"/admin/menu/{item_id}/edit", data={
                "name": "Paneer Butter Fried Rice Special",
                "category": "Meals & Biryani",
                "price": "105",
                "description": "Updated wok-tossed delicious rice.",
                "is_veg": "1",
                "prep_time": "18 min",
                "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"
            }, follow_redirects=True)
            self.assertEqual(res_edit.status_code, 200)
            cursor.execute("SELECT name, price FROM menu_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            self.assertEqual(row["name"], "Paneer Butter Fried Rice Special")
            self.assertEqual(row["price"], 105.0)

            # Delete item
            res_del = self.client.post(f"/admin/menu/{item_id}/delete", follow_redirects=True)
            self.assertEqual(res_del.status_code, 200)
            cursor.execute("SELECT id FROM menu_items WHERE id = ?", (item_id,))
            self.assertIsNone(cursor.fetchone())
            conn.close()

    def test_07_filters_and_search(self):
        """Verify search and category filtering work properly"""
        # Search for maggi
        res_search = self.client.get("/?search=maggi")
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b"Cheese Maggi Supreme", res_search.data)

        # Veg filter
        res_veg = self.client.get("/?diet=veg")
        self.assertEqual(res_veg.status_code, 200)
        self.assertIn(b"Veg Dum Biryani", res_veg.data)
        self.assertNotIn(b"Special Chicken Biryani", res_veg.data)

if __name__ == "__main__":
    unittest.main()
