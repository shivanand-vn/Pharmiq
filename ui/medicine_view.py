"""
Medicine View — Specialized module for managing medicine pricing and basic details.
Restricts editing to pricing-only fields as per strict separation of concerns.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from models.product import get_inventory_list, update_medicine_pricing
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


class MedicineView(ctk.CTkFrame):
    """View to manage medicine details with strict price-only edit rules."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self.inventory_data = []
        self.categories = set()
        self.medicines = []
        self.suppliers = []
        self.editing_batch_id = None  # Track editing state

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
            top, text="💊  Medicine Management",
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
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search medicine...",
            width=250, height=38, font=ctk.CTkFont(size=12), corner_radius=8,
            fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK
        )
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        # Header
        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("Product Name", 140), ("Batch", 80), ("Supplier", 100), ("Expiry", 80),
            ("Qty", 40), ("MRP", 65), ("Sell Price", 75), ("Disc%", 50), ("", 50)
        ]

        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=10, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text not in ["Qty", "MRP", "Sell Price", "Disc%", ""] else "center"
            ).pack(side="left", padx=2)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading medicines...", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.loading_lbl.pack(pady=40)

    def _build_form_area(self):
        self.form_title = ctk.CTkLabel(
            self.right_col, text="Add New Medicine",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        self.form_title.pack(pady=(25, 5))

        self.mode_lbl = ctk.CTkLabel(
            self.right_col, text="",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=WARNING
        )
        self.mode_lbl.pack(pady=(0, 10))

        form_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True)

        def add_field(parent, label_text, placeholder, required=True, tooltip=None):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=20, pady=(4, 8), fill="x")

            lbl_row = ctk.CTkFrame(row, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(0, 3))
            
            ctk.CTkLabel(lbl_row, text=label_text, font=ctk.CTkFont(size=11, weight="bold"), 
                         text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
            if required:
                ctk.CTkLabel(lbl_row, text=" *", font=ctk.CTkFont(size=12, weight="bold"), 
                             text_color=DANGER, anchor="w", height=15).pack(side="left")

            entry = ctk.CTkEntry(
                row, placeholder_text=placeholder, height=36, font=ctk.CTkFont(size=12),
                fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
            )
            entry.pack(fill="x")
            
            # Simple "Tooltip" using a small label below if needed, or we'll just handle state
            return entry, row

        # Fields
        self.f_product_combo_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.f_product_combo_row.pack(padx=20, pady=(4, 8), fill="x")
        ctk.CTkLabel(self.f_product_combo_row, text="Product Name *", font=ctk.CTkFont(size=11, weight="bold"), 
                     text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 3))
        self.f_product = ctk.CTkComboBox(
            self.f_product_combo_row, values=["Loading..."], height=36, font=ctk.CTkFont(size=12),
            fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
            corner_radius=6, button_color=ACCENT, button_hover_color=ACCENT_HOVER
        )
        self.f_product.pack(fill="x")

        self.f_batch, self.f_batch_row = add_field(form_scroll, "Batch No", "e.g. AB123")
        self.f_supplier_combo_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.f_supplier_combo_row.pack(padx=20, pady=(4, 8), fill="x")
        ctk.CTkLabel(self.f_supplier_combo_row, text="Supplier *", font=ctk.CTkFont(size=11, weight="bold"), 
                     text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 3))
        self.f_supplier = ctk.CTkComboBox(
            self.f_supplier_combo_row, values=["Loading..."], height=36, font=ctk.CTkFont(size=12),
            fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
            corner_radius=6, button_color=ACCENT, button_hover_color=ACCENT_HOVER
        )
        self.f_supplier.pack(fill="x")

        self.f_expiry, self.f_expiry_row = add_field(form_scroll, "Expiry Date", "YYYY-MM-DD")
        self.f_quantity, self.f_qty_row = add_field(form_scroll, "Opening Quantity", "e.g. 100")
        
        # --- Pricing Section (Always Editable) ---
        ctk.CTkFrame(form_scroll, fg_color=BORDER_CLR, height=2).pack(fill="x", padx=20, pady=15)
        
        self.f_mrp, self.f_mrp_row = add_field(form_scroll, "MRP (₹)", "Current MRP")
        self.f_selling, self.f_selling_row = add_field(form_scroll, "Selling Price (₹)", "Real Selling Price")
        self.f_discount, self.f_discount_row = add_field(form_scroll, "Default Discount (%)", "e.g. 10.0", required=False)

        # Buttons
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(20, 20))

        self.save_btn = ctk.CTkButton(
            btn_frame, text="Add Medicine", height=40,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._save_medicine
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.clear_btn = ctk.CTkButton(
            btn_frame, text="Clear", height=40,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._clear_form
        )
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Tooltip placeholder labels for disabled fields
        self.tooltips = {}
        for field_name in ["product", "batch", "supplier", "expiry", "qty"]:
            self.tooltips[field_name] = ctk.CTkLabel(
                form_scroll, text="To update stock/batch, use Inventory module.",
                font=ctk.CTkFont(size=10, slant="italic"), text_color=TEXT_MUTED
            )

    def _load_data(self):
        try:
            self.inventory_data = get_inventory_list(self.user["distributor_id"])
            self.medicines = fetch_all("SELECT medicine_id, name FROM medicines ORDER BY name")
            self.suppliers = fetch_all("SELECT supplier_id, name FROM suppliers WHERE distributor_id = %s ORDER BY name", (self.user["distributor_id"],))
            
            med_names = [m["name"] for m in self.medicines]
            sup_names = [s["name"] for s in self.suppliers]
            self.f_product.configure(values=med_names)
            self.f_supplier.configure(values=sup_names)
            
            self._apply_filters()
        except Exception as e:
            self.loading_lbl.configure(text=f"Error loading data: {e}", text_color=DANGER)

    def _apply_filters(self):
        query = self.search_var.get().strip().lower()
        for widget in self.scroll.winfo_children():
            widget.destroy()

        filtered = [r for r in self.inventory_data if query in str(r.get("product_name", "")).lower() or query in str(r.get("batch_no", "")).lower()]
        
        if not filtered:
            ctk.CTkLabel(self.scroll, text="No matches found.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        for row in filtered:
            f = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
            f.pack(fill="x", pady=1)
            f.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=5)

            cols = [
                (str(row.get("product_name", ""))[:20], 140, "w"),
                (str(row.get("batch_no", "")), 80, "w"),
                (str(row.get("supplier_name", "") or "N/A")[:15], 100, "w"),
                (row.get("expiry_date").strftime("%d/%m/%y") if hasattr(row.get("expiry_date"), "strftime") else str(row.get("expiry_date")), 80, "w"),
                (str(row.get("quantity", 0)), 40, "center"),
                (f"₹{float(row.get('mrp', 0)):.2f}", 65, "center"),
                (f"₹{float(row.get('selling_price', 0)):.2f}", 75, "center"),
                (f"{float(row.get('discount_percent', 0)):.1f}%", 50, "center")
            ]

            for val, w, anchor in cols:
                ctk.CTkLabel(f, text=val, width=w, font=ctk.CTkFont(size=10), text_color=TEXT_DARK, anchor=anchor).pack(side="left", padx=2)

            ctk.CTkButton(
                f, text="✏️ Edit", width=50, height=26, font=ctk.CTkFont(size=10),
                fg_color="#DBEAFE", hover_color="#BFDBFE", text_color="#1E3A8A",
                command=lambda r=row: self._start_edit(r)
            ).pack(side="left", padx=5)

    def _start_edit(self, row):
        self._clear_form()
        self.editing_batch_id = row.get("batch_id")
        self.form_title.configure(text="Update Medicine")
        self.mode_lbl.configure(text="Limited Edit Mode (Price Only)")
        self.save_btn.configure(text="Confirm Update", fg_color=WARNING, hover_color="#D97706")

        # Set Fields
        self.f_product.set(row.get("product_name", ""))
        self.f_batch.insert(0, row.get("batch_no", ""))
        self.f_supplier.set(row.get("supplier_name", ""))
        
        exp = row.get("expiry_date", "")
        if hasattr(exp, "strftime"): exp = exp.strftime("%Y-%m-%d")
        self.f_expiry.insert(0, str(exp))
        self.f_quantity.insert(0, str(row.get("quantity", "")))
        
        self.f_mrp.insert(0, str(row.get("mrp", "")))
        self.f_selling.insert(0, str(row.get("selling_price", "")))
        self.f_discount.insert(0, str(row.get("discount_percent", "")))

        # DISABLE LOCK FIELDS
        self.f_product.configure(state="disabled")
        self.f_batch.configure(state="disabled")
        self.f_supplier.configure(state="disabled")
        self.f_expiry.configure(state="disabled")
        self.f_quantity.configure(state="disabled")

        # Show tooltips next to rows (conceptual placement)
        # In a real app we might use a hover tooltip, here we just show the Lock icon or message
        messagebox.showinfo("Read Only Mode", "Field locking enabled: Use the Inventory module to update stock, batch details, or expiry dates.")

    def _clear_form(self):
        self.editing_batch_id = None
        self.form_title.configure(text="Add New Medicine")
        self.mode_lbl.configure(text="")
        self.save_btn.configure(text="Add Medicine", fg_color=SUCCESS, hover_color=SUCCESS_HOV)

        self.f_product.configure(state="normal")
        self.f_product.set("")
        self.f_batch.configure(state="normal")
        self.f_batch.delete(0, "end")
        self.f_supplier.configure(state="normal")
        self.f_supplier.set("")
        self.f_expiry.configure(state="normal")
        self.f_expiry.delete(0, "end")
        self.f_quantity.configure(state="normal")
        self.f_quantity.delete(0, "end")
        
        self.f_mrp.delete(0, "end")
        self.f_selling.delete(0, "end")
        self.f_discount.delete(0, "end")

    def _save_medicine(self):
        mrp_val = self.f_mrp.get().strip()
        sell_val = self.f_selling.get().strip()
        disc_val = self.f_discount.get().strip() or "0"

        if not mrp_val or not sell_val:
            messagebox.showwarning("Incomplete", "Price fields are required.")
            return

        try:
            mrp = float(mrp_val)
            sell = float(sell_val)
            disc = float(disc_val)
        except ValueError:
            messagebox.showerror("Invalid Data", "Check your price/discount values.")
            return

        # Validations
        if sell <= 0:
            messagebox.showwarning("Validation Error", "Selling Price must be greater than 0.")
            return
        if mrp < sell:
            messagebox.showwarning("Validation Error", "MRP cannot be less than Selling Price.")
            return

        if self.editing_batch_id:
            if not messagebox.askyesno("Confirm Update", 
                "Are you sure you want to update this medicine?\nOnly pricing changes will be saved."):
                return
            
            try:
                update_medicine_pricing(self.editing_batch_id, sell, mrp, disc)
                messagebox.showinfo("Success", "Medicine pricing updated successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update: {e}")
        else:
            if not messagebox.askyesno("Confirm Add", "Are you sure you want to add this new medicine?"):
                return
            
            # Full insert flow (logic from InventoryView for creation)
            p_name = self.f_product.get()
            b_no = self.f_batch.get()
            s_name = self.f_supplier.get()
            exp = self.f_expiry.get()
            qty = self.f_quantity.get()
            
            med_id = next((m["medicine_id"] for m in self.medicines if m["name"] == p_name), None)
            sup_id = next((s["supplier_id"] for s in self.suppliers if s["name"] == s_name), None)
            
            if not all([med_id, sup_id, b_no, exp, qty]):
                messagebox.showwarning("Missing Data", "All fields are required for new additions.")
                return
            
            try:
                query = """
                    INSERT INTO batches 
                    (medicine_id, supplier_id, distributor_id, batch_no, expiry_date, quantity, mrp, selling_price, discount_percent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                execute_query(query, (med_id, sup_id, self.user["distributor_id"], b_no, exp, int(qty), mrp, sell, disc))
                messagebox.showinfo("Success", "New medicine stock added successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add: {e}")

        self._clear_form()
        self.inventory_data = get_inventory_list(self.user["distributor_id"])
        self._apply_filters()

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children(): widget.destroy()
        Dashboard(self.master, self.user, self.app).pack(fill="both", expand=True)
