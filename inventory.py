import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import csv
import json
import os
import ttkbootstrap as tb
try:
    from PIL import Image, ImageTk  # optional
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ---------------- Database ----------------
conn = sqlite3.connect("optiedge_inventory.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")
# Add default admin user
cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
conn.commit()

# ---------------- Functions ----------------

def add_product():
    name = name_entry.get()
    price = price_entry.get()
    quantity = quantity_entry.get()
    if not name or not price or not quantity:
        if error_label:
            error_label.config(text="All fields are required")
        messagebox.showwarning("Input Error", "All fields are required")
        return
    try:
        cursor.execute("INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)",
                       (name, float(price), int(quantity)))
        conn.commit()
        load_products()
        clear_inputs()
        show_toast("Product added")
        if error_label:
            error_label.config(text="")
    except ValueError:
        if error_label:
            error_label.config(text="Price must be numeric and Quantity must be integer")
        messagebox.showerror("Input Error", "Price must be numeric and Quantity must be integer")

def update_product():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Error", "Select a product to update")
        return
    item = tree.item(selected)
    product_id = item["values"][0]

    name = name_entry.get()
    price = price_entry.get()
    quantity = quantity_entry.get()

    if not name or not price or not quantity:
        if error_label:
            error_label.config(text="All fields are required")
        messagebox.showwarning("Input Error", "All fields are required")
        return
    try:
        # Confirm update
        if not messagebox.askyesno("Confirm Update", f"Update product ID {product_id} to name='{name}', price={price}, qty={quantity}?"):
            return
        cursor.execute("UPDATE products SET name=?, price=?, quantity=? WHERE id=?",
                       (name, float(price), int(quantity), product_id))
        conn.commit()
        load_products()
        clear_inputs()
        show_toast("Product updated")
        if error_label:
            error_label.config(text="")
    except ValueError:
        if error_label:
            error_label.config(text="Price must be numeric and Quantity must be integer")
        messagebox.showerror("Input Error", "Price must be numeric and Quantity must be integer")

def delete_product():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Error", "Select a product to delete")
        return
    item = tree.item(selected)
    product_id = item["values"][0]
    name = item["values"][1]
    if not messagebox.askyesno("Confirm Delete", f"Delete product '{name}' (ID {product_id})?"):
        return
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    load_products()
    show_toast("Product deleted")

def load_products():
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM products")
    for idx, product in enumerate(cursor.fetchall()):
        tag = "evenrow" if idx % 2 == 0 else "oddrow"
        tree.insert("", "end", values=product, tags=(tag,))
    update_total_value()
    color_tree_rows()

def clear_inputs():
    name_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)

def search_product():
    query = (search_entry.get() or "").strip()
    if query == "":
        load_products()
        prefs['last_search'] = ""
        save_prefs(prefs)
        return
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute(
        "SELECT * FROM products WHERE name LIKE ? OR CAST(id AS TEXT) LIKE ?",
        ('%' + query + '%', '%' + query + '%')
    )
    for idx, product in enumerate(cursor.fetchall()):
        tag = "evenrow" if idx % 2 == 0 else "oddrow"
        tree.insert("", "end", values=product, tags=(tag,))
    update_total_value()
    color_tree_rows()
    # Persist last search
    prefs['last_search'] = query
    save_prefs(prefs)

def color_tree_rows():
    try:
        for i, item in enumerate(tree.get_children()):
            tree.item(item, tags=("evenrow",) if i % 2 == 0 else ("oddrow",))
        tree.tag_configure("evenrow", background="#FFFFFF")
        tree.tag_configure("oddrow", background="#F5F7FA")
    except Exception:
        pass

def update_total_value():
    cursor.execute("SELECT SUM(price*quantity) FROM products")
    total = cursor.fetchone()[0]
    if total is None:
        total = 0
    total_label.config(text=f"Total Inventory Value: ₦{total:,.2f}")

def export_csv():
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    if not data:
        messagebox.showinfo("Export", "No products to export")
        return
    file_path = filedialog.asksaveasfilename(
        title="Export Inventory",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        initialfile="inventory_export.csv",
    )
    if not file_path:
        return
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Price", "Quantity"])
        writer.writerows(data)
    show_toast(f"Exported to {os.path.basename(file_path)}")

def export_selected_csv():
    try:
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Export", "Select a row to export")
            return
        vals = tree.item(sel[0], "values")
        file_path = filedialog.asksaveasfilename(
            title="Export Selected Product",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"product_{vals[0]}.csv",
        )
        if not file_path:
            return
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Price", "Quantity"])
            writer.writerow(vals)
        show_toast(f"Exported product to {os.path.basename(file_path)}")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))

