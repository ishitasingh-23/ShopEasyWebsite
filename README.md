# 🛒 ShopEasy — Online Shopping App (Python + tkinter)

A desktop online shopping application written entirely in Python.
The front end is built with **tkinter**, and data is stored in a local **SQLite** database.
No third-party packages are required.

## Features

**Customers**
- Register / log in (passwords are salted and hashed with PBKDF2)
- Browse products as cards, search by name, filter by category, sort by price
- Add to cart with quantity, change quantities, remove items (stock is checked)
- Checkout with delivery address and payment method
- View order history and the items in each order

**Admin** (`admin@shop.com` / `admin123`)
- Add, edit and delete products
- View all customer orders and update their status (Placed → Packed → Shipped → Delivered)

## Run it

Requires Python 3.8+ with tkinter (included with the python.org installers).

```bash
python3 main.py
```

In VS Code: open this folder, then press **F5** (uses the "Run ShopEasy" launch configuration).

The database file `shop.db` is created automatically on first run and seeded with sample products.
Delete it to reset the store.

## Run the tests

```bash
python3 -m unittest discover -v
```

## Project structure

```
Online_Shoping/
├── main.py              # entry point
├── shop/
│   ├── database.py      # SQLite data layer: users, products, cart, orders
│   └── gui.py           # tkinter screens: login, shop, cart, checkout, orders, admin
├── tests/
│   └── test_database.py # unit tests for the data layer
└── .vscode/             # run/debug and test settings for VS Code
```
