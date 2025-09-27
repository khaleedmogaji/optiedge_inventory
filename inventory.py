import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import ttkbootstrap as tb
from datetime import datetime
import sys

# --- Global Variables ---
conn = cursor = root = style = None
login_frame = inventory_frame = None
username_entry = password_entry = None
name_entry = price_entry = qty_entry = search_entry = None
tree = None
total_qty_label = total_value_label = None
clock_label = None
form = None

# --- Database Functions ---
def init_database():
    global conn, cursor
    conn = sqlite3.connect("optiedge_inventory.db")
    cursor = conn.cursor()

    # Create products table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL
    )""")

    # --- Add this block here ---
    # Ensure updated_at column exists
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'updated_at' not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN updated_at TEXT")
        conn.commit()
    # ----------------------------

    # Create users table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )""")

    # Create default admin
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)", ("admin","admin123"))
        conn.commit()
    
    return conn, cursor


# --- Validation ---
def validate_product_input(name, price_str, qty_str):
    if not name: raise ValueError("Name is required")
    if not price_str or not qty_str: raise ValueError("Price and Quantity required")
    try:
        price = float(price_str.replace('₦','').replace(',',''))
        qty = int(qty_str.replace(',',''))
        if price<0 or qty<0: raise ValueError
        return price, qty
    except:
        raise ValueError("Invalid Price or Quantity")

# --- Styles ---
def setup_styles():
    style.configure("success.TButton", font=("Segoe UI",11,"bold"), padding=(20,10))
    style.configure("info.TButton", font=("Segoe UI",11,"bold"), padding=(20,10))
    style.configure("danger.TButton", font=("Segoe UI",11,"bold"), padding=(20,10))
    style.configure("warning.TButton", font=("Segoe UI",11,"bold"), padding=(20,10))
    style.configure("primary.TButton", font=("Segoe UI",11,"bold"), padding=(20,10))
    style.configure("Modern.TLabelframe", background="#FFFFFF", borderwidth=2, relief="solid", bordercolor="#E1E5E9")
    style.configure("Modern.TLabelframe.Label", font=("Segoe UI",12,"bold"), background="#FFFFFF", foreground="#2E3A59")
    style.configure("Custom.Treeview", rowheight=35, font=("Segoe UI",10))
    style.configure("Custom.Treeview.Heading", font=("Segoe UI",11,"bold"), padding=10, background="#2E3A59", foreground="white")
    style.configure("Modern.TEntry", font=("Segoe UI",11), padding=8)

def create_modern_button(parent, text, style_name, command, width=15):
    return ttk.Button(parent, text=text, style=f"{style_name}.TButton", command=command, width=width)

# --- Login ---
def setup_login_frame():
    import os
    from PIL import Image, ImageTk

    global username_entry, password_entry
    for w in login_frame.winfo_children(): 
        w.destroy()

    login_frame.pack(fill="both", expand=True)
    login_frame.configure(bg="#F8FAFC")

    center_frame = tk.Frame(login_frame, bg="#F8FAFC")
    center_frame.pack(expand=True)

    content_frame = tk.Frame(center_frame, bg="#F8FAFC")
    content_frame.pack(padx=30, pady=30)

    # --- Logo ---
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        img = Image.open(logo_path)
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(content_frame, image=logo_photo, bg="#F8FAFC")
        logo_label.pack(pady=(0, 15))
        center_frame.logo_photo = logo_photo  # keep reference

    # --- Title ---
    tk.Label(content_frame, text="OPTIEDGE INVENTORY", font=("Segoe UI", 22, "bold"), bg="#F8FAFC").pack(pady=(0,5))
    tk.Label(content_frame, text="Management System", font=("Segoe UI", 14), bg="#F8FAFC").pack(pady=(0,15))

    # --- Login Form ---
    form_frame = tk.Frame(content_frame, bg="#F8FAFC")
    form_frame.pack(fill="x")

    tk.Label(form_frame, text="Username", bg="#F8FAFC").pack(anchor="w")
    username_entry = ttk.Entry(form_frame, style="Modern.TEntry")
    username_entry.pack(fill="x", pady=5)

    tk.Label(form_frame, text="Password", bg="#F8FAFC").pack(anchor="w")
    password_entry = ttk.Entry(form_frame, show="•", style="Modern.TEntry")
    password_entry.pack(fill="x", pady=5)

    ttk.Button(form_frame, text="Login", style="primary.TButton", command=login).pack(pady=10, fill="x")

    # --- Bind Enter key ---
    password_entry.bind("<Return>", lambda e: login())
    username_entry.focus()


