"""
Medicine View — Specialized module for managing medicine definitions and pricing.
Restricted to pricing and basic details to ensure strict separation from Inventory.
"""

import customtkinter as ctk
from tkinter import messagebox
from models.product import update_medicine_pricing
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
    """View to manage medicine definitions with pricing-only focus."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self.medicine_data = []
        self.editing_medicine_id = None

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
            top, text="💊  Medicine Definitions",
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
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search medicine definition...",
            width=300, height=38, font=ctk.CTkFont(size=12), corner_radius=8,
            fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK
        )
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        # Header
        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("Medicine Name", 220), ("Unit", 80), ("MRP", 80), ("Sell Price", 80), ("Disc%", 60), ("", 50)
        ]

        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text == "Medicine Name" else "center"
            ).pack(side="left", padx=3)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading medicines...", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.loading_lbl.pack(pady=40)

    def _build_form_area(self):
        self.form_title = ctk.CTkLabel(
            self.right_col, text="Add New Medicine",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        self.form_title.pack(pady=(25, 20))

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

        self.f_name = add_field(form_scroll, "Medicine Name", "e.g. Paracetamol 500mg")
        self.f_unit = add_field(form_scroll, "Unit/Pack", "e.g. 10x10 Tablets")
        
        ctk.CTkFrame(form_scroll, fg_color=BORDER_CLR, height=2).pack(fill="x", padx=20, pady=15)
        
        self.f_mrp = add_field(form_scroll, "MRP (₹)", "Maximum Retail Price")
        self.f_selling = add_field(form_scroll, "Selling Price (₹)", "Distributor Selling Price")
        self.f_discount = add_field(form_scroll, "Default Discount (%)", "e.g. 10.0", required=False)

        self.f_mrp.bind("<KeyRelease>", self._validate_prices)
        self.f_selling.bind("<KeyRelease>", self._validate_prices)

        ctk.CTkFrame(form_scroll, fg_color=BORDER_CLR, height=2).pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(form_scroll, text="Inventory / Stock Information", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(anchor="w", padx=20, pady=(0, 5))

        def add_dummy_field(parent, label_text, tooltip):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=20, pady=(4, 8), fill="x")
            ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED, anchor="w", height=15).pack(anchor="w")
            entry = ctk.CTkEntry(
                row, placeholder_text="Managed in Inventory", height=38, font=ctk.CTkFont(size=12, slant="italic"),
                fg_color="#F3F4F6", border_color=BORDER_CLR, border_width=1, text_color=TEXT_MUTED, corner_radius=6, state="disabled"
            )
            entry.pack(fill="x")
            ctk.CTkLabel(row, text=tooltip, font=ctk.CTkFont(size=10, slant="italic"), text_color="#9CA3AF", height=12).pack(anchor="w", pady=(2, 0))

        add_dummy_field(form_scroll, "Batch Number", "This field cannot be edited. Use Inventory module for stock updates.")
        add_dummy_field(form_scroll, "Quantity", "This field cannot be edited. Use Inventory module for stock updates.")
        add_dummy_field(form_scroll, "Expiry Date", "This field cannot be edited. Use Inventory module for stock updates.")
        add_dummy_field(form_scroll, "Manufacturer", "This field cannot be edited. Use suppliers tracking.")

        # Buttons
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")

        btn_frame.pack(fill="x", padx=20, pady=(20, 20))

        self.save_btn = ctk.CTkButton(
            btn_frame, text="Save Medicine", height=42,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._save_medicine
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.clear_btn = ctk.CTkButton(
            btn_frame, text="Clear", height=42,
            font=ctk.CTkFont(size=13), corner_radius=10,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._clear_form
        )
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(form_scroll, text="Stock must be added via Inventory Module", font=ctk.CTkFont(size=10, slant="italic"), text_color=TEXT_MUTED).pack(pady=10)

    def _validate_prices(self, event=None):
        mrp_text = self.f_mrp.get().strip()
        sell_text = self.f_selling.get().strip()
        
        try:
            mrp_val = float(mrp_text) if mrp_text else -1
        except ValueError:
            mrp_val = -1
            
        try:
            sell_val = float(sell_text) if sell_text else -1
        except ValueError:
            sell_val = -1

        # Check sell price
        if sell_val > 0:
            self.f_selling.configure(border_color=SUCCESS)
        elif sell_text:
            self.f_selling.configure(border_color=DANGER)
        else:
            self.f_selling.configure(border_color=BORDER_CLR)
            
        # Check mrp
        if mrp_val >= 0 and sell_val > 0 and mrp_val >= sell_val:
            self.f_mrp.configure(border_color=SUCCESS)
        elif mrp_text:
            self.f_mrp.configure(border_color=DANGER)
        else:
            self.f_mrp.configure(border_color=BORDER_CLR)

    def _load_data(self):
        try:
            self.medicine_data = fetch_all("SELECT * FROM medicines ORDER BY name")
            self._apply_filters()
        except Exception as e:
            self.loading_lbl.configure(text=f"Error loading: {e}", text_color=DANGER)

    def _apply_filters(self):
        query = self.search_var.get().strip().lower()
        for widget in self.scroll.winfo_children(): widget.destroy()

        filtered = [r for r in self.medicine_data if query in str(r.get("name", "")).lower()]
        
        if not filtered:
            ctk.CTkLabel(self.scroll, text="No medicines found.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        for row in filtered:
            f = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
            f.pack(fill="x", pady=1)
            f.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=5)

            cols = [
                (str(row.get("name", ""))[:32], 220, "w"),
                (str(row.get("unit", "N/A")), 80, "center"),
                (f"₹{float(row.get('mrp', 0)):.2f}", 80, "center"),
                (f"₹{float(row.get('selling_price', 0)):.2f}", 80, "center"),
                (f"{float(row.get('discount_percent', 0)):.1f}%", 60, "center")
            ]

            for val, w, anchor in cols:
                ctk.CTkLabel(f, text=val, width=w, font=ctk.CTkFont(size=11), text_color=TEXT_DARK, anchor=anchor).pack(side="left", padx=3)

            ctk.CTkButton(
                f, text="✎", width=40, height=26, font=ctk.CTkFont(size=12),
                fg_color="#DBEAFE", hover_color="#BFDBFE", text_color="#1E3A8A",
                command=lambda r=row: self._start_edit(r)
            ).pack(side="left", padx=5)

    def _start_edit(self, row):
        self._clear_form()
        self.editing_medicine_id = row["medicine_id"]
        self.form_title.configure(text="Edit Pricing")
        self.save_btn.configure(text="Update Medicine", fg_color=WARNING)

        self.f_name.insert(0, row["name"])
        self.f_unit.insert(0, row.get("unit") or "")
        
        self.f_name.configure(state="disabled", fg_color="#F3F4F6", text_color=TEXT_MUTED)
        self.f_unit.configure(state="disabled", fg_color="#F3F4F6", text_color=TEXT_MUTED)

        self.f_mrp.insert(0, str(row.get("mrp", "")))
        self.f_selling.insert(0, str(row.get("selling_price", "")))
        self.f_discount.insert(0, str(row.get("discount_percent", "")))
        self._validate_prices()

    def _clear_form(self):
        self.editing_medicine_id = None
        self.form_title.configure(text="Add New Medicine")
        self.save_btn.configure(text="Save Medicine", fg_color=SUCCESS)
        
        self.f_name.configure(state="normal", fg_color=ENTRY_BG, text_color=TEXT_DARK)
        self.f_unit.configure(state="normal", fg_color=ENTRY_BG, text_color=TEXT_DARK)
        self.f_mrp.configure(border_color=BORDER_CLR)
        self.f_selling.configure(border_color=BORDER_CLR)
        
        self.f_name.delete(0, "end")
        self.f_unit.delete(0, "end")
        self.f_mrp.delete(0, "end")
        self.f_selling.delete(0, "end")
        self.f_discount.delete(0, "end")

    def _save_medicine(self):
        name = self.f_name.get().strip()
        unit = self.f_unit.get().strip()
        mrp = self.f_mrp.get().strip()
        sell = self.f_selling.get().strip()
        disc = self.f_discount.get().strip() or "0"

        if not name or not mrp or not sell:
            messagebox.showwarning("Incomplete", "Name and Price fields are required.")
            return

        try:
            mrp_val = float(mrp)
            sell_val = float(sell)
            disc_val = float(disc)
            if sell_val <= 0 or mrp_val < sell_val:
                raise ValueError("Price validation failed")
        except ValueError:
            messagebox.showerror("Invalid Data", "Check your prices. (Sell > 0 and MRP >= Sell)")
            return

        if self.editing_medicine_id:
            if not messagebox.askyesno("Confirm Update", "Are you sure you want to update this medicine? Only pricing changes will be saved."):
                return
            try:
                update_medicine_pricing(self.editing_medicine_id, sell_val, mrp_val, disc_val)
                # We skip updating name and unit since they are disabled in edit mode
                messagebox.showinfo("Success", "Medicine definition updated.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")
        else:
            if not messagebox.askyesno("Confirm Adding", "Are you sure you want to add this new medicine?"):
                return
            try:
                execute_query(
                    "INSERT INTO medicines (name, unit, mrp, selling_price, discount_percent) VALUES (%s, %s, %s, %s, %s)",
                    (name, unit, mrp_val, sell_val, disc_val)
                )
                messagebox.showinfo("Success", "New medicine defined.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

        self._clear_form()
        self._load_data()

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children(): widget.destroy()
        Dashboard(self.master, self.user, self.app).pack(fill="both", expand=True)
