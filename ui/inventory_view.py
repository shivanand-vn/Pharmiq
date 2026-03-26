"""
Inventory View — CustomTkinter frame for managing and viewing inventory/stock.
Features a 2-column layout with table on left and inline Add/Update Stock form on right.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from models.product import get_inventory_list
from db.connection import execute_query, fetch_all

# ── Colour palette ──
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
    """View to list, search, and manage inventory batches inline."""

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

    # ──────────────────────────── UI BUILD ────────────────────────────

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=60, border_width=1, border_color=BORDER_CLR)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back to Dashboard", width=140, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            top, text="📦  Inventory Management",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Main 2-Column Split ──
        split_container = ctk.CTkFrame(self, fg_color="transparent")
        split_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Column (Table)
        self.left_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Right Column (Form)
        self.right_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR, width=370)
        self.right_col.pack(side="right", fill="y")
        self.right_col.pack_propagate(False)

        self._build_table_area()
        self._build_form_area()

    def _build_table_area(self):
        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self.left_col, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=15)

        # Search
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search medicine or batch...",
            width=220, height=38, font=ctk.CTkFont(size=12), corner_radius=8,
            fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK
        )
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        # Category Filter
        self.cat_var = ctk.StringVar(value="All Categories")
        self.cat_menu = ctk.CTkOptionMenu(
            toolbar, variable=self.cat_var, values=["All Categories"],
            width=140, height=38, corner_radius=8, fg_color=ENTRY_BG, text_color=TEXT_DARK,
            button_color=ACCENT, button_hover_color=ACCENT_HOVER, command=lambda _: self._apply_filters()
        )
        self.cat_menu.pack(side="left", padx=(0, 8))

        # Status Filter
        self.status_var = ctk.StringVar(value="All Status")
        status_menu = ctk.CTkOptionMenu(
            toolbar, variable=self.status_var,
            values=["All Status", "Low Stock (<50)", "Out of Stock", "Expiring Soon (<90 days)", "Expired"],
            width=170, height=38, corner_radius=8, fg_color=ENTRY_BG, text_color=TEXT_DARK,
            button_color=ACCENT, button_hover_color=ACCENT_HOVER, command=lambda _: self._apply_filters()
        )
        status_menu.pack(side="left", padx=(0, 8))

        # Header
        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("Product Name", 160), ("Batch No", 80), ("Category", 80),
            ("Supplier", 110), ("Expiry", 85), ("Qty", 50),
            ("Purchase", 70), ("MRP", 65), ("Status", 85), ("", 50)
        ]

        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text not in ["Qty", "Purchase", "MRP", "Status", ""] else "center"
            ).pack(side="left", padx=3)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        # Loading label
        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading inventory...", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.loading_lbl.pack(pady=40)

    def _build_form_area(self):
        # Title
        self.form_title = ctk.CTkLabel(
            self.right_col, text="Add Stock",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        self.form_title.pack(pady=(25, 15))

        # Scrollable form container
        form_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True)

        def add_field(parent, label_text, placeholder, required=True):
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
            return entry

        # Product Name — ComboBox
        prod_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        prod_row.pack(padx=20, pady=(4, 8), fill="x")
        lbl_r = ctk.CTkFrame(prod_row, fg_color="transparent")
        lbl_r.pack(fill="x", pady=(0, 3))
        ctk.CTkLabel(lbl_r, text="Product Name", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
        ctk.CTkLabel(lbl_r, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w", height=15).pack(side="left")
        self.f_product = ctk.CTkComboBox(
            prod_row, values=["Loading..."], height=38, font=ctk.CTkFont(size=12),
            fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
            corner_radius=6, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            command=self._on_product_selected
        )
        self.f_product.pack(fill="x")
        self.f_product.set("")

        self.f_batch = add_field(form_scroll, "Batch No", "e.g. B12345")
        self.f_category = add_field(form_scroll, "Category", "Auto-filled", required=False)
        self.f_category.configure(state="disabled")

        # Supplier — ComboBox
        sup_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        sup_row.pack(padx=20, pady=(4, 8), fill="x")
        lbl_s = ctk.CTkFrame(sup_row, fg_color="transparent")
        lbl_s.pack(fill="x", pady=(0, 3))
        ctk.CTkLabel(lbl_s, text="Supplier", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
        ctk.CTkLabel(lbl_s, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w", height=15).pack(side="left")
        self.f_supplier = ctk.CTkComboBox(
            sup_row, values=["Loading..."], height=38, font=ctk.CTkFont(size=12),
            fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
            corner_radius=6, button_color=ACCENT, button_hover_color=ACCENT_HOVER
        )
        self.f_supplier.pack(fill="x")
        self.f_supplier.set("")

        self.f_expiry = add_field(form_scroll, "Expiry Date", "YYYY-MM-DD")
        self.f_quantity = add_field(form_scroll, "Quantity", "e.g. 100")
        self.f_purchase = add_field(form_scroll, "Purchase Price (₹)", "e.g. 50.00")
        self.f_mrp = add_field(form_scroll, "MRP (₹)", "e.g. 75.00")

        # Buttons
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(18, 20))

        self.save_btn = ctk.CTkButton(
            btn_frame, text="Save Stock", height=40,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._save_stock
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.clear_btn = ctk.CTkButton(
            btn_frame, text="Clear", height=40,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._clear_form
        )
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ──────────────────────────── DATA ────────────────────────────

    def _load_data(self):
        try:
            self.inventory_data = get_inventory_list(self.user["distributor_id"])
            for row in self.inventory_data:
                cat = row.get("category")
                if cat:
                    self.categories.add(cat)

            # Update category menu
            cat_list = ["All Categories"] + sorted(list(self.categories))
            self.cat_menu.configure(values=cat_list)

            # Fetch medicines & suppliers for the form dropdowns
            self.medicines = fetch_all("SELECT medicine_id, name, unit FROM medicines ORDER BY name")
            self.suppliers = fetch_all(
                "SELECT supplier_id, name FROM suppliers WHERE distributor_id = %s ORDER BY name",
                (self.user["distributor_id"],)
            )

            med_names = [m["name"] for m in self.medicines] if self.medicines else ["No medicines found"]
            sup_names = [s["name"] for s in self.suppliers] if self.suppliers else ["No suppliers found"]
            self.f_product.configure(values=med_names)
            self.f_supplier.configure(values=sup_names)

            self._apply_filters()
        except Exception as e:
            self.loading_lbl.configure(text=f"Error loading data: {e}", text_color=DANGER)

    def _on_product_selected(self, selected_name):
        """Auto-fill category when a product is selected."""
        med = next((m for m in self.medicines if m["name"] == selected_name), None)
        if med:
            self.f_category.configure(state="normal")
            self.f_category.delete(0, "end")
            self.f_category.insert(0, med.get("unit", ""))
            self.f_category.configure(state="disabled")

    # ──────────────────────────── FILTERS & TABLE ────────────────────────────

    def _apply_filters(self):
        search_q = self.search_var.get().strip().lower()
        cat_filter = self.cat_var.get()
        status_filter = self.status_var.get()

        for widget in self.scroll.winfo_children():
            widget.destroy()

        filtered = []
        now = datetime.now()

        for row in self.inventory_data:
            name = str(row.get("product_name", "")).lower()
            batch = str(row.get("batch_no", "")).lower()
            if search_q and search_q not in name and search_q not in batch:
                continue

            if cat_filter != "All Categories" and row.get("category") != cat_filter:
                continue

            qty = int(row.get("quantity") or 0)
            exp_date = row.get("expiry_date")
            days_to_expiry = 9999
            if exp_date:
                try:
                    if hasattr(exp_date, "strftime"):
                        diff = exp_date - now.date()
                        days_to_expiry = diff.days
                except:
                    pass

            status_tags = []
            if qty <= 0:
                status_tags.append("Out of Stock")
            elif qty < 50:
                status_tags.append("Low Stock")

            if days_to_expiry < 0:
                status_tags.append("Expired")
            elif days_to_expiry < 90:
                status_tags.append("Expiring Soon")

            row["_computed_status"] = status_tags

            if status_filter == "Low Stock (<50)" and ("Low Stock" not in status_tags and "Out of Stock" not in status_tags):
                continue
            if status_filter == "Out of Stock" and "Out of Stock" not in status_tags:
                continue
            if status_filter == "Expiring Soon (<90 days)" and "Expiring Soon" not in status_tags:
                continue
            if status_filter == "Expired" and "Expired" not in status_tags:
                continue

            filtered.append(row)

        if not filtered:
            ctk.CTkLabel(self.scroll, text="No inventory items found matching filters.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        cols = [
            ("product_name", 160, "w"), ("batch_no", 80, "w"), ("category", 80, "w"),
            ("supplier_name", 110, "w"), ("expiry_date", 85, "w"), ("quantity", 50, "center"),
            ("purchase_price", 70, "center"), ("mrp", 65, "center")
        ]

        for i, row in enumerate(filtered):
            qty_color = TEXT_DARK
            qty_weight = "normal"
            if "Out of Stock" in row["_computed_status"]:
                qty_color = DANGER
                qty_weight = "bold"
            elif "Low Stock" in row["_computed_status"]:
                qty_color = WARNING
                qty_weight = "bold"

            exp_color = TEXT_DARK
            exp_weight = "normal"
            if "Expired" in row["_computed_status"]:
                exp_color = DANGER
                exp_weight = "bold"
            elif "Expiring Soon" in row["_computed_status"]:
                exp_color = WARNING
                exp_weight = "bold"

            frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=42)
            frame.pack(fill="x", pady=1)
            frame.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=5)

            for key, w, align in cols:
                val = row.get(key, "")
                t_color = TEXT_DARK
                t_weight = "normal"

                if key == "quantity":
                    t_color = qty_color
                    t_weight = qty_weight
                    val = f"{val}"
                elif key == "expiry_date":
                    t_color = exp_color
                    t_weight = exp_weight
                    if hasattr(val, "strftime"):
                        val = val.strftime("%d/%m/%Y")
                elif key in ["purchase_price", "mrp"]:
                    val = f"₹{float(val or 0):.2f}"
                elif key == "product_name":
                    val = str(val)[:22]
                elif key == "supplier_name":
                    val = str(val)[:18] if val else "N/A"

                ctk.CTkLabel(
                    frame, text=str(val), width=w, font=ctk.CTkFont(size=11, weight=t_weight),
                    text_color=t_color, anchor=align
                ).pack(side="left", padx=3)

            # Status pill
            status = "OK"
            s_bg = "#D1FAE5"
            s_fg = "#065F46"
            if row["_computed_status"]:
                status = row["_computed_status"][0][:12]
                if "Out" in status or "Exp" in status:
                    s_bg = "#FEE2E2"
                    s_fg = "#991B1B"
                else:
                    s_bg = "#FEF3C7"
                    s_fg = "#92400E"

            status_frame = ctk.CTkFrame(frame, fg_color=s_bg, corner_radius=10, width=85, height=22)
            status_frame.pack_propagate(False)
            status_frame.pack(side="left", padx=3, pady=8)
            ctk.CTkLabel(status_frame, text=status, font=ctk.CTkFont(size=9, weight="bold"), text_color=s_fg).pack(expand=True)

            # Edit button
            ctk.CTkButton(
                frame, text="✏️", width=40, height=26,
                font=ctk.CTkFont(size=12), corner_radius=6,
                fg_color="#DBEAFE", hover_color="#BFDBFE", text_color="#1E3A8A",
                command=lambda r=row: self._start_edit(r)
            ).pack(side="left", padx=(3, 5), pady=8)

    # ──────────────────────────── FORM LOGIC ────────────────────────────

    def _start_edit(self, row):
        """Load a row's data into the form for editing."""
        self._clear_form()
        self.editing_batch_id = row.get("batch_id")
        self.form_title.configure(text="Update Stock")
        self.save_btn.configure(text="Update Stock")

        # Populate fields
        self.f_product.set(row.get("product_name", ""))
        self._on_product_selected(row.get("product_name", ""))
        self.f_batch.insert(0, row.get("batch_no", ""))

        sup_name = row.get("supplier_name", "")
        if sup_name:
            self.f_supplier.set(sup_name)

        exp = row.get("expiry_date", "")
        if hasattr(exp, "strftime"):
            exp = exp.strftime("%Y-%m-%d")
        self.f_expiry.insert(0, str(exp))
        self.f_quantity.insert(0, str(row.get("quantity", "")))
        self.f_purchase.insert(0, str(row.get("purchase_price", "")))
        self.f_mrp.insert(0, str(row.get("mrp", "")))

    def _clear_form(self):
        """Reset all form fields."""
        self.editing_batch_id = None
        self.form_title.configure(text="Add Stock")
        self.save_btn.configure(text="Save Stock")

        self.f_product.set("")
        self.f_batch.delete(0, "end")
        self.f_category.configure(state="normal")
        self.f_category.delete(0, "end")
        self.f_category.configure(state="disabled")
        self.f_supplier.set("")
        self.f_expiry.delete(0, "end")
        self.f_quantity.delete(0, "end")
        self.f_purchase.delete(0, "end")
        self.f_mrp.delete(0, "end")

    def _save_stock(self):
        """Save or update a stock entry."""
        med_name = self.f_product.get().strip()
        sup_name = self.f_supplier.get().strip()
        batch_no = self.f_batch.get().strip()
        expiry_date = self.f_expiry.get().strip()
        qty = self.f_quantity.get().strip()
        pur_price = self.f_purchase.get().strip()
        mrp = self.f_mrp.get().strip()

        # Resolve IDs
        med_id = next((m["medicine_id"] for m in self.medicines if m["name"] == med_name), None)
        sup_id = next((s["supplier_id"] for s in self.suppliers if s["name"] == sup_name), None)

        if not all([med_id, sup_id, batch_no, expiry_date, qty, pur_price, mrp]):
            messagebox.showwarning("Incomplete", "Please fill in all the required fields (marked with *).")
            return

        try:
            qty = int(qty)
            pur_price = float(pur_price)
            mrp = float(mrp)
            datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError as ve:
            messagebox.showerror("Invalid Data", f"Please check inputs (Date: YYYY-MM-DD, numbers for qty/prices).\n\n{ve}")
            return

        try:
            if self.editing_batch_id:
                query = """
                    UPDATE batches
                    SET medicine_id = %s, supplier_id = %s, batch_no = %s, expiry_date = %s,
                        quantity = %s, purchase_price = %s, mrp = %s
                    WHERE batch_id = %s
                """
                execute_query(query, (med_id, sup_id, batch_no, expiry_date, qty, pur_price, mrp, self.editing_batch_id))
                messagebox.showinfo("Success", "Stock updated successfully!")
            else:
                query = """
                    INSERT INTO batches
                    (medicine_id, supplier_id, distributor_id, batch_no, expiry_date, quantity, purchase_price, mrp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                execute_query(query, (med_id, sup_id, self.user["distributor_id"], batch_no, expiry_date, qty, pur_price, mrp))
                messagebox.showinfo("Success", "Stock added successfully!")

            self._clear_form()
            # Reload inventory data from DB
            self.inventory_data = get_inventory_list(self.user["distributor_id"])
            self._apply_filters()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save stock:\n{e}")

    # ──────────────────────────── NAVIGATION ────────────────────────────

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
