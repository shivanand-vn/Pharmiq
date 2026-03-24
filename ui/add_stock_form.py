"""
Add Stock Form — CustomTkinter form for adding stock (batches) for medicines.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from db.connection import execute_query, fetch_all

# ── Colour palette ──
BG_DARK = "#0f0f1a"
CARD_BG = "#16213e"
BORDER_CLR = "#2a2a4a"
ACCENT = "#00d4ff"
TEXT_WHITE = "#ffffff"
TEXT_MUTED = "#888899"
ENTRY_BG = "#0f0f1a"
SUCCESS = "#00b894"


class AddStockForm(ctk.CTkFrame):
    """Form to restock medicines."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self.medicines = []
        self.suppliers = []

        self._load_data()
        self._build_ui()

    def _load_data(self):
        try:
            self.medicines = fetch_all("SELECT medicine_id, name FROM medicines ORDER BY name")
            self.suppliers = fetch_all(
                "SELECT supplier_id, name FROM suppliers WHERE distributor_id = %s ORDER BY name",
                (self.user["distributor_id"],)
            )
        except Exception as e:
            print(f"Error loading medicines/suppliers: {e}")

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=80, height=30,
            font=ctk.CTkFont(size=11), corner_radius=8,
            fg_color="#333355", hover_color="#444466",
            command=self._go_back,
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top, text="📦  Add Stock (New Batch)",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Form Content ──
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_CLR)
        card.pack(fill="x", padx=10, pady=20)

        def add_row(parent, label_text, widget_class=ctk.CTkEntry, **kwargs):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row, text=label_text, width=150, anchor="w",
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left")
            widget = widget_class(row, height=35, font=ctk.CTkFont(size=12), **kwargs)
            widget.pack(side="left", fill="x", expand=True)
            return widget

        # Medicine Dropdown
        med_names = [m["name"] for m in self.medicines] if self.medicines else ["No matching medicines"]
        self.medicine_cb = add_row(card, "Select Medicine", ctk.CTkOptionMenu, values=med_names,
                                   fg_color=ENTRY_BG, button_color=ACCENT, text_color=TEXT_WHITE)

        # Supplier Dropdown
        sup_names = [s["name"] for s in self.suppliers] if self.suppliers else ["No suppliers found"]
        self.supplier_cb = add_row(card, "Select Supplier", ctk.CTkOptionMenu, values=sup_names,
                                   fg_color=ENTRY_BG, button_color=ACCENT, text_color=TEXT_WHITE)

        self.batch_entry = add_row(card, "Batch Number")
        self.expiry_entry = add_row(card, "Expiry Date (YYYY-MM-DD)")
        self.quantity_entry = add_row(card, "Quantity")
        self.purchase_price_entry = add_row(card, "Purchase Price (₹)")
        self.mrp_entry = add_row(card, "MRP (₹)")

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame, text="✅  Save Batch", height=45, width=200,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            fg_color=SUCCESS, hover_color="#009975", text_color=TEXT_WHITE,
            command=self._save_stock,
        ).pack(side="left", padx=5)

    def _save_stock(self):
        med_name = self.medicine_cb.get()
        sup_name = self.supplier_cb.get()

        med_id = next((m["medicine_id"] for m in self.medicines if m["name"] == med_name), None)
        sup_id = next((s["supplier_id"] for s in self.suppliers if s["name"] == sup_name), None)

        batch_no = self.batch_entry.get().strip()
        expiry_date = self.expiry_entry.get().strip()
        qty = self.quantity_entry.get().strip()
        pur_price = self.purchase_price_entry.get().strip()
        mrp = self.mrp_entry.get().strip()

        if not all([med_id, sup_id, batch_no, expiry_date, qty, pur_price, mrp]):
            messagebox.showwarning("Incomplete", "All fields are required.")
            return

        try:
            # Validate numeric and date fields
            qty = int(qty)
            pur_price = float(pur_price)
            mrp = float(mrp)
            datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError as ve:
            messagebox.showerror("Invalid Data", "Please check your inputs (Date format YYYY-MM-DD, numbers for qty/prices).\n\n" + str(ve))
            return

        try:
            query = """
                INSERT INTO batches 
                (medicine_id, supplier_id, distributor_id, batch_no, expiry_date, quantity, purchase_price, mrp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            execute_query(query, (
                med_id, sup_id, self.user["distributor_id"], batch_no, expiry_date, qty, pur_price, mrp
            ))

            messagebox.showinfo("Success", "Stock added successfully!")
            self._go_back()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save stock:\n{e}")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
