"""
Inventory View — Refactored for batch-wise stock management and enforced validation.
Strict separation from Medicines module with controlled stock entry flows.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
import re

from models.product import (
    get_inventory_list, 
    check_batch_exists, 
    add_new_stock, 
    update_existing_stock_qty,
    update_inventory_batch_details
)
from db.connection import execute_query, fetch_all

# -- Colour palette --
BG_DARK = "#F8F9FA"
CARD_BG = "#FFFFFF"
BORDER_CLR = "#E5E7EB"
ACCENT = "#4361EE"
ACCENT_HOVER = "#3A0CA3"
TEXT_DARK = "#111827"
TEXT_MUTED = "#6B7280"
ENTRY_BG = "#F9FAFB"
SUCCESS = "#10B981"
SUCCESS_HOV = "#059669"
WARNING = "#F59E0B"
DANGER = "#EF4444"


class InventoryView(ctk.CTkFrame):
    """Refactored View for batch-wise inventory management."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self.inventory_data = []
        self.medicines = []
        self.suppliers = []
        self.editing_batch_id = None  # For "Edit Details" mode if allowed

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # -- Top bar --
        top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=60, border_width=1, border_color=BORDER_CLR)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Dashboard", width=120, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            top, text="📦  Inventory Management",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # -- Main 2-Column Split --
        split_container = ctk.CTkFrame(self, fg_color="transparent")
        split_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Column (Table)
        self.left_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Right Column (Form)
        self.right_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR, width=380)
        self.right_col.pack(side="right", fill="y")
        self.right_col.pack_propagate(False)

        self._build_table_area()
        self._build_form_area()

    def _build_table_area(self):
        # -- Toolbar --
        toolbar = ctk.CTkFrame(self.left_col, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=15)

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search batch or medicine...",
            width=280, height=38, font=ctk.CTkFont(size=12), corner_radius=8,
            fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK
        )
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        ctk.CTkLabel(toolbar, text="Stock managed batch-wise", font=ctk.CTkFont(size=11, slant="italic"), text_color=TEXT_MUTED).pack(side="right", padx=10)

        # Header
        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("Medicine Name", 160), ("Batch Number", 100), ("Supplier", 110), 
            ("Expiry", 85), ("Qty", 50), ("Purchase", 75), ("Status", 80), ("", 50)
        ]

        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text not in ["Qty", "Purchase", "Status", ""] else "center"
            ).pack(side="left", padx=3)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading inventory...", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.loading_lbl.pack(pady=40)

    def _build_form_area(self):
        self.form_title = ctk.CTkLabel(
            self.right_col, text="Add Inventory",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        self.form_title.pack(pady=(25, 15))

        # Scrollable form container
        form_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True)

        def add_field(parent, label_text, placeholder, required=True, command=None):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=20, pady=(4, 8), fill="x")

            lbl_row = ctk.CTkFrame(row, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(0, 3))
            ctk.CTkLabel(lbl_row, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
            if required:
                ctk.CTkLabel(lbl_row, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w", height=15).pack(side="left")

            entry = ctk.CTkEntry(
                row, placeholder_text=placeholder, height=38, font=ctk.CTkFont(size=12),
                fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
            )
            entry.pack(fill="x")
            if command:
                entry.bind("<KeyRelease>", command)
            return entry

        # Medicine Dropdown
        med_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        med_row.pack(padx=20, pady=(4, 8), fill="x")
        ctk.CTkLabel(med_row, text="Select Medicine *", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 3))
        self.f_medicine = ctk.CTkComboBox(
            med_row, values=["Loading..."], height=38, font=ctk.CTkFont(size=12),
            fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
            corner_radius=6, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            command=lambda _: self._validate_form()
        )
        self.f_medicine.pack(fill="x")
        self.f_medicine.set("")

        self.f_batch = add_field(form_scroll, "Batch Number", "3-20 chars", command=lambda e: self._validate_form())
        
        # Supplier Dropdown
        sup_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        sup_row.pack(padx=20, pady=(4, 8), fill="x")
        ctk.CTkLabel(sup_row, text="Supplier *", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 3))
        self.f_supplier = ctk.CTkComboBox(
            sup_row, values=["Loading..."], height=38, font=ctk.CTkFont(size=12),
            fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
            corner_radius=6, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            command=lambda _: self._validate_form()
        )
        self.f_supplier.pack(fill="x")
        self.f_supplier.set("")

        self.f_expiry = add_field(form_scroll, "Expiry Date", "YYYY-MM-DD", command=lambda e: self._validate_form())
        self.f_quantity = add_field(form_scroll, "Quantity", "Enter positive number", command=lambda e: self._validate_form())
        self.f_purchase = add_field(form_scroll, "Purchase Price (₹)", "Price per unit", command=lambda e: self._validate_form())

        # Validation status label
        self.v_lbl = ctk.CTkLabel(form_scroll, text="", font=ctk.CTkFont(size=11), text_color=DANGER)
        self.v_lbl.pack(pady=5)

        # Buttons
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.save_btn = ctk.CTkButton(
            btn_frame, text="Add Inventory", height=42,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._handle_save, state="disabled"
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.clear_btn = ctk.CTkButton(
            btn_frame, text="Reset", height=42,
            font=ctk.CTkFont(size=13), corner_radius=10,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._clear_form
        )
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _load_data(self):
        try:
            self.inventory_data = get_inventory_list(self.user["distributor_id"])
            
            # Fetch medicines & suppliers
            self.medicines = fetch_all("SELECT medicine_id, name FROM medicines ORDER BY name")
            self.suppliers = fetch_all("SELECT supplier_id, name FROM suppliers WHERE distributor_id = %s ORDER BY name", (self.user["distributor_id"],))

            med_names = [m["name"] for m in self.medicines]
            sup_names = [s["name"] for s in self.suppliers]
            self.f_medicine.configure(values=med_names)
            self.f_supplier.configure(values=sup_names)

            self._apply_filters()
        except Exception as e:
            self.loading_lbl.configure(text=f"Error: {e}", text_color=DANGER)

    def _validate_form(self):
        """Perform real-time validation and enable/disable Save button."""
        errors = []
        med = self.f_medicine.get().strip()
        batch = self.f_batch.get().strip()
        sup = self.f_supplier.get().strip()
        exp = self.f_expiry.get().strip()
        qty = self.f_quantity.get().strip()
        purchase = self.f_purchase.get().strip()

        if not med or med == "Loading...": errors.append("Select Medicine")
        if not sup or sup == "Loading...": errors.append("Select Supplier")
        
        # Batch: Alphanumeric, 3-20
        if not re.match(r"^[a-zA-Z0-9]{3,20}$", batch):
            errors.append("Batch: 3-20 Alphanumeric")
        
        # Qty: Positive Int
        try:
            if int(qty) <= 0: errors.append("Qty must be > 0")
        except: errors.append("Qty must be number")

        # Purchase: Positive Float
        try:
            if float(purchase) <= 0: errors.append("Price must be > 0")
        except: errors.append("Price must be number")

        # Expiry: Future YYYY-MM-DD
        try:
            exp_d = datetime.strptime(exp, "%Y-%m-%d").date()
            if exp_d <= date.today(): errors.append("Expiry must be future")
        except: errors.append("Expiry: YYYY-MM-DD")

        if errors:
            self.v_lbl.configure(text=f"⚠  {errors[0]}")
            self.save_btn.configure(state="disabled", fg_color="#D1D5DB")
        else:
            self.v_lbl.configure(text="✅  Form Valid", text_color=SUCCESS)
            self.save_btn.configure(state="normal", fg_color=SUCCESS)

    def _apply_filters(self):
        query = self.search_var.get().strip().lower()
        for widget in self.scroll.winfo_children(): widget.destroy()

        # Sort by expiry (FIFO concept)
        self.inventory_data.sort(key=lambda x: x.get('expiry_date') if x.get('expiry_date') else date.max)

        filtered = [r for r in self.inventory_data if query in str(r.get("product_name", "")).lower() or query in str(r.get("batch_number", "")).lower()]
        
        if not filtered:
            ctk.CTkLabel(self.scroll, text="No items found.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        today = date.today()
        for row in filtered:
            f = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
            f.pack(fill="x", pady=1)
            f.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=5)

            exp = row.get("expiry_date")
            qty = int(row.get("quantity", 0))
            is_expired = exp < today if exp else False
            is_near_expiry = (exp - today).days < 30 if exp and not is_expired else False
            is_low_stock = qty < 10

            text_clr = TEXT_DARK
            if is_expired: text_clr = DANGER
            elif is_near_expiry or is_low_stock: text_clr = WARNING

            cols = [
                (str(row.get("product_name", ""))[:20], 160, "w"),
                (str(row.get("batch_number", "")), 100, "w"),
                (str(row.get("supplier_name", "") or "N/A")[:18], 110, "w"),
                (exp.strftime("%d/%m/%y") if exp else "N/A", 85, "w"),
                (str(qty), 50, "center"),
                (f"₹{float(row.get('purchase_price', 0)):.2f}", 75, "center"),
            ]

            for val, w, anchor in cols:
                ctk.CTkLabel(f, text=val, width=w, font=ctk.CTkFont(size=10, weight="bold" if text_clr != TEXT_DARK else "normal"), text_color=text_clr, anchor=anchor).pack(side="left", padx=3)

            # Status Tag
            status = "ACTIVE"
            s_bg = "#ECFDF5"; s_fg = "#065F46"
            if is_expired: status = "EXPIRED"; s_bg = "#FEF2F2"; s_fg = "#991B1B"
            elif is_near_expiry: status = "NEAR EXP"; s_bg = "#FFF7ED"; s_fg = "#9A3412"
            elif is_low_stock: status = "LOW STOCK"; s_bg = "#FEFCE8"; s_fg = "#854D0E"

            tag = ctk.CTkFrame(f, fg_color=s_bg, corner_radius=6, height=22, width=80)
            tag.pack_propagate(False)
            tag.pack(side="left", padx=3, pady=10)
            ctk.CTkLabel(tag, text=status, text_color=s_fg, font=ctk.CTkFont(size=9, weight="bold")).pack(expand=True)

            # Details/Edit button (Admin Only concept)
            ctk.CTkButton(
                f, text="✎", width=40, height=26, font=ctk.CTkFont(size=12),
                fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
                command=lambda r=row: self._start_edit_details(r)
            ).pack(side="left", padx=5)

    def _handle_save(self):
        med_name = self.f_medicine.get()
        sup_name = self.f_supplier.get()
        batch_no = self.f_batch.get().strip().upper()
        exp_date = self.f_expiry.get().strip()
        qty = int(self.f_quantity.get().strip())
        price = float(self.f_purchase.get().strip())

        med_id = next((m["medicine_id"] for m in self.medicines if m["name"] == med_name), None)
        sup_id = next((s["supplier_id"] for s in self.suppliers if s["name"] == sup_name), None)

        # Check for existing batch (Merge Logic)
        existing = check_batch_exists(self.user["distributor_id"], med_id, batch_no)

        if existing:
            msg = f"This batch already exists.\nExisting Qty: {existing['quantity']}\nNew Qty: +{qty}\nTotal will be: {existing['quantity'] + qty}\n\nContinue?"
            if not messagebox.askyesno("Batch Found", msg):
                return
            
            try:
                update_existing_stock_qty(existing["batch_id"], qty, price)
                messagebox.showinfo("Success", "Stock updated successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update stock: {e}")
        else:
            if not messagebox.askyesno("Confirm Add", "Are you sure you want to add this stock?"):
                return
            
            try:
                add_new_stock(self.user["distributor_id"], med_id, sup_id, batch_no, exp_date, qty, price)
                messagebox.showinfo("Success", "New stock batch added successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add stock: {e}")

        self._clear_form()
        self._load_data()

    def _start_edit_details(self, row):
        """Restricted edit mode for correcting non-quantity details."""
        self._clear_form()
        self.editing_batch_id = row["batch_id"]
        self.form_title.configure(text="Edit Stock Details")
        self.save_btn.configure(text="Apply Changes", fg_color=WARNING)

        self.f_medicine.set(row["product_name"])
        self.f_medicine.configure(state="disabled")
        self.f_batch.insert(0, row["batch_number"])
        self.f_supplier.set(row["supplier_name"] or "")
        self.f_expiry.insert(0, str(row["expiry_date"]))
        self.f_quantity.insert(0, str(row["quantity"]))
        self.f_quantity.configure(state="disabled")  # Direct qty edit not allowed
        self.f_purchase.insert(0, str(row["purchase_price"]))
        
        self.v_lbl.configure(text="⚠  Qty/Medicine locking active.", text_color=WARNING)
        self.save_btn.configure(state="normal")
        # Update command to handle direct updates for non-locked fields
        self.save_btn.configure(command=self._handle_restricted_update)

    def _handle_restricted_update(self):
        """Handles updating non-locked fields in the details mode."""
        if not messagebox.askyesno("Confirm Changes", "Apply changes to this batch details?"):
            return
        
        try:
            sup_name = self.f_supplier.get()
            b_no = self.f_batch.get().strip().upper()
            exp = self.f_expiry.get().strip()
            price = float(self.f_purchase.get().strip())
            
            sup_id = next((s["supplier_id"] for s in self.suppliers if s["name"] == sup_name), None)

            update_inventory_batch_details(self.editing_batch_id, sup_id, b_no, exp, price)
            messagebox.showinfo("Success", "Batch details updated.")
            self._clear_form()
            self._load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    def _clear_form(self):
        self.editing_batch_id = None
        self.form_title.configure(text="Add Inventory")
        self.save_btn.configure(text="Add Inventory", fg_color=SUCCESS, command=self._handle_save)
        self.f_medicine.configure(state="normal")
        self.f_medicine.set("")
        self.f_batch.delete(0, "end")
        self.f_supplier.set("")
        self.f_expiry.delete(0, "end")
        self.f_quantity.configure(state="normal")
        self.f_quantity.delete(0, "end")
        self.f_purchase.delete(0, "end")
        self.v_lbl.configure(text="")
        self.save_btn.configure(state="disabled")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children(): widget.destroy()
        Dashboard(self.master, self.user, self.app).pack(fill="both", expand=True)
