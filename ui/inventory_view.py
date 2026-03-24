"""
Inventory View — CustomTkinter frame for managing and viewing inventory/stock.
Features search, filtering, and highlight logic for low stock and near expiry.
"""

import customtkinter as ctk
from datetime import datetime
from models.product import get_inventory_list

# ── Colour palette ──
BG_DARK = "#F8F9FA"
CARD_BG = "#212529"
ROW_BG_1 = "#212529"
ROW_BG_2 = "#F1F3F5"
BORDER_CLR = "#DEE2E6"
ACCENT = "#4361EE"
ACCENT_HOVER = "#3A0CA3"
TEXT_WHITE = "#212529"
TEXT_MUTED = "#868E96"
ENTRY_BG = "#FFFFFF"
SUCCESS = "#2DC653"
WARNING = "#F59E0B"
DANGER = "#EF233C"


class InventoryView(ctk.CTkFrame):
    """View to list, search, and filter all inventory batches."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref
        
        self.inventory_data = [] # Full raw data
        self.categories = set()

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#212529", corner_radius=0, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=80, height=30,
            font=ctk.CTkFont(size=11), corner_radius=8,
            fg_color="#E9ECEF", hover_color="#CED4DA", text_color="#212529",
            command=self._go_back,
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top, text="📦  Inventory Management",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(15, 5))

        # Search
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search medicine or batch...",
            width=250, height=35, corner_radius=8, fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE
        )
        search_entry.pack(side="left", padx=(0, 10))
        search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        # Category Filter
        self.cat_var = ctk.StringVar(value="All Categories")
        self.cat_menu = ctk.CTkOptionMenu(
            toolbar, variable=self.cat_var, values=["All Categories"],
            width=150, height=35, corner_radius=8, fg_color=ENTRY_BG, text_color=TEXT_WHITE,
            button_color=ACCENT, button_hover_color=ACCENT_HOVER, command=lambda _: self._apply_filters()
        )
        self.cat_menu.pack(side="left", padx=(0, 10))

        # Status Filter
        self.status_var = ctk.StringVar(value="All Status")
        status_menu = ctk.CTkOptionMenu(
            toolbar, variable=self.status_var, 
            values=["All Status", "Low Stock (<50)", "Out of Stock", "Expiring Soon (<90 days)", "Expired"],
            width=180, height=35, corner_radius=8, fg_color=ENTRY_BG, text_color=TEXT_WHITE,
            button_color=ACCENT, button_hover_color=ACCENT_HOVER, command=lambda _: self._apply_filters()
        )
        status_menu.pack(side="left", padx=(0, 10))

        # Add Stock Button
        ctk.CTkButton(
            toolbar, text="+ Add Stock", height=35, font=ctk.CTkFont(size=12, weight="bold"), 
            corner_radius=8, fg_color=SUCCESS, hover_color="#208B3A", text_color="#FFFFFF",
            command=self._add_stock
        ).pack(side="right")

        # ── Table Area ──
        table_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color=BORDER_CLR)
        table_container.pack(fill="both", expand=True, padx=15, pady=(10, 20))

        # Header
        header = ctk.CTkFrame(table_container, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        cols = [
            ("Product Name", 200), ("Batch No", 100), ("Category", 100), 
            ("Supplier", 150), ("Expiry", 100), ("Qty", 70), 
            ("Purchase", 80), ("MRP", 80), ("Status", 120)
        ]
        
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#4B5563", anchor="w" if text not in ["Qty", "Purchase", "MRP", "Status"] else "center"
            ).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Loading label
        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading inventory...", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.loading_lbl.pack(pady=40)

    def _load_data(self):
        # In a real app with huge data, this might run in a thread.
        try:
            self.inventory_data = get_inventory_list(self.user["distributor_id"])
            for row in self.inventory_data:
                cat = row.get("category")
                if cat: self.categories.add(cat)
                
            # Update category menu
            cat_list = ["All Categories"] + sorted(list(self.categories))
            self.cat_menu.configure(values=cat_list)
            
            self._apply_filters()
        except Exception as e:
            self.loading_lbl.configure(text=f"Error loading data: {e}", text_color=DANGER)

    def _apply_filters(self):
        search_q = self.search_var.get().strip().lower()
        cat_filter = self.cat_var.get()
        status_filter = self.status_var.get()

        for widget in self.scroll.winfo_children():
            widget.destroy()

        filtered = []
        now = datetime.now()

        for row in self.inventory_data:
            # Match search
            name = str(row.get("product_name", "")).lower()
            batch = str(row.get("batch_no", "")).lower()
            if search_q and search_q not in name and search_q not in batch:
                continue
                
            # Match category
            if cat_filter != "All Categories" and row.get("category") != cat_filter:
                continue
                
            # Calculate dynamic status
            qty = int(row.get("quantity") or 0)
            
            exp_date = row.get("expiry_date")
            days_to_expiry = 9999
            if exp_date:
                try:
                    if hasattr(exp_date, "strftime"):
                         diff = exp_date - now.date()
                         days_to_expiry = diff.days
                except: pass

            status_tags = []
            if qty <= 0: status_tags.append("Out of Stock")
            elif qty < 50: status_tags.append("Low Stock")
            
            if days_to_expiry < 0: status_tags.append("Expired")
            elif days_to_expiry < 90: status_tags.append("Expiring Soon")

            row["_computed_status"] = status_tags
            
            # Match Status
            if status_filter == "Low Stock (<50)" and ("Low Stock" not in status_tags and "Out of Stock" not in status_tags): continue
            if status_filter == "Out of Stock" and "Out of Stock" not in status_tags: continue
            if status_filter == "Expiring Soon (<90 days)" and "Expiring Soon" not in status_tags: continue
            if status_filter == "Expired" and "Expired" not in status_tags: continue

            filtered.append(row)

        if not filtered:
            ctk.CTkLabel(self.scroll, text="No inventory items found matching filters.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        cols = [
            ("product_name", 200, "w"), ("batch_no", 100, "w"), ("category", 100, "w"), 
            ("supplier_name", 150, "w"), ("expiry_date", 100, "w"), ("quantity", 70, "center"), 
            ("purchase_price", 80, "center"), ("mrp", 80, "center")
        ]

        for i, row in enumerate(filtered):
            # Styling based on highlight logic
            qty_color = TEXT_WHITE
            qty_weight = "normal"
            if "Out of Stock" in row["_computed_status"]:
                qty_color = DANGER
                qty_weight = "bold"
            elif "Low Stock" in row["_computed_status"]:
                qty_color = WARNING
                qty_weight = "bold"
                
            exp_color = TEXT_WHITE
            exp_weight = "normal"
            if "Expired" in row["_computed_status"]:
                exp_color = DANGER
                exp_weight = "bold"
            elif "Expiring Soon" in row["_computed_status"]:
                exp_color = WARNING
                exp_weight = "bold"

            frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
            frame.pack(fill="x", pady=2)
            frame.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color="#F3F4F6", height=1).pack(fill="x", padx=10)

            for key, w, align in cols:
                val = row.get(key, "")
                t_color = TEXT_WHITE
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
                    val = str(val)[:25]
                elif key == "supplier_name":
                    val = str(val)[:20] if val else "N/A"

                ctk.CTkLabel(
                    frame, text=str(val), width=w, font=ctk.CTkFont(size=12, weight=t_weight),
                    text_color=t_color, anchor=align
                ).pack(side="left", padx=5)

            # Status pill
            status = "OK"
            s_bg = "#D1FAE5"
            s_fg = "#065F46"
            if row["_computed_status"]:
                status = row["_computed_status"][0][:12] # First most critical
                if "Out" in status or "Exp" in status:
                    s_bg = "#FEE2E2"
                    s_fg = "#991B1B"
                else:
                    s_bg = "#FEF3C7"
                    s_fg = "#92400E"

            status_frame = ctk.CTkFrame(frame, fg_color=s_bg, corner_radius=10, width=100, height=24)
            status_frame.pack_propagate(False)
            status_frame.pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(status_frame, text=status, font=ctk.CTkFont(size=10, weight="bold"), text_color=s_fg).pack(expand=True)

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
        
    def _add_stock(self):
        from ui.add_stock_form import AddStockForm
        for widget in self.master.winfo_children():
            widget.destroy()
        form = AddStockForm(self.master, self.user, self.app)
        form.pack(fill="both", expand=True)
