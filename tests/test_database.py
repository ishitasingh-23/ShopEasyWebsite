import unittest

from shop.database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.user = self.db.register("Test User", "test@example.com", "secret1")

    def tearDown(self):
        self.db.close()

    def test_seeds_products_and_admin(self):
        self.assertGreater(len(self.db.products()), 0)
        admin = self.db.login("admin@shop.com", "admin123")
        self.assertEqual(admin["is_admin"], 1)

    def test_register_and_login(self):
        self.assertEqual(self.db.login("TEST@example.com", "secret1")["id"], self.user["id"])
        with self.assertRaises(ValueError):
            self.db.login("test@example.com", "wrong")
        with self.assertRaises(ValueError):
            self.db.register("Again", "test@example.com", "secret1")
        with self.assertRaises(ValueError):
            self.db.register("Short", "short@example.com", "123")

    def test_search_and_filter(self):
        books = self.db.products(category="Books")
        self.assertTrue(books and all(p["category"] == "Books" for p in books))
        self.assertEqual(self.db.products(search="Yoga")[0]["name"], "Yoga Mat")
        prices = [p["price"] for p in self.db.products(sort="Price: Low to High")]
        self.assertEqual(prices, sorted(prices))

    def test_cart_respects_stock(self):
        product = self.db.products(search="Cricket Bat")[0]
        self.db.add_to_cart(self.user["id"], product["id"], 2)
        self.db.add_to_cart(self.user["id"], product["id"], 1)
        self.assertEqual(self.db.cart_count(self.user["id"]), 3)
        with self.assertRaises(ValueError):
            self.db.add_to_cart(self.user["id"], product["id"], product["stock"])
        self.db.set_cart_quantity(self.user["id"], product["id"], 0)
        self.assertEqual(self.db.cart(self.user["id"]), [])

    def test_place_order_reduces_stock_and_clears_cart(self):
        product = self.db.products(search="Yoga")[0]
        self.db.add_to_cart(self.user["id"], product["id"], 2)
        order_id = self.db.place_order(self.user["id"], "12 MG Road, Pune", "UPI")
        self.assertEqual(self.db.get_product(product["id"])["stock"], product["stock"] - 2)
        self.assertEqual(self.db.cart(self.user["id"]), [])
        order = self.db.orders(self.user["id"])[0]
        self.assertEqual(order["id"], order_id)
        self.assertAlmostEqual(order["total"], product["price"] * 2)
        self.assertEqual(len(self.db.order_items(order_id)), 1)

    def test_empty_cart_or_address_rejected(self):
        with self.assertRaises(ValueError):
            self.db.place_order(self.user["id"], "Somewhere", "UPI")
        product = self.db.products()[0]
        self.db.add_to_cart(self.user["id"], product["id"])
        with self.assertRaises(ValueError):
            self.db.place_order(self.user["id"], "   ", "UPI")

    def test_admin_product_crud(self):
        pid = self.db.add_product("Test Pen", "Stationery", "20", "100", "Blue ink")
        self.assertIn("Stationery", self.db.categories())
        self.db.update_product(pid, "Test Pen", "Stationery", "25", "90", "Blue ink")
        self.assertEqual(self.db.get_product(pid)["price"], 25)
        with self.assertRaises(ValueError):
            self.db.add_product("Bad", "X", "-5", "1")
        self.db.delete_product(pid)
        self.assertIsNone(self.db.get_product(pid))


if __name__ == "__main__":
    unittest.main()
