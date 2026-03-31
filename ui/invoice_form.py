"""
Invoice Form — CustomTkinter form for creating new invoices.
Dynamic product rows, customer selection, live calculations.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date

from models.customer import search_customers, get_customer_by_license
from models.product import search_products, get_batch_by_id
from models.invoice import get_next_order_no
from services.invoice_service import calculate_item_amount, calculate_invoice_totals, create_full_invoice
from services.pdf_generator import generate_invoice_pdf, open_pdf
from models.distributor import get_distributor_by_id


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
ENTRY_BG = "#F8F9FA"
SUCCESS = "#2DC653"
DANGER = "#EF233C"


class InvoiceForm(ctk.CTkFrame):
    """Invoice creation form with dynamic product rows and live totals."""

    def __init__(self, master, user_context, distributor, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.distributor = distributor
        self.app = app_ref
        self.product_rows = []  # list of dicts holding row widgets + data
        self.selected_customer = None

        self._build_ui()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#212529", corner_radius=0, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=80, height=30,
            font=ctk.CTkFont(size=11), corner_radius=8,
            fg_color="#E9ECEF", hover_color="#CED4DA",
            command=self._go_back,
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top, text="📝  Create New Invoice",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Scrollable main content ──
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_header_section()
        self._build_customer_section()
        self._build_product_section()
        self._build_totals_section()
        self._build_action_buttons()

        # Add initial empty row
        self._add_product_row()

    # ══════════════════════════════════════════════════
    # HEADER: Invoice meta fields
    # ══════════════════════════════════════════════════
    def _build_header_section(self):
        frame = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=12,
                              border_width=1, border_color=BORDER_CLR)
        frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(frame, text="Invoice Details", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=TEXT_WHITE).pack(anchor="w", padx=12, pady=(10, 5))

        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=3)

        # Invoice Date
        ctk.CTkLabel(row1, text="Invoice Date:", font=ctk.CTkFont(size=11),
                      text_color=TEXT_MUTED).pack(side="left")
        self.date_entry = ctk.CTkEntry(row1, width=120, height=30, font=ctk.CTkFont(size=11),
                                        fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        self.date_entry.pack(side="left", padx=(5, 15))
        self.date_entry.insert(0, date.today().strftime("%d/%m/%Y"))

        # Order No
        ctk.CTkLabel(row1, text="Order No:", font=ctk.CTkFont(size=11),
                      text_color=TEXT_MUTED).pack(side="left")
        self.order_entry = ctk.CTkEntry(row1, width=120, height=30, font=ctk.CTkFont(size=11),
                                         fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        self.order_entry.pack(side="left", padx=(5, 15))
        
        # Pre-fill Order No
        try:
            next_order = get_next_order_no(self.user["distributor_id"])
            self.order_entry.insert(0, next_order)
        except Exception:
            self.order_entry.insert(0, "1")

        # LR No
        ctk.CTkLabel(row1, text="L.R No:", font=ctk.CTkFont(size=11),
                      text_color=TEXT_MUTED).pack(side="left")
        self.lr_entry = ctk.CTkEntry(row1, width=120, height=30, font=ctk.CTkFont(size=11),
                                      fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        self.lr_entry.pack(side="left", padx=(5, 15))

        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(3, 10))

        # Transport
        ctk.CTkLabel(row2, text="Transport:", font=ctk.CTkFont(size=11),
                      text_color=TEXT_MUTED).pack(side="left")
        self.transport_entry = ctk.CTkEntry(row2, width=180, height=30, font=ctk.CTkFont(size=11),
                                             fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        self.transport_entry.pack(side="left", padx=(5, 15))

        # Payment Type
        ctk.CTkLabel(row2, text="Payment:", font=ctk.CTkFont(size=11),
                      text_color=TEXT_MUTED).pack(side="left")
        self.payment_var = ctk.StringVar(value="Credit")
        self.payment_menu = ctk.CTkOptionMenu(
            row2, values=["Credit", "Cash"], variable=self.payment_var,
            width=120, height=30, font=ctk.CTkFont(size=11),
            fg_color=ENTRY_BG, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
        )
        self.payment_menu.pack(side="left", padx=5)

    # ══════════════════════════════════════════════════
    # CUSTOMER SECTION
    # ══════════════════════════════════════════════════
    def _build_customer_section(self):
        frame = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=12,
                              border_width=1, border_color=BORDER_CLR)
        frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(frame, text="Customer (Party) Details", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=TEXT_WHITE).pack(anchor="w", padx=12, pady=(10, 5))

        search_row = ctk.CTkFrame(frame, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=3)

        ctk.CTkLabel(search_row, text="Search:", font=ctk.CTkFont(size=11),
                      text_color=TEXT_MUTED).pack(side="left")
        self.cust_search = ctk.CTkEntry(search_row, width=250, height=30, font=ctk.CTkFont(size=11),
                                         placeholder_text="Type customer name or license...",
                                         fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        self.cust_search.pack(side="left", padx=5)
        self.cust_search.bind("<KeyRelease>", self._on_customer_search)

        self.cust_dropdown = ctk.CTkOptionMenu(
            search_row, values=["-- Select Customer --"], width=300, height=30,
            font=ctk.CTkFont(size=11),
            fg_color=ENTRY_BG, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            command=self._on_customer_selected,
        )
        self.cust_dropdown.pack(side="left", padx=5)

        # Customer details display
        self.cust_details_frame = ctk.CTkFrame(frame, fg_color=ROW_BG_1, corner_radius=8)
        self.cust_details_frame.pack(fill="x", padx=12, pady=(5, 10))

        self.cust_name_lbl = ctk.CTkLabel(self.cust_details_frame, text="No customer selected",
                                            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.cust_name_lbl.pack(anchor="w", padx=10, pady=5)
        self.cust_info_lbl = ctk.CTkLabel(self.cust_details_frame, text="",
                                            font=ctk.CTkFont(size=10), text_color=TEXT_MUTED, justify="left")
        self.cust_info_lbl.pack(anchor="w", padx=10, pady=(0, 5))

        # Populate initial customer list
        self._load_customers()

    def _load_customers(self, query=""):
        try:
            customers = search_customers(self.user["distributor_id"], query)
        except Exception:
            customers = []

        self._customer_list = customers
        names = [f"{c['shop_name']} ({c['license_no']})" for c in customers]
        if not names:
            names = ["-- No customers found --"]
        self.cust_dropdown.configure(values=names)
        if names:
            self.cust_dropdown.set(names[0])

    def _on_customer_search(self, event=None):
        query = self.cust_search.get().strip()
        self._load_customers(query)

    def _on_customer_selected(self, choice):
        # Find matching customer
        for c in self._customer_list:
            label = f"{c['shop_name']} ({c['license_no']})"
            if label == choice:
                self.selected_customer = c
                self.cust_name_lbl.configure(
                    text=f"🏪 {c['shop_name']}  —  {c['license_holder_name']}",
                    text_color=TEXT_WHITE,
                )
                info = f"📍 {c.get('address', 'N/A')}\n📞 {c.get('mobile_no', 'N/A')}    GSTIN: {c.get('gst_no', 'N/A')}    Licence: {c['license_no']}"
                self.cust_info_lbl.configure(text=info)
                return

    # ══════════════════════════════════════════════════
    # PRODUCT TABLE
    # ══════════════════════════════════════════════════
    def _build_product_section(self):
        frame = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=12,
                              border_width=1, border_color=BORDER_CLR)
        frame.pack(fill="x", pady=(0, 8))

        header_row = ctk.CTkFrame(frame, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(10, 5))

        ctk.CTkLabel(header_row, text="Products", font=ctk.CTkFont(size=13, weight="bold"),
                      text_color=TEXT_WHITE).pack(side="left")

        ctk.CTkButton(
            header_row, text="+ Add Row", width=90, height=28,
            font=ctk.CTkFont(size=11, weight="bold"), corner_radius=8,
            fg_color=SUCCESS, hover_color="#208B3A",
            command=self._add_product_row,
        ).pack(side="right")

        # Column headers
        col_header = ctk.CTkFrame(frame, fg_color=ROW_BG_1, corner_radius=6, height=30)
        col_header.pack(fill="x", padx=12, pady=(0, 3))
        col_header.pack_propagate(False)

        col_names = ["#", "Product Name", "Batch", "Expiry", "Qty", "MRP", "Rate", "Disc%", "GST%", "Amount", ""]
        col_widths = [30, 180, 80, 70, 55, 70, 70, 55, 50, 80, 35]
        for name, w in zip(col_names, col_widths):
            ctk.CTkLabel(
                col_header, text=name, width=w,
                font=ctk.CTkFont(size=9, weight="bold"), text_color="#495057",
            ).pack(side="left", padx=1)

        # Product rows container
        self.products_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.products_frame.pack(fill="x", padx=12, pady=(0, 10))

    def _add_product_row(self):
        """Add a new dynamic product row."""
        idx = len(self.product_rows)
        bg = ROW_BG_1 if idx % 2 == 0 else ROW_BG_2

        row_frame = ctk.CTkFrame(self.products_frame, fg_color=bg, corner_radius=6, height=35)
        row_frame.pack(fill="x", pady=1)
        row_frame.pack_propagate(False)

        row_data = {"frame": row_frame, "batch_id": None}

        # Serial number
        ctk.CTkLabel(row_frame, text=str(idx + 1), width=30,
                      font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(side="left", padx=1)

        # Product search (combobox-like)
        prod_entry = ctk.CTkEntry(row_frame, width=180, height=28, font=ctk.CTkFont(size=10),
                                   placeholder_text="Type to search...",
                                   fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        prod_entry.pack(side="left", padx=1)
        row_data["product_entry"] = prod_entry

        # When user types, show search results via popup
        prod_entry.bind("<KeyRelease>", lambda e, rd=row_data: self._on_product_search(e, rd))

        # Batch (auto-filled)
        batch_lbl = ctk.CTkLabel(row_frame, text="", width=80,
                                  font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)
        batch_lbl.pack(side="left", padx=1)
        row_data["batch_lbl"] = batch_lbl

        # Expiry (auto-filled)
        exp_lbl = ctk.CTkLabel(row_frame, text="", width=70,
                                font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)
        exp_lbl.pack(side="left", padx=1)
        row_data["exp_lbl"] = exp_lbl

        # Qty
        qty_entry = ctk.CTkEntry(row_frame, width=55, height=28, font=ctk.CTkFont(size=10),
                                  fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        qty_entry.pack(side="left", padx=1)
        qty_entry.insert(0, "1")
        qty_entry.bind("<KeyRelease>", lambda e: self._recalculate_row(row_data))
        row_data["qty_entry"] = qty_entry

        # MRP (auto-filled)
        mrp_lbl = ctk.CTkLabel(row_frame, text="0.00", width=70,
                                font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)
        mrp_lbl.pack(side="left", padx=1)
        row_data["mrp_lbl"] = mrp_lbl

        # Rate
        rate_entry = ctk.CTkEntry(row_frame, width=70, height=28, font=ctk.CTkFont(size=10),
                                   fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        rate_entry.pack(side="left", padx=1)
        rate_entry.insert(0, "0.00")
        rate_entry.bind("<KeyRelease>", lambda e: self._recalculate_row(row_data))
        row_data["rate_entry"] = rate_entry

        # Discount %
        disc_entry = ctk.CTkEntry(row_frame, width=55, height=28, font=ctk.CTkFont(size=10),
                                   fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE)
        disc_entry.pack(side="left", padx=1)
        disc_entry.insert(0, "0")
        disc_entry.bind("<KeyRelease>", lambda e: self._recalculate_row(row_data))
        row_data["disc_entry"] = disc_entry

        # GST %
        gst_lbl = ctk.CTkLabel(row_frame, text="12", width=50,
                                font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)
        gst_lbl.pack(side="left", padx=1)
        row_data["gst_lbl"] = gst_lbl

        # Amount (calculated)
        amt_lbl = ctk.CTkLabel(row_frame, text="0.00", width=80,
                                font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT)
        amt_lbl.pack(side="left", padx=1)
        row_data["amt_lbl"] = amt_lbl

        # Remove button
        ctk.CTkButton(
            row_frame, text="✕", width=30, height=24,
            font=ctk.CTkFont(size=11), corner_radius=6,
            fg_color=DANGER, hover_color="#D90429", text_color=TEXT_WHITE,
            command=lambda rd=row_data: self._remove_product_row(rd),
        ).pack(side="left", padx=2)

        self.product_rows.append(row_data)

    def _remove_product_row(self, row_data):
        """Remove a product row."""
        row_data["frame"].destroy()
        self.product_rows.remove(row_data)
        self._recalculate_totals()

    def _on_product_search(self, event, row_data):
        """Search products as user types and show a selection popup."""
        query = row_data["product_entry"].get().strip()
        if len(query) < 2:
            return

        try:
            results = search_products(self.user["distributor_id"], query)
        except Exception:
            results = []

        if not results:
            return

        # Create a popup menu
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        # Position near the entry
        entry = row_data["product_entry"]
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        popup.geometry(f"400x{min(len(results) * 28, 200)}+{x}+{y}")

        popup_frame = ctk.CTkScrollableFrame(popup, fg_color=CARD_BG, corner_radius=4)
        popup_frame.pack(fill="both", expand=True)

        for prod in results:
            exp = prod.get("expiry_date", "")
            if hasattr(exp, "strftime"):
                exp = exp.strftime("%m/%y")
            label = f"{prod['product_name']}  |  Batch: {prod['batch_number']}  |  Sell Price: {prod['selling_price']}  |  Qty: {prod['available_qty']}"

            btn = ctk.CTkButton(
                popup_frame, text=label, height=26,
                font=ctk.CTkFont(size=9), corner_radius=4,
                fg_color="transparent", hover_color="#DEE2E6",
                text_color=TEXT_WHITE, anchor="w",
                command=lambda p=prod, pp=popup: self._select_product(row_data, p, pp),
            )
            btn.pack(fill="x", padx=2, pady=1)

        # Close popup when focus lost
        popup.bind("<FocusOut>", lambda e: popup.destroy())
        popup.focus_set()

    def _select_product(self, row_data, product, popup):
        """Fill row with selected product data."""
        popup.destroy()

        row_data["batch_id"] = product["batch_id"]
        row_data["product_data"] = product

        # Fill fields
        row_data["product_entry"].delete(0, "end")
        row_data["product_entry"].insert(0, product["product_name"])
        row_data["batch_lbl"].configure(text=product["batch_number"])

        exp = product.get("expiry_date", "")
        if hasattr(exp, "strftime"):
            exp = exp.strftime("%m/%y")
        row_data["exp_lbl"].configure(text=str(exp))

        mrp = float(product.get("mrp", 0))
        row_data["mrp_lbl"].configure(text=f"{mrp:.2f}")
        row_data["gst_lbl"].configure(text=f"{float(product.get('gst_percent', 12)):.0f}")

        # Set rate = selling_price (default)
        rate = float(product.get("selling_price", product.get("mrp", 0)))
        row_data["rate_entry"].delete(0, "end")
        row_data["rate_entry"].insert(0, f"{rate:.2f}")

        # Set discount = default discount_percent
        disc = float(product.get("discount_percent", 0))
        row_data["disc_entry"].delete(0, "end")
        row_data["disc_entry"].insert(0, f"{disc:.1f}")

        self._recalculate_row(row_data)

    def _recalculate_row(self, row_data):
        """Recalculate amount for a single row."""
        try:
            qty = int(row_data["qty_entry"].get() or "0")
            rate = float(row_data["rate_entry"].get() or "0")
            disc = float(row_data["disc_entry"].get() or "0")
            amount = calculate_item_amount(qty, rate, disc)
            row_data["amt_lbl"].configure(text=f"{amount:.2f}")
        except (ValueError, KeyError):
            row_data["amt_lbl"].configure(text="0.00")

        self._recalculate_totals()

    # ══════════════════════════════════════════════════
    # TOTALS SECTION
    # ══════════════════════════════════════════════════
    def _build_totals_section(self):
        self.totals_frame = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=12,
                                          border_width=1, border_color=BORDER_CLR)
        self.totals_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(self.totals_frame, text="Invoice Summary",
                      font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_WHITE,
                      ).pack(anchor="w", padx=12, pady=(10, 5))

        summary = ctk.CTkFrame(self.totals_frame, fg_color="transparent")
        summary.pack(fill="x", padx=12, pady=(0, 10))

        labels = ["Subtotal:", "Discount:", "SGST:", "CGST:", "Total GST:", "Grand Total:"]
        self.total_labels = {}

        for i, lbl_text in enumerate(labels):
            row = ctk.CTkFrame(summary, fg_color="transparent")
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(row, text=lbl_text, font=ctk.CTkFont(size=11),
                          text_color=TEXT_MUTED, width=100, anchor="e").pack(side="left", padx=(0, 10))

            is_grand = (lbl_text == "Grand Total:")
            val_label = ctk.CTkLabel(
                row, text="₹ 0.00",
                font=ctk.CTkFont(size=14 if is_grand else 11, weight="bold" if is_grand else "normal"),
                text_color=ACCENT if is_grand else TEXT_WHITE,
                anchor="w",
            )
            val_label.pack(side="left")
            self.total_labels[lbl_text] = val_label

    def _recalculate_totals(self):
        """Recalculate and update invoice totals."""
        items = self._collect_items_for_calc()
        if not items:
            for lbl in self.total_labels.values():
                lbl.configure(text="₹ 0.00")
            return

        totals = calculate_invoice_totals(items)
        self.total_labels["Subtotal:"].configure(text=f"₹ {totals['subtotal']:,.2f}")
        self.total_labels["Discount:"].configure(text=f"₹ {totals['discount_amount']:,.2f}")
        self.total_labels["SGST:"].configure(text=f"₹ {totals['sgst']:,.2f}")
        self.total_labels["CGST:"].configure(text=f"₹ {totals['cgst']:,.2f}")
        self.total_labels["Total GST:"].configure(text=f"₹ {totals['total_gst']:,.2f}")
        self.total_labels["Grand Total:"].configure(text=f"₹ {totals['grand_total']:,.2f}")

    def _collect_items_for_calc(self):
        """Collect items data from rows for calculation."""
        items = []
        for row in self.product_rows:
            try:
                qty = int(row["qty_entry"].get() or "0")
                rate = float(row["rate_entry"].get() or "0")
                disc = float(row["disc_entry"].get() or "0")
                gst = float(row["gst_lbl"].cget("text") or "0")
                if qty > 0 and rate > 0:
                    items.append({
                        "qty": qty, "rate": rate,
                        "discount_percent": disc, "gst_percent": gst,
                    })
            except (ValueError, KeyError):
                continue
        return items

    # ══════════════════════════════════════════════════
    # ACTION BUTTONS
    # ══════════════════════════════════════════════════
    def _build_action_buttons(self):
        frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(
            frame, text="🧾  Generate Invoice & PDF", height=45, width=250,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=BG_DARK,
            command=self._generate_invoice,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame, text="🔄  Reset", height=45, width=100,
            font=ctk.CTkFont(size=13), corner_radius=10,
            fg_color="#E9ECEF", hover_color="#CED4DA",
            command=self._reset_form,
        ).pack(side="left", padx=5)

    # ══════════════════════════════════════════════════
    # GENERATE INVOICE
    # ══════════════════════════════════════════════════
    def _generate_invoice(self):
        """Validate, create invoice in DB, generate PDF."""
        # Validate customer
        if not self.selected_customer:
            messagebox.showwarning("Missing Customer", "Please select a customer first.")
            return

        # Collect product items
        items = []
        for row in self.product_rows:
            if not row.get("batch_id"):
                continue
            try:
                qty = int(row["qty_entry"].get() or "0")
                rate = float(row["rate_entry"].get() or "0")
                disc = float(row["disc_entry"].get() or "0")
                if qty <= 0 or rate <= 0:
                    continue

                prod = row.get("product_data", {})
                exp = prod.get("expiry_date", "")
                if hasattr(exp, "strftime"):
                    exp = exp.strftime("%Y-%m-%d")

                items.append({
                    "batch_id": row["batch_id"],
                    "product_name": prod.get("product_name", ""),
                    "batch_no": prod.get("batch_number", ""),
                    "expiry_date": str(exp),
                    "qty": qty,
                    "mrp": float(prod.get("mrp", 0)),
                    "rate": rate,
                    "discount_percent": disc,
                    "gst_percent": float(prod.get("gst_percent", 12)),
                })
            except (ValueError, KeyError):
                continue

        if not items:
            messagebox.showwarning("No Products", "Please add at least one product.")
            return

        # Validate stock
        for item in items:
            batch = get_batch_by_id(item["batch_id"])
            if batch and item["qty"] > batch["available_qty"]:
                messagebox.showwarning(
                    "Insufficient Stock",
                    f"Only {batch['available_qty']} available for {item['product_name']} (Batch: {item['batch_number']})"
                )
                return

        try:
            # Create invoice
            invoice = create_full_invoice(
                distributor_id=self.user["distributor_id"],
                user_id=self.user["user_id"],
                customer_license_no=self.selected_customer["license_no"],
                items=items,
                order_no=self.order_entry.get().strip(),
                lr_no=self.lr_entry.get().strip(),
                transport=self.transport_entry.get().strip(),
                payment_type=self.payment_var.get(),
            )

            # Generate PDF
            customer = get_customer_by_license(self.selected_customer["license_no"])
            distributor = get_distributor_by_id(self.user["distributor_id"])
            pdf_path = generate_invoice_pdf(invoice, distributor, customer)

            # Show success
            result = messagebox.askyesno(
                "Invoice Created ✅",
                f"Invoice {invoice['invoice_no']} created successfully!\n\n"
                f"Grand Total: ₹{float(invoice['grand_total']):,.2f}\n"
                f"PDF saved at: {pdf_path}\n\n"
                f"Open PDF now?",
            )
            if result:
                open_pdf(pdf_path)

            # Go back to dashboard
            self._go_back()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create invoice:\n{e}")

    def _reset_form(self):
        """Reset the form."""
        for row in self.product_rows[:]:
            row["frame"].destroy()
        self.product_rows.clear()
        self._add_product_row()
        self.selected_customer = None
        self.cust_name_lbl.configure(text="No customer selected", text_color=TEXT_MUTED)
        self.cust_info_lbl.configure(text="")
        self.order_entry.delete(0, "end")
        self.lr_entry.delete(0, "end")
        self.transport_entry.delete(0, "end")
        self._recalculate_totals()

    def _go_back(self):
        """Return to dashboard."""
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