def show_about():
    messagebox.showinfo(
        "About",
        "Optiedge Inventory System\n\nA simple, modern inventory manager built with Python and Tkinter.\n© Optiedge",
    )

def show_shortcuts():
    messagebox.showinfo(
        "Keyboard Shortcuts",
        "Shortcuts:\n\n"
        "Ctrl+F: Focus Search\n"
        "Enter: Search\n"
        "Delete: Delete selected row\n"
        "Ctrl+S: Export CSV\n"
        "Ctrl+N: Add Product",
    )

# ---- UI helpers (top-level, no nested button functions) ----
def _wrap_command(fn):
    def _inner():
        try:
            fn()
        except Exception as e:
            try:
                messagebox.showerror("Error", str(e))
            except Exception:
                pass
    return _inner

def create_button(parent, text, command, bootstyle):
    try:
        return tb.Button(parent, text=text, bootstyle=bootstyle, width=14, command=_wrap_command(command))
    except Exception:
        # Fallback to standard ttk if ttkbootstrap unavailable at runtime
        return ttk.Button(parent, text=text, command=_wrap_command(command))

def set_density(mode: str = "Comfortable"):
    try:
        rowheight = 30 if mode == "Comfortable" else 24
        ttk.Style().configure("Treeview", rowheight=rowheight)
        prefs['density'] = mode
        save_prefs(prefs)
    except Exception:
        pass

def login():
    username = username_entry.get()
    password = password_entry.get()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    if user:
        login_frame.pack_forget()
        build_inventory_ui()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password")
        password_entry.delete(0, tk.END)
        password_entry.focus_set()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Optiedge Inventory System")
root.geometry("950x600")
root.configure(bg="#f0f0f0")
root.minsize(900, 560)

# Initialize modern theme (ttkbootstrap)
tb.Style(theme='flatly')
# Consistent readable fonts
root.option_add("*Font", ("Segoe UI", 12))
root.option_add("*TLabel.Font", ("Segoe UI", 12))
root.option_add("*TEntry.Font", ("Segoe UI", 12))

# Preferences helpers
PREFS_FILE = "ui_prefs.json"

def load_prefs():
    try:
        if os.path.exists(PREFS_FILE):
            with open(PREFS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_prefs(prefs):
    try:
        with open(PREFS_FILE, 'w') as f:
            json.dump(prefs, f)
    except Exception:
        pass

prefs = load_prefs()
if 'window' in prefs and isinstance(prefs['window'], dict):
    w = prefs['window'].get('width')
    h = prefs['window'].get('height')
    if w and h:
        root.geometry(f"{w}x{h}")

# Menu bar (File/View/Help)
menubar = tk.Menu(root)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Export CSV", command=export_csv)
file_menu.add_command(label="Export Selected", command=export_selected_csv)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Comfortable Density", command=lambda: set_density("Comfortable"))
view_menu.add_command(label="Compact Density", command=lambda: set_density("Compact"))
menubar.add_cascade(label="View", menu=view_menu)

help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
help_menu.add_command(label="Keyboard Shortcuts", command=show_shortcuts)
menubar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menubar)