def login():
    username=username_entry.get().strip(); password=password_entry.get().strip()
    if not username or not password: messagebox.showwarning("Warning","Enter username & password"); return
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
    if cursor.fetchone(): show_inventory()
    else: messagebox.showerror("Login Failed","❌ Invalid username or password")

# --- Inventory Frame ---
def create_inventory_frame():
    global clock_label
    header = tk.Frame(inventory_frame,bg="#1F2937",height=70); header.pack(fill="x"); header.pack_propagate(False)
    tk.Label(header,text="🏪 OPTIEDGE INVENTORY SYSTEM", font=("Segoe UI",18,"bold"), bg="#1F2937",fg="white").pack(side="left", padx=20)
    clock_label = tk.Label(header,font=("Segoe UI",11),bg="#1F2937",fg="#D1D5DB"); clock_label.pack(side="left",expand=True)
    ttk.Button(header,text="🚪 Logout", style="danger.TButton", command=logout).pack(side="right", padx=10)
    create_form_frame(); create_search_frame(); create_table_frame(); create_totals_frame()

def create_form_frame():
    global name_entry, price_entry, qty_entry, form
    form = ttk.LabelFrame(inventory_frame, text="📦 Product Details", padding=20, style="Modern.TLabelframe"); form.pack(padx=25,pady=15, fill="x")
    name_entry = ttk.Entry(form, style="Modern.TEntry"); price_entry = ttk.Entry(form, style="Modern.TEntry"); qty_entry = ttk.Entry(form, style="Modern.TEntry")
    labels=["Product Name:","Price (₦):","Quantity:"]; entries=[name_entry,price_entry,qty_entry]
    for i,(label,entry) in enumerate(zip(labels,entries)): 
        ttk.Label(form,text=label,font=("Segoe UI",11,"bold")).grid(row=i,column=0,padx=5,pady=5,sticky="w"); entry.grid(row=i,column=1,padx=5,pady=5,sticky="ew")
    form.columnconfigure(1,weight=1)
    btn_frame=ttk.Frame(form); btn_frame.grid(row=0,column=2,rowspan=3,padx=20)
    for txt,style_name,cmd in [("➕ Add","success",add_product),("✏️ Update","info",update_product),
                               ("🗑️ Delete","danger",delete_product),("🧹 Clear","warning",clear_entries),
                               ("📤 Export","primary",export_csv)]:
        create_modern_button(btn_frame,txt,style_name,cmd).pack(pady=5,fill="x")
    # Bind price auto-format
    price_entry.bind("<FocusOut>", price_entry)
    price_entry.bind("<KeyRelease>", price_entry)


def create_search_frame():
    global search_entry
    search_frame=ttk.LabelFrame(inventory_frame,text="🔍 Search Products",padding=15,style="Modern.TLabelframe"); search_frame.pack(fill="x", padx=25, pady=10)
    search_entry = ttk.Entry(search_frame, style="Modern.TEntry"); search_entry.pack(side="left",fill="x",expand=True,padx=5, ipady=5)
    create_modern_button(search_frame,"Search","primary",search_product).pack(side="left", padx=5)
    create_modern_button(search_frame,"Refresh","info",load_products).pack(side="left")

