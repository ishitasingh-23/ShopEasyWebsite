"""tkinter front end for ShopEasy."""

import tkinter as tk
from tkinter import messagebox, ttk

from .database import Database

APP_NAME = "ShopEasy"
CURRENCY = "₹"

COLORS = {
    "bg": "#f4f6fb",
    "card": "#ffffff",
    "primary": "#4f46e5",
    "primary_dark": "#3730a3",
    "text": "#1f2937",
    "muted": "#6b7280",
    "success": "#059669",
    "danger": "#dc2626",
    "border": "#e5e7eb",
}

ORDER_STATUSES = ["Placed", "Packed", "Shipped", "Delivered", "Cancelled"]
PAYMENT_METHODS = ["Cash on Delivery", "UPI", "Card on Delivery"]


def money(value):
    return f"{CURRENCY}{value:,.2f}"


def setup_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=COLORS["bg"])
    style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], font=("Helvetica", 12))
    style.configure("Card.TFrame", background=COLORS["card"], relief="solid", borderwidth=1)
    style.configure("Card.TLabel", background=COLORS["card"])
    style.configure("CardTitle.TLabel", background=COLORS["card"], font=("Helvetica", 13, "bold"))
    style.configure("CardMuted.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=("Helvetica", 11))
    style.configure("Price.TLabel", background=COLORS["card"], foreground=COLORS["success"], font=("Helvetica", 14, "bold"))
    style.configure("Title.TLabel", font=("Helvetica", 22, "bold"))
    style.configure("Heading.TLabel", font=("Helvetica", 16, "bold"))
    style.configure("Muted.TLabel", foreground=COLORS["muted"])
    style.configure("Total.TLabel", font=("Helvetica", 16, "bold"), foreground=COLORS["success"])
    style.configure("Nav.TFrame", background=COLORS["primary"])
    style.configure("Nav.TLabel", background=COLORS["primary"], foreground="white", font=("Helvetica", 18, "bold"))
    style.configure("NavUser.TLabel", background=COLORS["primary"], foreground="#e0e7ff", font=("Helvetica", 11))
    style.configure("Nav.TButton", background=COLORS["primary"], foreground="white", borderwidth=0, padding=(12, 6))
    style.map("Nav.TButton", background=[("active", COLORS["primary_dark"])])
    style.configure("Accent.TButton", background=COLORS["primary"], foreground="white", borderwidth=0, padding=(12, 6))
    style.map("Accent.TButton", background=[("active", COLORS["primary_dark"]), ("disabled", COLORS["border"])])
    style.configure("Danger.TButton", background=COLORS["danger"], foreground="white", borderwidth=0, padding=(10, 5))
    style.map("Danger.TButton", background=[("active", "#b91c1c")])
    style.configure("Treeview", rowheight=28, font=("Helvetica", 12))
    style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
    style.configure("TRadiobutton", background=COLORS["bg"])


class ScrollableFrame(ttk.Frame):
    """A frame with a vertical scrollbar; put widgets inside `self.inner`."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event):
        # macOS sends small deltas, Windows sends multiples of 120.
        delta = event.delta if abs(event.delta) < 120 else event.delta // 120
        self.canvas.yview_scroll(-delta, "units")


# ---------------------------------------------------------------- auth screens
class LoginView(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.root, padding=40)
        self.app = app
        box = ttk.Frame(self)
        box.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(box, text=f"🛒 {APP_NAME}", style="Title.TLabel").pack(pady=(0, 4))
        ttk.Label(box, text="Sign in to start shopping", style="Muted.TLabel").pack(pady=(0, 20))

        ttk.Label(box, text="Email").pack(anchor="w")
        self.email = ttk.Entry(box, width=34)
        self.email.pack(pady=(0, 10), ipady=4)
        ttk.Label(box, text="Password").pack(anchor="w")
        self.password = ttk.Entry(box, width=34, show="•")
        self.password.pack(pady=(0, 16), ipady=4)

        ttk.Button(box, text="Login", style="Accent.TButton", command=self.submit).pack(fill="x")
        ttk.Button(box, text="New here? Create an account", command=app.show_register).pack(fill="x", pady=(8, 0))
        ttk.Label(box, text="Admin demo: admin@shop.com / admin123", style="Muted.TLabel").pack(pady=(18, 0))

        self.email.focus_set()
        self.password.bind("<Return>", lambda e: self.submit())

    def submit(self):
        try:
            user = self.app.db.login(self.email.get(), self.password.get())
        except ValueError as err:
            messagebox.showerror("Login failed", str(err))
            return
        self.app.login(user)


class RegisterView(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.root, padding=40)
        self.app = app
        box = ttk.Frame(self)
        box.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(box, text="Create your account", style="Title.TLabel").pack(pady=(0, 20))
        self.fields = {}
        for label, key, show in [("Full name", "name", ""), ("Email", "email", ""),
                                 ("Password", "password", "•"), ("Confirm password", "confirm", "•")]:
            ttk.Label(box, text=label).pack(anchor="w")
            entry = ttk.Entry(box, width=34, show=show)
            entry.pack(pady=(0, 10), ipady=4)
            self.fields[key] = entry

        ttk.Button(box, text="Register", style="Accent.TButton", command=self.submit).pack(fill="x", pady=(6, 0))
        ttk.Button(box, text="Back to login", command=app.show_login).pack(fill="x", pady=(8, 0))
        self.fields["name"].focus_set()

    def submit(self):
        values = {k: e.get() for k, e in self.fields.items()}
        if values["password"] != values["confirm"]:
            messagebox.showerror("Register", "Passwords do not match.")
            return
        try:
            user = self.app.db.register(values["name"], values["email"], values["password"])
        except ValueError as err:
            messagebox.showerror("Register", str(err))
            return
        messagebox.showinfo("Welcome", f"Account created. Welcome, {user['name']}!")
        self.app.login(user)


# ---------------------------------------------------------------- main shell
class MainView(ttk.Frame):
    """Top navigation bar plus a content area that swaps pages."""

    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        user = app.user

        nav = ttk.Frame(self, style="Nav.TFrame", padding=(16, 10))
        nav.pack(fill="x")
        ttk.Label(nav, text=f"🛒 {APP_NAME}", style="Nav.TLabel").pack(side="left")
        ttk.Button(nav, text="Logout", style="Nav.TButton", command=app.logout).pack(side="right")
        ttk.Label(nav, text=f"Hi, {user['name']}", style="NavUser.TLabel").pack(side="right", padx=12)
        if user["is_admin"]:
            ttk.Button(nav, text="Admin", style="Nav.TButton", command=lambda: self.show(AdminPage)).pack(side="right")
        ttk.Button(nav, text="My Orders", style="Nav.TButton", command=lambda: self.show(OrdersPage)).pack(side="right")
        self.cart_button = ttk.Button(nav, style="Nav.TButton", command=lambda: self.show(CartPage))
        self.cart_button.pack(side="right")
        ttk.Button(nav, text="Shop", style="Nav.TButton", command=lambda: self.show(ShopPage)).pack(side="right")

        self.content = ttk.Frame(self, padding=16)
        self.content.pack(fill="both", expand=True)
        self.page = None
        self.refresh_cart_badge()
        self.show(ShopPage)

    def show(self, page_class, **kwargs):
        if self.page is not None:
            self.page.destroy()
        self.page = page_class(self.content, self.app, **kwargs)
        self.page.pack(fill="both", expand=True)

    def refresh_cart_badge(self):
        count = self.app.db.cart_count(self.app.user["id"])
        self.cart_button.configure(text=f"Cart ({count})")


# ---------------------------------------------------------------- pages
class ShopPage(ttk.Frame):
    COLUMNS = 3

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 12))
        ttk.Label(bar, text="Search").pack(side="left")
        self.search = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.search, width=28)
        entry.pack(side="left", padx=(6, 16), ipady=3)
        entry.bind("<KeyRelease>", lambda e: self.load())

        ttk.Label(bar, text="Category").pack(side="left")
        self.category = tk.StringVar(value="All")
        cat = ttk.Combobox(bar, textvariable=self.category, state="readonly", width=16,
                           values=["All"] + app.db.categories())
        cat.pack(side="left", padx=(6, 16))
        cat.bind("<<ComboboxSelected>>", lambda e: self.load())

        ttk.Label(bar, text="Sort").pack(side="left")
        self.sort = tk.StringVar(value="Name")
        sort = ttk.Combobox(bar, textvariable=self.sort, state="readonly", width=18,
                            values=["Name", "Price: Low to High", "Price: High to Low"])
        sort.pack(side="left", padx=6)
        sort.bind("<<ComboboxSelected>>", lambda e: self.load())

        self.result_label = ttk.Label(bar, style="Muted.TLabel")
        self.result_label.pack(side="right")

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True)
        for col in range(self.COLUMNS):
            self.scroll.inner.columnconfigure(col, weight=1, uniform="col")
        self.load()

    def load(self):
        for child in self.scroll.inner.winfo_children():
            child.destroy()
        products = self.app.db.products(self.search.get(), self.category.get(), self.sort.get())
        self.result_label.configure(text=f"{len(products)} product(s)")
        if not products:
            ttk.Label(self.scroll.inner, text="No products match your search.",
                      style="Muted.TLabel").grid(row=0, column=0, columnspan=self.COLUMNS, pady=40)
        for i, product in enumerate(products):
            card = self._card(product)
            card.grid(row=i // self.COLUMNS, column=i % self.COLUMNS, sticky="nsew", padx=8, pady=8)

    def _card(self, product):
        card = ttk.Frame(self.scroll.inner, style="Card.TFrame", padding=14)
        ttk.Label(card, text=product["name"], style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=product["category"], style="CardMuted.TLabel").pack(anchor="w")
        ttk.Label(card, text=product["description"] or "", style="Card.TLabel",
                  wraplength=240, justify="left").pack(anchor="w", pady=(6, 8))
        ttk.Label(card, text=money(product["price"]), style="Price.TLabel").pack(anchor="w")

        in_stock = product["stock"] > 0
        ttk.Label(card, text=f"{product['stock']} in stock" if in_stock else "Out of stock",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(0, 8))

        row = ttk.Frame(card, style="Card.TFrame", borderwidth=0)
        row.pack(fill="x")
        qty = tk.IntVar(value=1)
        ttk.Spinbox(row, from_=1, to=max(product["stock"], 1), textvariable=qty, width=4,
                    state="readonly" if in_stock else "disabled").pack(side="left")
        ttk.Button(row, text="Add to Cart", style="Accent.TButton",
                   state="normal" if in_stock else "disabled",
                   command=lambda: self.add(product, qty.get())).pack(side="right")
        return card

    def add(self, product, quantity):
        try:
            self.app.db.add_to_cart(self.app.user["id"], product["id"], quantity)
        except ValueError as err:
            messagebox.showwarning("Cart", str(err))
            return
        self.app.main.refresh_cart_badge()
        messagebox.showinfo("Cart", f"Added {quantity} × {product['name']} to your cart.")


class CartPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Your Cart", style="Heading.TLabel").pack(anchor="w", pady=(0, 10))

        columns = ("name", "price", "qty", "subtotal")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        for col, text, width, anchor in [("name", "Product", 320, "w"), ("price", "Price", 120, "e"),
                                         ("qty", "Quantity", 100, "center"), ("subtotal", "Subtotal", 140, "e")]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.pack(fill="both", expand=True)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=10)
        ttk.Button(actions, text="＋", width=3, command=lambda: self.change(1)).pack(side="left")
        ttk.Button(actions, text="－", width=3, command=lambda: self.change(-1)).pack(side="left", padx=4)
        ttk.Button(actions, text="Remove", style="Danger.TButton", command=self.remove).pack(side="left", padx=4)
        ttk.Button(actions, text="Clear cart", command=self.clear).pack(side="left", padx=4)

        self.checkout_btn = ttk.Button(actions, text="Proceed to Checkout →", style="Accent.TButton",
                                       command=lambda: app.main.show(CheckoutPage))
        self.checkout_btn.pack(side="right")
        self.total_label = ttk.Label(actions, style="Total.TLabel")
        self.total_label.pack(side="right", padx=16)
        self.load()

    def load(self):
        self.tree.delete(*self.tree.get_children())
        items = self.app.db.cart(self.app.user["id"])
        for item in items:
            self.tree.insert("", "end", iid=str(item["id"]), values=(
                item["name"], money(item["price"]), item["quantity"], money(item["subtotal"])))
        total = sum(i["subtotal"] for i in items)
        self.total_label.configure(text=f"Total: {money(total)}")
        self.checkout_btn.configure(state="normal" if items else "disabled")
        self.app.main.refresh_cart_badge()

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Cart", "Please select an item first.")
            return None
        return int(sel[0])

    def change(self, delta):
        product_id = self._selected()
        if product_id is None:
            return
        current = int(self.tree.set(str(product_id), "qty"))
        try:
            self.app.db.set_cart_quantity(self.app.user["id"], product_id, current + delta)
        except ValueError as err:
            messagebox.showwarning("Cart", str(err))
        self.load()
        if self.tree.exists(str(product_id)):
            self.tree.selection_set(str(product_id))

    def remove(self):
        product_id = self._selected()
        if product_id is not None:
            self.app.db.set_cart_quantity(self.app.user["id"], product_id, 0)
            self.load()

    def clear(self):
        if self.tree.get_children() and messagebox.askyesno("Cart", "Remove all items from your cart?"):
            self.app.db.clear_cart(self.app.user["id"])
            self.load()


class CheckoutPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Checkout", style="Heading.TLabel").pack(anchor="w", pady=(0, 10))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        ttk.Label(left, text="Delivery address").pack(anchor="w")
        self.address = tk.Text(left, height=5, width=40, font=("Helvetica", 12), relief="solid", borderwidth=1)
        self.address.pack(fill="x", pady=(4, 16))

        ttk.Label(left, text="Payment method").pack(anchor="w")
        self.payment = tk.StringVar(value=PAYMENT_METHODS[0])
        for method in PAYMENT_METHODS:
            ttk.Radiobutton(left, text=method, value=method, variable=self.payment).pack(anchor="w", pady=2)

        right = ttk.Frame(body, style="Card.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="new")
        ttk.Label(right, text="Order summary", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        items = app.db.cart(app.user["id"])
        for item in items:
            line = ttk.Frame(right, style="Card.TFrame", borderwidth=0)
            line.pack(fill="x")
            ttk.Label(line, text=f"{item['name']} × {item['quantity']}", style="Card.TLabel").pack(side="left")
            ttk.Label(line, text=money(item["subtotal"]), style="Card.TLabel").pack(side="right")
        ttk.Separator(right).pack(fill="x", pady=8)
        total = ttk.Frame(right, style="Card.TFrame", borderwidth=0)
        total.pack(fill="x")
        ttk.Label(total, text="Total", style="CardTitle.TLabel").pack(side="left")
        ttk.Label(total, text=money(sum(i["subtotal"] for i in items)), style="Price.TLabel").pack(side="right")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=12)
        ttk.Button(buttons, text="← Back to cart", command=lambda: app.main.show(CartPage)).pack(side="left")
        ttk.Button(buttons, text="Place Order", style="Accent.TButton", command=self.place).pack(side="right")

    def place(self):
        try:
            order_id = self.app.db.place_order(
                self.app.user["id"], self.address.get("1.0", "end"), self.payment.get())
        except ValueError as err:
            messagebox.showerror("Checkout", str(err))
            return
        self.app.main.refresh_cart_badge()
        messagebox.showinfo("Order placed", f"Thank you! Your order #{order_id} has been placed.")
        self.app.main.show(OrdersPage)


class OrderList(ttk.Frame):
    """Orders table with an item breakdown for the selected order (shared by customer and admin)."""

    def __init__(self, parent, app, orders, show_customer=False):
        super().__init__(parent)
        self.app = app
        columns = ("id", "customer", "date", "total", "payment", "status") if show_customer \
            else ("id", "date", "total", "payment", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=8, selectmode="browse")
        widths = {"id": 70, "customer": 150, "date": 150, "total": 120, "payment": 160, "status": 110}
        for col in columns:
            self.tree.heading(col, text="Order #" if col == "id" else col.title())
            self.tree.column(col, width=widths[col], anchor="w" if col in ("customer", "payment") else "center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_items())

        ttk.Label(self, text="Items in selected order", style="Muted.TLabel").pack(anchor="w", pady=(10, 4))
        self.items = ttk.Treeview(self, columns=("name", "price", "qty", "subtotal"), show="headings", height=5)
        for col, text in [("name", "Product"), ("price", "Price"), ("qty", "Qty"), ("subtotal", "Subtotal")]:
            self.items.heading(col, text=text)
        self.items.column("name", width=300)
        self.items.pack(fill="both", expand=True)
        self.address = ttk.Label(self, style="Muted.TLabel", wraplength=700, justify="left")
        self.address.pack(anchor="w", pady=(6, 0))
        self.set_orders(orders)

    def set_orders(self, orders):
        self.orders = {str(o["id"]): o for o in orders}
        self.tree.delete(*self.tree.get_children())
        for o in orders:
            values = [o["id"], o["created_at"], money(o["total"]), o["payment_method"], o["status"]]
            if "customer" in self.tree["columns"]:
                values.insert(1, o["customer"])
            self.tree.insert("", "end", iid=str(o["id"]), values=values)
        self.show_items()

    def selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def show_items(self):
        self.items.delete(*self.items.get_children())
        order_id = self.selected_id()
        if order_id is None:
            self.address.configure(text="")
            return
        for item in self.app.db.order_items(order_id):
            self.items.insert("", "end", values=(
                item["name"], money(item["price"]), item["quantity"], money(item["price"] * item["quantity"])))
        self.address.configure(text=f"Deliver to: {self.orders[str(order_id)]['address']}")


class OrdersPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        ttk.Label(self, text="My Orders", style="Heading.TLabel").pack(anchor="w", pady=(0, 10))
        orders = app.db.orders(app.user["id"])
        if not orders:
            ttk.Label(self, text="You haven't placed any orders yet.", style="Muted.TLabel").pack(pady=30)
            ttk.Button(self, text="Start shopping", style="Accent.TButton",
                       command=lambda: app.main.show(ShopPage)).pack()
            return
        OrderList(self, app, orders).pack(fill="both", expand=True)


class AdminPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Admin Panel", style="Heading.TLabel").pack(anchor="w", pady=(0, 10))
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        tabs.add(self._products_tab(tabs), text="  Products  ")
        tabs.add(self._orders_tab(tabs), text="  Orders  ")

    # ----- products
    def _products_tab(self, parent):
        frame = ttk.Frame(parent, padding=10)
        columns = ("id", "name", "category", "price", "stock")
        self.ptree = ttk.Treeview(frame, columns=columns, show="headings", height=10, selectmode="browse")
        for col, width in zip(columns, (50, 260, 150, 100, 80)):
            self.ptree.heading(col, text=col.title())
            self.ptree.column(col, width=width, anchor="w" if col in ("name", "category") else "center")
        self.ptree.pack(fill="both", expand=True)
        self.ptree.bind("<<TreeviewSelect>>", lambda e: self._fill_form())

        form = ttk.Frame(frame)
        form.pack(fill="x", pady=10)
        self.pvars = {}
        for i, (label, key) in enumerate([("Name", "name"), ("Category", "category"), ("Price", "price"),
                                          ("Stock", "stock"), ("Description", "description")]):
            ttk.Label(form, text=label).grid(row=i // 3, column=(i % 3) * 2, sticky="e", padx=(8, 4), pady=4)
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=60 if key == "description" else 22).grid(
                row=i // 3, column=(i % 3) * 2 + 1, columnspan=3 if key == "description" else 1, sticky="w", pady=4)
            self.pvars[key] = var

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Add new", style="Accent.TButton", command=self._add_product).pack(side="left")
        ttk.Button(buttons, text="Update selected", command=self._update_product).pack(side="left", padx=6)
        ttk.Button(buttons, text="Delete selected", style="Danger.TButton",
                   command=self._delete_product).pack(side="left")
        ttk.Button(buttons, text="Clear form", command=lambda: [v.set("") for v in self.pvars.values()]).pack(side="right")
        self._load_products()
        return frame

    def _load_products(self):
        self.ptree.delete(*self.ptree.get_children())
        for p in self.app.db.products():
            self.ptree.insert("", "end", iid=str(p["id"]),
                              values=(p["id"], p["name"], p["category"], money(p["price"]), p["stock"]))

    def _selected_product(self):
        sel = self.ptree.selection()
        if not sel:
            messagebox.showinfo("Products", "Please select a product first.")
            return None
        return int(sel[0])

    def _fill_form(self):
        sel = self.ptree.selection()
        if sel:
            product = self.app.db.get_product(int(sel[0]))
            for key, var in self.pvars.items():
                var.set(product[key] if product[key] is not None else "")

    def _form_values(self):
        return {k: v.get() for k, v in self.pvars.items()}

    def _add_product(self):
        try:
            self.app.db.add_product(**self._form_values())
        except ValueError as err:
            messagebox.showerror("Products", str(err))
            return
        self._load_products()
        messagebox.showinfo("Products", "Product added.")

    def _update_product(self):
        product_id = self._selected_product()
        if product_id is None:
            return
        try:
            self.app.db.update_product(product_id, **self._form_values())
        except ValueError as err:
            messagebox.showerror("Products", str(err))
            return
        self._load_products()
        self.ptree.selection_set(str(product_id))

    def _delete_product(self):
        product_id = self._selected_product()
        if product_id is not None and messagebox.askyesno("Products", "Delete this product?"):
            self.app.db.delete_product(product_id)
            self._load_products()
            self.app.main.refresh_cart_badge()

    # ----- orders
    def _orders_tab(self, parent):
        frame = ttk.Frame(parent, padding=10)
        bar = ttk.Frame(frame)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Set status of selected order:").pack(side="left")
        self.status = tk.StringVar(value=ORDER_STATUSES[0])
        ttk.Combobox(bar, textvariable=self.status, values=ORDER_STATUSES, state="readonly",
                     width=14).pack(side="left", padx=6)
        ttk.Button(bar, text="Update", style="Accent.TButton", command=self._update_status).pack(side="left")
        self.order_list = OrderList(frame, self.app, self.app.db.orders(), show_customer=True)
        self.order_list.pack(fill="both", expand=True)
        return frame

    def _update_status(self):
        order_id = self.order_list.selected_id()
        if order_id is None:
            messagebox.showinfo("Orders", "Please select an order first.")
            return
        self.app.db.update_order_status(order_id, self.status.get())
        self.order_list.set_orders(self.app.db.orders())
        self.order_list.tree.selection_set(str(order_id))


# ---------------------------------------------------------------- application
class ShopApp:
    def __init__(self, db=None):
        self.db = db or Database()
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        setup_styles(self.root)
        self.user = None
        self.main = None
        self.view = None
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.show_login()

    def _switch(self, view):
        if self.view is not None:
            self.view.destroy()
        self.view = view
        self.view.pack(fill="both", expand=True)

    def show_login(self):
        self._switch(LoginView(self))

    def show_register(self):
        self._switch(RegisterView(self))

    def login(self, user):
        self.user = user
        self.main = MainView(self)
        self._switch(self.main)

    def logout(self):
        self.user = None
        self.main = None
        self.show_login()

    def quit(self):
        self.db.close()
        self.root.destroy()

    def bring_to_front(self):
        # On macOS a window launched from a terminal opens behind the active app.
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(300, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

    def run(self):
        self.root.after(100, self.bring_to_front)
        self.root.mainloop()