# Toast notifications
def show_toast(message: str, duration_ms: int = 1800):
    try:
        toast = tk.Toplevel(root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        toast.configure(bg='#111111')
        label = tk.Label(toast, text=message, fg='white', bg='#111111', font=("Arial", 10, "bold"), padx=12, pady=8)
        label.pack()
        # Position bottom-right
        root.update_idletasks()
        x = root.winfo_x() + root.winfo_width() - toast.winfo_reqwidth() - 20
        y = root.winfo_y() + root.winfo_height() - toast.winfo_reqheight() - 40
        toast.geometry(f"+{x}+{y}")
        toast.after(duration_ms, toast.destroy)
    except Exception:
        pass
# Header - Blue background, centered logo and title
header_frame = tk.Frame(root, bg="#2196F3")
header_frame.pack(fill="x")
header_inner = tk.Frame(header_frame, bg="#2196F3")
header_inner.pack(pady=12)

# Logo loading: prefer Pillow for resizing; otherwise try native Tk PhotoImage
logo_photo = None
if PIL_AVAILABLE:
    try:
        img = Image.open("logo.png")
        img = img.resize((60, 60))
        logo_photo = ImageTk.PhotoImage(img)
    except Exception:
        logo_photo = None
if logo_photo is None:
    try:
        logo_photo = tk.PhotoImage(file="logo.png")
    except Exception:
        logo_photo = None
if logo_photo is not None:
    logo_label = tk.Label(header_inner, image=logo_photo, bg="#2196F3")
    logo_label.image = logo_photo
    logo_label.pack(pady=4)

tk.Label(header_inner, text="Optiedge Inventory System", font=("Segoe UI", 20, "bold"),
         fg="white", bg="#2196F3").pack(pady=(0, 8))

# Login Frame
login_frame = tk.Frame(root, bg="#f0f0f0")
login_frame.pack(pady=100)

tk.Label(login_frame, text="Username", font=("Arial", 12), bg="#f0f0f0", fg="black").grid(row=0, column=0, padx=10, pady=5)
tk.Label(login_frame, text="Password", font=("Arial", 12), bg="#f0f0f0", fg="black").grid(row=1, column=0, padx=10, pady=5)

username_entry = tk.Entry(login_frame, font=("Arial", 12))
password_entry = tk.Entry(login_frame, font=("Arial", 12), show="*")

username_entry.grid(row=0, column=1, padx=10, pady=5)
password_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Button(login_frame, text="Login", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
          width=15, command=login).grid(row=2, column=0, columnspan=2, pady=15)

# Inventory Frame
def build_inventory_ui():
    global name_entry, price_entry, quantity_entry, tree, search_entry, total_label, error_label
    inventory_frame = tk.Frame(root, bg="#f0f0f0")
    inventory_frame.pack(pady=10, fill="x")

    tk.Label(inventory_frame, text="Product Name", font=("Arial", 12), bg="#f0f0f0", fg="black").grid(row=0, column=0, padx=10, pady=5)
    tk.Label(inventory_frame, text="Price", font=("Arial", 12), bg="#f0f0f0", fg="black").grid(row=1, column=0, padx=10, pady=5)
    tk.Label(inventory_frame, text="Quantity", font=("Arial", 12), bg="#f0f0f0", fg="black").grid(row=2, column=0, padx=10, pady=5)

    name_entry = tk.Entry(inventory_frame, font=("Arial", 12))
    # Live validation functions
    vcmd_price = (root.register(lambda s: s == "" or s.replace('.', '', 1).isdigit()), '%P')
    vcmd_qty = (root.register(lambda s: s == "" or s.isdigit()), '%P')
    price_entry = tk.Entry(inventory_frame, font=("Arial", 12), validate='key', validatecommand=vcmd_price)
    quantity_entry = tk.Entry(inventory_frame, font=("Arial", 12), validate='key', validatecommand=vcmd_qty)

    name_entry.grid(row=0, column=1, padx=10, pady=5)
    price_entry.grid(row=1, column=1, padx=10, pady=5)
    quantity_entry.grid(row=2, column=1, padx=10, pady=5)

    # Inline error label
    error_label = tk.Label(inventory_frame, text="", font=("Arial", 10), fg="#dc2626", bg="#f0f0f0")
    error_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(2, 0))

    create_button(inventory_frame, "Add Product", add_product, "primary").grid(row=0, column=2, padx=10)
    create_button(inventory_frame, "Update Product", update_product, "primary-outline").grid(row=1, column=2, padx=10)
    create_button(inventory_frame, "Delete Product", delete_product, "dark").grid(row=2, column=2, padx=10)
    create_button(inventory_frame, "Export to CSV", export_csv, "primary").grid(row=3, column=2, padx=10)
    root.bind_all('<Control-s>', lambda e: export_csv())
    root.bind_all('<Control-n>', lambda e: add_product())

    # Search
    tk.Label(inventory_frame, text="Search Product", font=("Arial", 12), bg="#f0f0f0", fg="black").grid(row=3, column=0, padx=10)
    search_entry = tk.Entry(inventory_frame, font=("Arial", 12))
    search_entry.grid(row=3, column=1, padx=10)
    tb.Button(inventory_frame, text="Search", bootstyle="dark", width=14,
              command=search_product).grid(row=3, column=3, padx=10)
    tb.Button(inventory_frame, text="Reset", bootstyle="primary-outline", width=12,
              command=lambda: [search_entry.delete(0, tk.END), load_products()]).grid(row=3, column=2, padx=10)
    # (moved) restore last search after Treeview is created

    # Treeview
    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 11), rowheight=30)
    style.configure("Treeview.Heading", background="#2196F3", foreground="white", font=("Arial", 12, "bold"))
    style.map('Treeview',
              background=[('selected', '#2196F3'), ('!selected', 'white'), ('active', '#EAF2FE')],
              foreground=[('selected', 'white')])

    table_wrap = tk.Frame(root, bg="#f0f0f0")
    table_wrap.pack(pady=10, fill="both", expand=True)

    columns = ("ID", "Name", "Price", "Quantity")
    tree = ttk.Treeview(table_wrap, columns=columns, show="headings")
    # Sorting by clicking headers
    def sort_by(col, reverse=False):
        col_idx = {"ID": 0, "Name": 1, "Price": 2, "Quantity": 3}[col]
        data = []
        for iid in tree.get_children(""):
            vals = tree.item(iid, "values")
            key = vals[col_idx]
            if col in ("ID", "Price", "Quantity"):
                try:
                    key = float(key)
                except Exception:
                    pass
            data.append((key, iid, vals))
        data.sort(key=lambda x: x[0], reverse=reverse)
        for i, (_, iid, vals) in enumerate(data):
            tree.move(iid, "", i)
            tree.item(iid, values=vals, tags=(("evenrow",) if i % 2 == 0 else ("oddrow",)))
        tree.heading(col, command=lambda c=col, r=not reverse: sort_by(c, r))
        color_rows()

    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_by(c, False))

    # Apply saved column widths if available
    widths = prefs.get('columns', {}) if isinstance(prefs.get('columns'), dict) else {}
    tree.column("ID", width=widths.get('ID', 60), anchor="center")
    tree.column("Name", width=widths.get('Name', 340))
    tree.column("Price", width=widths.get('Price', 140), anchor="center")
    tree.column("Quantity", width=widths.get('Quantity', 140), anchor="center")

    y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview)
    x_scroll = ttk.Scrollbar(table_wrap, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    tree.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")

    table_wrap.grid_columnconfigure(0, weight=1)
    table_wrap.grid_rowconfigure(0, weight=1)

    # Restore density
    if prefs.get('density'):
        set_density(prefs['density'])

    # Double-click to populate form
    def on_row_double_click(event):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], 'values')
        if not vals:
            return
        name_entry.delete(0, tk.END)
        price_entry.delete(0, tk.END)
        quantity_entry.delete(0, tk.END)
        name_entry.insert(0, vals[1])
        price_entry.insert(0, vals[2])
        quantity_entry.insert(0, vals[3])
        name_entry.focus_set()
    tree.bind("<Double-1>", on_row_double_click)

    # Right-click context menu
    context = tk.Menu(root, tearoff=0)
    context.add_command(label="Edit (Load to Form)", command=lambda: on_row_double_click(None))
    context.add_command(label="Delete", command=delete_product)
    context.add_command(label="Export Selected", command=export_selected_csv)

    def show_context_menu(event):
        try:
            row_id = tree.identify_row(event.y)
            if row_id:
                tree.selection_set(row_id)
            context.tk_popup(event.x_root, event.y_root)
        finally:
            context.grab_release()

    tree.bind("<Button-3>", show_context_menu)

    # Alternate row colors
    def color_rows():
        for i, item in enumerate(tree.get_children()):
            tree.item(item, tags=("evenrow",) if i % 2 == 0 else ("oddrow",))
        tree.tag_configure("evenrow", background="#FFFFFF")
        tree.tag_configure("oddrow", background="#F5F7FA")
    tree.bind("<ButtonRelease-1>", lambda e: color_rows())

    # Total inventory value
    total_label = tk.Label(root, text="Total Inventory Value: ₦0.00", font=("Arial", 14, "bold"), bg="#f0f0f0", fg="black")
    total_label.pack(pady=5)

    # Keyboard shortcuts
    root.bind_all('<Return>', lambda e: search_product())
    root.bind_all('<Control-f>', lambda e: search_entry.focus_set())
    root.bind_all('<Delete>', lambda e: delete_product())

    load_products()
    update_total_value()
    color_rows()
    # Restore last search (now table exists)
    if prefs.get('last_search'):
        search_entry.delete(0, tk.END)
        search_entry.insert(0, prefs['last_search'])
        search_product()

def save_and_quit():
    # Save window size and column widths
    try:
        w = root.winfo_width()
        h = root.winfo_height()
        prefs['window'] = {'width': w, 'height': h}
        if 'columns' not in prefs:
            prefs['columns'] = {}
        try:
            cols = { 'ID': tree.column('ID')['width'],
                     'Name': tree.column('Name')['width'],
                     'Price': tree.column('Price')['width'],
                     'Quantity': tree.column('Quantity')['width'] }
            prefs['columns'] = cols
        except Exception:
            pass
        save_prefs(prefs)
    except Exception:
        pass
    root.destroy()
    try:
        conn.close()
    except Exception:
        pass

root.protocol("WM_DELETE_WINDOW", save_and_quit)
root.mainloop()