def create_table_frame():
    global tree
    table_frame=ttk.LabelFrame(inventory_frame,text="📋 Product Inventory",padding=15,style="Modern.TLabelframe"); table_frame.pack(fill="both", padx=25, pady=10, expand=True)
    columns=("ID","Name","Price","Quantity","Total Value"); tree=ttk.Treeview(table_frame,columns=columns,show="headings",style="Custom.Treeview",height=15)
    col_config={"ID":{"width":80,"anchor":"center","text":"🆔 ID"},"Name":{"width":350,"anchor":"w","text":"📛 Product Name"},"Price":{"width":150,"anchor":"e","text":"💰 Price"},"Quantity":{"width":120,"anchor":"center","text":"📦 Quantity"},"Total Value":{"width":150,"anchor":"e","text":"💵 Total Value"}}
    for col in columns: 
        tree.heading(col,text=col_config[col]["text"],command=lambda c=col: sort_treeview(c,False))
        tree.column(col, **{k:v for k,v in col_config[col].items() if k!="text"})
    tree.grid(row=0,column=0,sticky="nsew")
    ttk.Scrollbar(table_frame,orient="vertical",command=tree.yview).grid(row=0,column=1,sticky="ns")
    ttk.Scrollbar(table_frame,orient="horizontal",command=tree.xview).grid(row=1,column=0,sticky="ew")
    table_frame.columnconfigure(0,weight=1); table_frame.rowconfigure(0,weight=1)
    tree.tag_configure('evenrow', background='#F8FAFC'); tree.tag_configure('oddrow', background='#FFFFFF')
    tree.bind('<<TreeviewSelect>>', on_tree_select)

def create_totals_frame():
    global total_qty_label,total_value_label
    totals_frame=tk.Frame(inventory_frame,bg="#2E3A59",height=100); totals_frame.pack(side="bottom",fill="x", padx=25, pady=10); totals_frame.pack_propagate(False)
    tk.Label(totals_frame,text="📦 OVERALL TOTAL PRODUCTS",bg="#4F46E5",fg="white", font=("Segoe UI",12,"bold")).pack(side="left",expand=True,fill="both", padx=5, pady=10)
    total_qty_label=tk.Label(totals_frame,text="0",bg="#4F46E5",fg="white", font=("Segoe UI",24,"bold")); total_qty_label.pack(side="left",expand=True,fill="both")
    tk.Label(totals_frame,text="💵 OVERALL TOTAL VALUE",bg="#10B981",fg="white", font=("Segoe UI",12,"bold")).pack(side="left",expand=True,fill="both", padx=5, pady=10)
    total_value_label=tk.Label(totals_frame,text="₦0.00",bg="#10B981",fg="white", font=("Segoe UI",24,"bold")); total_value_label.pack(side="left",expand=True,fill="both")

# --- Core Functions ---
def add_product():
    try:
        name=name_entry.get().strip(); price_str=price_entry.get().strip(); qty_str=qty_entry.get().strip()
        price, qty = validate_product_input(name, price_str, qty_str)
        cursor.execute("INSERT INTO products (name,price,quantity) VALUES (?,?,?)",(name,price,qty)); conn.commit()
        load_products(); clear_entries(); messagebox.showinfo("Success","✅ Product added successfully")
    except Exception as e: messagebox.showerror("Error",str(e))

def update_product():
    sel = tree.selection()
    if not sel: messagebox.showwarning("Warning", "Select a product"); return
    item_id = tree.item(sel[0])['values'][0]
    try:
        name=name_entry.get().strip(); price_str=price_entry.get().strip(); qty_str=qty_entry.get().strip()
        price, qty = validate_product_input(name, price_str, qty_str)
        cursor.execute("UPDATE products SET name=?, price=?, quantity=? WHERE id=?",
                       (name, price, qty, item_id)); conn.commit()
        load_products(); clear_entries(); messagebox.showinfo("Success","✅ Product updated successfully")
    except Exception as e: messagebox.showerror("Error",f"Failed to update product: {str(e)}"); conn.rollback()

def delete_product():
    sel=tree.selection(); 
    if not sel: messagebox.showwarning("Warning","Select product"); return
    vals=tree.item(sel[0])["values"]
    if messagebox.askyesno("Confirm Delete",f"Delete '{vals[1]}'?"):
        cursor.execute("DELETE FROM products WHERE id=?",(vals[0],)); conn.commit(); load_products(); clear_entries()

def clear_entries(): 
    for e in [name_entry,price_entry,qty_entry,search_entry]: e.delete(0,tk.END)

def search_product():
    text=search_entry.get().strip().lower()
    for i in tree.get_children(): tree.delete(i)
    cursor.execute("SELECT * FROM products WHERE LOWER(name) LIKE ?",(f"%{text}%",))
    rows=cursor.fetchall()
    if not rows: tree.insert("", "end", values=("", "No matching products","","","")); return
    for i,row in enumerate(rows):
        val=(row[0],row[1],f"₦{row[2]:,.2f}",f"{row[3]:,}",f"₦{row[2]*row[3]:,.2f}")
        tree.insert("", "end", values=val, tags=('evenrow' if i%2==0 else 'oddrow',))
    update_totals()

def load_products():
    for i in tree.get_children(): tree.delete(i)
    cursor.execute("SELECT * FROM products ORDER BY id DESC"); rows=cursor.fetchall()
    for i,row in enumerate(rows):
        val=(row[0],row[1],f"₦{row[2]:,.2f}",f"{row[3]:,}",f"₦{row[2]*row[3]:,.2f}")
        tree.insert("", "end", values=val, tags=('evenrow' if i%2==0 else 'oddrow',))
    update_totals()

def update_totals():
    cursor.execute("SELECT SUM(quantity),SUM(price*quantity) FROM products"); r=cursor.fetchone()
    total_qty_label.config(text=f"{int(r[0] or 0):,}"); total_value_label.config(text=f"₦{float(r[1] or 0):,.2f}")

def on_tree_select(event=None):
    sel=tree.selection(); 
    if not sel: return
    vals=tree.item(sel[0])["values"]
    if not vals or not vals[0]: return
    clear_entries(); 
    name_entry.insert(0,vals[1])
    price_entry.insert(0,str(vals[2]).replace('₦','').replace(',',''))
    qty_entry.insert(0,str(vals[3]).replace(',',''))

def logout():
    if messagebox.askyesno("Logout","Are you sure?"):
        inventory_frame.pack_forget(); setup_login_frame()

def show_inventory():
    login_frame.pack_forget(); inventory_frame.pack(fill="both",expand=True); load_products(); update_clock()

def update_clock():
    time_str=datetime.now().strftime("%I:%M:%S %p"); date_str=datetime.now().strftime("%B %d, %Y")
    if clock_label and clock_label.winfo_exists(): clock_label.config(text=f"🕒 {date_str} | {time_str}"); root.after(1000,update_clock)

def export_csv():
    """Export products to a CSV file with a calculated Total Value column."""
    filename = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        title="Save inventory as CSV"
    )
    if not filename:
        return  # User cancelled

    # Only select the columns we need
    cursor.execute("SELECT id, name, price, quantity FROM products")
    rows = cursor.fetchall()

    # Write the CSV with a computed Total column
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Price", "Quantity", "Total Value"])

        for r in rows:
            pid, name, price, qty = r
            try:
                total_value = float(price) * int(qty)
            except (ValueError, TypeError):
                total_value = 0.0  # fallback if any bad data
            writer.writerow([
                pid,
                name,
                f"{float(price):.2f}",
                qty,
                f"{total_value:.2f}"
            ])

    messagebox.showinfo("Export Complete",
                        f"✅ Exported {len(rows)} products to:\n{filename}")


def sort_treeview(col, reverse):
    l=[(tree.set(k,col),k) for k in tree.get_children('')]
    try:
        if col in ['Price','Quantity','Total Value']: l.sort(key=lambda t: float(str(t[0]).replace('₦','').replace(',','')), reverse=reverse)
        else: l.sort(reverse=reverse)
    except: l.sort(reverse=reverse)
    for index,(val,k) in enumerate(l): tree.move(k,'',index); tree.item(k, tags=('evenrow' if index%2==0 else 'oddrow',))
    tree.heading(col, command=lambda: sort_treeview(col, not reverse))

# --- Initialize App ---
def initialize_app():
    global root, style, login_frame, inventory_frame
    root=tb.Window(title="Optiedge Inventory System",themename="litera"); root.state('zoomed'); root.minsize(1000,700)
    style=tb.Style(theme="litera"); setup_styles()
    login_frame=tk.Frame(root); inventory_frame=tk.Frame(root)
    setup_login_frame(); create_inventory_frame()
    root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    root.mainloop()

# --- Main ---
if __name__=="__main__":
    conn,cursor=init_database()
    initialize_app()
