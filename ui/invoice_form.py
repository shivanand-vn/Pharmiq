"""
Invoice Form — CustomTkinter form for creating new invoices.
Dynamic product rows, customer selection, live calculations.
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, datetime
from tkcalendar import Calendar

from models.customer import search_customers, get_customer_by_license
from models.product import search_products, get_batch_by_id
from models.invoice import get_next_order_no
from services.invoice_service import calculate_item_amount, calculate_invoice_totals, create_full_invoice
from services.pdf_generator import generate_invoice_pdf, open_pdf
from models.distributor import get_distributor_by_id

BG_MAIN = "#F8FAFC"
CARD_BG = "#FFFFFF"
ROW_BG_1 = "#FFFFFF"
ROW_BG_2 = "#F1F5F9"
BORDER_CLR = "#E2E8F0"
ACCENT = "#3B82F6"
ACCENT_HOVER = "#2563EB"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
ENTRY_BG = "#F8FAFC"
SUCCESS = "#10B981"
DANGER = "#EF4444"

class InvoiceForm(ctk.CTkFrame):
    def __init__(self, master, user_context, distributor, app_ref):
        super().__init__(master, fg_color=BG_MAIN)
        self.user = user_context
        self.distributor = distributor
        self.app = app_ref
        self.product_rows = []
        self.selected_customer = None

        self._build_ui()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=45)
        top.pack(fill="x", pady=(0, 5))
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=70, height=30,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color=TEXT_DARK,
            command=self._go_back,
        ).pack(side="left", padx=15, pady=8)

        ctk.CTkLabel(
            top, text="Create New Invoice",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_DARK,
        ).pack(side="left", padx=10)

        # ── Scrollable main content ──
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=5)

        # -- Horizontal split: Invoice Details (left 40%) + Customer Details (right 60%) --
        top_split = ctk.CTkFrame(self.scroll, fg_color="transparent")
        top_split.pack(fill="x", pady=(0, 10))
        top_split.columnconfigure(0, weight=4)
        top_split.columnconfigure(1, weight=6)

        self._build_header_section(top_split)
        self._build_customer_section(top_split)
        self._build_product_section()
        
        # Bottom layout (Totals + Actions)
        bottom_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bottom_container.pack(fill="x", pady=(10, 20))
        bottom_container.columnconfigure(0, weight=6)
        bottom_container.columnconfigure(1, weight=4)

        self.actions_container = ctk.CTkFrame(bottom_container, fg_color="transparent")
        self.actions_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._build_action_buttons()

        self.totals_container = ctk.CTkFrame(bottom_container, fg_color="transparent")
        self.totals_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._build_totals_section()

        # Add initial empty row
        self._add_product_row()

        # Autofocus customer search
        self.after(200, lambda: self.cust_search.focus())

    def _build_header_section(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_CLR)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 12))
        ctk.CTkLabel(header, text="Invoice Details", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(side="left")

        fields = ctk.CTkFrame(frame, fg_color="transparent")
        fields.pack(fill="x", padx=15, pady=(0, 15))

        # Row 1: Invoice Date | Order No (50/50 Split)
        r1 = ctk.CTkFrame(fields, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 15))
        r1.columnconfigure(0, weight=1)
        r1.columnconfigure(1, weight=1)

        # Invoice Date
        date_col = ctk.CTkFrame(r1, fg_color="transparent")
        date_col.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(date_col, text="Invoice Date", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        
        date_input_row = ctk.CTkFrame(date_col, fg_color="transparent")
        date_input_row.pack(fill="x", pady=(4, 0))
        self.date_entry = ctk.CTkEntry(date_input_row, height=34, font=ctk.CTkFont(size=12), fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK, corner_radius=6)
        self.date_entry.pack(side="left", fill="x", expand=True)
        self.date_entry.insert(0, date.today().strftime("%d/%m/%Y"))
        ctk.CTkButton(
            date_input_row, text="📅", width=34, height=34, font=ctk.CTkFont(size=14),
            corner_radius=6, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            command=self._open_calendar,
        ).pack(side="left", padx=(4, 0))

        # Order No
        order_col = ctk.CTkFrame(r1, fg_color="transparent")
        order_col.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(order_col, text="Order No", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        self.order_entry = ctk.CTkEntry(order_col, height=34, font=ctk.CTkFont(size=12), fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK, corner_radius=6)
        self.order_entry.pack(fill="x", pady=(4, 0))
        try:
            self.order_entry.insert(0, get_next_order_no(self.user["distributor_id"]))
        except Exception:
            self.order_entry.insert(0, "1")

        # Row 2: Payment Radio Buttons
        r2 = ctk.CTkFrame(fields, fg_color="transparent")
        r2.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(r2, text="Payment Method", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        
        radio_row = ctk.CTkFrame(r2, fg_color="transparent")
        radio_row.pack(fill="x", pady=(8, 0))
        
        self.payment_var = ctk.StringVar(value="Credit")
        opts = [("Credit", "Credit"), ("Cash", "Cash"), ("UPI", "UPI")]
        for text, val in opts:
            rb = ctk.CTkRadioButton(
                radio_row, text=text, variable=self.payment_var, value=val,
                font=ctk.CTkFont(size=12), border_color=ACCENT, hover_color=ACCENT_HOVER,
                fg_color=ACCENT, text_color=TEXT_DARK, width=100
            )
            rb.pack(side="left", padx=(0, 20))

    def _build_customer_section(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_CLR)
        frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 5))
        ctk.CTkLabel(header, text="Customer Details", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(side="left")

        search_row = ctk.CTkFrame(frame, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=(0, 10))

        # Separate the search from the preview for more visual weight
        self.cust_search = ctk.CTkEntry(search_row, height=34, font=ctk.CTkFont(size=12), placeholder_text="🔍 Search customers (Name or License No)...", fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK, corner_radius=6)
        self.cust_search.pack(fill="x")
        self.cust_search.bind("<KeyRelease>", self._on_customer_search)

        self.cust_details_box = ctk.CTkFrame(frame, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color=BORDER_CLR)
        self.cust_details_box.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        content = ctk.CTkFrame(self.cust_details_box, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=12)

        # Row 1: Shop Name — Owner Name
        self.cust_name_lbl = ctk.CTkLabel(content, text="No customer selected", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_MUTED)
        self.cust_name_lbl.pack(anchor="w", pady=(0, 10))

        # Row 2: 3-Column Info Row (License | GST | Mobile)
        self.info_row = ctk.CTkFrame(content, fg_color="transparent")
        self.info_row.pack(fill="x", pady=(0, 10))
        for i in range(3): self.info_row.columnconfigure(i, weight=1)

        def add_sub_field(parent, col, label):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=0, column=col, sticky="nsew")
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
            val = ctk.CTkLabel(f, text="—", font=ctk.CTkFont(size=12), text_color=TEXT_DARK)
            val.pack(anchor="w")
            return val

        self.lbl_license = add_sub_field(self.info_row, 0, "License No")
        self.lbl_gst = add_sub_field(self.info_row, 1, "GST No")
        self.lbl_mobile = add_sub_field(self.info_row, 2, "Mobile No")

        # Row 3: Address Footer
        sep = ctk.CTkFrame(content, fg_color=BORDER_CLR, height=1)
        sep.pack(fill="x", pady=(5, 10))
        
        addr_header = ctk.CTkLabel(content, text="ADDRESS", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        addr_header.pack(anchor="w")
        self.lbl_address = ctk.CTkLabel(content, text="Type above to search...", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, justify="left", wraplength=400)
        self.lbl_address.pack(anchor="w")

        self._customer_list = []
        self._cust_popup = None

    def _on_customer_search(self, event=None):
        query = self.cust_search.get().strip()
        if len(query) < 2:
            if self._cust_popup:
                self._cust_popup.destroy()
                self._cust_popup = None
            return

        try:
            customers = search_customers(self.user["distributor_id"], query)
        except Exception:
            customers = []

        self._customer_list = customers

        if self._cust_popup:
            self._cust_popup.destroy()
            self._cust_popup = None

        if not customers:
            return

        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        self._cust_popup = popup

        x = self.cust_search.winfo_rootx()
        y = self.cust_search.winfo_rooty() + self.cust_search.winfo_height()
        w = self.cust_search.winfo_width()
        popup.geometry(f"{w}x{min(len(customers) * 40, 250)}+{x}+{y}")

        popup_frame = ctk.CTkScrollableFrame(popup, fg_color=CARD_BG, corner_radius=6, border_width=1, border_color=BORDER_CLR)
        popup_frame.pack(fill="both", expand=True)

        for c in customers:
            label = f"🏪 {c['shop_name']}  —  {c.get('license_no', '')}  |  📞 {c.get('mobile_no', 'N/A')}"
            btn = ctk.CTkButton(
                popup_frame, text=label, height=36, font=ctk.CTkFont(size=11), corner_radius=4,
                fg_color="transparent", hover_color="#F1F5F9", text_color=TEXT_DARK, anchor="w",
                command=lambda cust=c, pp=popup: self._select_customer(cust, pp),
            )
            btn.pack(fill="x", padx=4, pady=2)

        popup.bind("<FocusOut>", lambda e: self._close_cust_popup())

    def _close_cust_popup(self):
        if self._cust_popup:
            self._cust_popup.destroy()
            self._cust_popup = None

    def _select_customer(self, c, popup):
        popup.destroy()
        self._cust_popup = None
        self.selected_customer = c
        self.cust_search.delete(0, "end")
        self.cust_search.insert(0, f"{c['shop_name']} ({c['license_no']})")
        
        # UI Updates for structured preview
        self.cust_name_lbl.configure(text=f"🏪  {c['shop_name']}  —  {c.get('license_holder_name', 'Owner Name')}", text_color=TEXT_DARK)
        self.lbl_license.configure(text=c['license_no'], text_color=TEXT_DARK)
        self.lbl_gst.configure(text=c.get('gst_no', 'N/A'), text_color=TEXT_DARK)
        self.lbl_mobile.configure(text=c.get('mobile_no', 'N/A'), text_color=TEXT_DARK)
        
        addr_parts = [c.get('address_line1', ''), c.get('city', ''), c.get('state', '')]
        address = ', '.join(p for p in addr_parts if p) or c.get('address', 'N/A')
        self.lbl_address.configure(text=address, text_color=TEXT_DARK)

    def _build_product_section(self):
        frame = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_CLR)
        frame.pack(fill="x", pady=(0, 10))

        header_row = ctk.CTkFrame(frame, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=(15, 8))

        ctk.CTkLabel(header_row, text="Products", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(side="left")

        ctk.CTkButton(
            header_row, text="+ Add Row", width=90, height=30,
            font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6,
            fg_color=SUCCESS, hover_color="#059669", text_color="#FFFFFF",
            command=self._add_product_row,
        ).pack(side="right")

        col_header = ctk.CTkFrame(frame, fg_color="#F1F5F9", corner_radius=6, height=36)
        col_header.pack(fill="x", padx=15, pady=(0, 4))
        col_header.pack_propagate(False)

        col_names = ["#", "Product Name", "Batch", "Expiry", "Qty", "MRP", "Rate", "Disc%", "GST%", "Amount", ""]
        col_widths = [25, 230, 85, 60, 55, 70, 70, 55, 50, 95, 30]
        self.col_widths = col_widths
        for name, w in zip(col_names, col_widths):
            ctk.CTkLabel(col_header, text=name.upper(), width=w, font=ctk.CTkFont(size=10, weight="bold"), text_color="#475569", anchor="w" if name != "#" else "center").pack(side="left", padx=2, pady=8)

        self.products_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.products_frame.pack(fill="x", padx=15, pady=(0, 15))

    def _add_product_row(self):
        idx = len(self.product_rows)
        bg = ROW_BG_1 if idx % 2 == 0 else ROW_BG_2

        row_frame = ctk.CTkFrame(self.products_frame, fg_color=bg, corner_radius=6, height=40)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)

        rd = {"frame": row_frame, "batch_id": None}
        widths = self.col_widths

        ctk.CTkLabel(row_frame, text=str(idx + 1), width=widths[0], font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left", padx=2)

        pe = ctk.CTkEntry(row_frame, width=widths[1], height=30, font=ctk.CTkFont(size=11), placeholder_text="Type to search...", fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK)
        pe.pack(side="left", padx=2)
        rd["product_entry"] = pe
        pe.bind("<KeyRelease>", lambda e, r=rd: self._on_product_search(e, r))

        lbl = lambda w: ctk.CTkLabel(row_frame, text="", width=w, font=ctk.CTkFont(size=11), text_color=TEXT_DARK, anchor="w")
        rd["batch_lbl"] = lbl(widths[2]); rd["batch_lbl"].pack(side="left", padx=2)
        rd["exp_lbl"] = lbl(widths[3]); rd["exp_lbl"].pack(side="left", padx=2)

        def make_entry(w, val):
            en = ctk.CTkEntry(row_frame, width=w, height=30, font=ctk.CTkFont(size=11), fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK)
            en.pack(side="left", padx=2); en.insert(0, val)
            en.bind("<KeyRelease>", lambda e, r=rd: self._recalculate_row(r))
            return en

        rd["qty_entry"] = make_entry(widths[4], "1")
        
        rd["mrp_lbl"] = lbl(widths[5])
        rd["mrp_lbl"].configure(text="0.00")
        rd["mrp_lbl"].pack(side="left", padx=2)

        rd["rate_entry"] = make_entry(widths[6], "0.00")
        rd["disc_entry"] = make_entry(widths[7], "0")
        
        rd["gst_lbl"] = ctk.CTkLabel(row_frame, text="12", width=widths[8], font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, anchor="w")
        rd["gst_lbl"].pack(side="left", padx=2)

        rd["amt_lbl"] = ctk.CTkLabel(row_frame, text="₹ 0.00", width=widths[9], font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT, anchor="w")
        rd["amt_lbl"].pack(side="left", padx=2)

        ctk.CTkButton(row_frame, text="✕", width=26, height=26, font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6, fg_color="#FEE2E2", hover_color="#FECACA", text_color="#EF4444", command=lambda r=rd: self._remove_product_row(r)).pack(side="left", padx=2)
        self.product_rows.append(rd)

    def _remove_product_row(self, row_data):
        row_data["frame"].destroy()
        self.product_rows.remove(row_data)
        self._recalculate_totals()

    def _on_product_search(self, event, row_data):
        query = row_data["product_entry"].get().strip()
        if len(query) < 2: return
        try: results = search_products(self.user["distributor_id"], query)
        except Exception: results = []
        if not results: return

        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        entry = row_data["product_entry"]
        x, y = entry.winfo_rootx(), entry.winfo_rooty() + entry.winfo_height()
        popup.geometry(f"520x{min(len(results) * 40, 350)}+{x}+{y}")

        popup_frame = ctk.CTkScrollableFrame(popup, fg_color=CARD_BG, corner_radius=6, border_width=1, border_color=BORDER_CLR)
        popup_frame.pack(fill="both", expand=True)

        for prod in results:
            exp = prod.get("expiry_date", "")
            if hasattr(exp, "strftime"): exp = exp.strftime("%m/%y")
            label = f"{prod['product_name']} | B: {prod['batch_number']} | MRP: ₹{prod['mrp']} | Qty: {prod['available_qty']} | Exp: {exp}"
            btn = ctk.CTkButton(
                popup_frame, text=label, height=36, font=ctk.CTkFont(size=11), corner_radius=4,
                fg_color="transparent", hover_color="#F1F5F9", text_color=TEXT_DARK, anchor="w",
                command=lambda p=prod, pp=popup: self._select_product(row_data, p, pp),
            )
            btn.pack(fill="x", padx=4, pady=2)
        popup.bind("<FocusOut>", lambda e: popup.destroy())
        popup.focus_set()

    def _select_product(self, row_data, product, popup):
        popup.destroy()
        row_data["batch_id"] = product["batch_id"]
        row_data["product_data"] = product

        row_data["product_entry"].delete(0, "end")
        row_data["product_entry"].insert(0, product["product_name"])
        row_data["batch_lbl"].configure(text=product["batch_number"])

        exp = product.get("expiry_date", "")
        if hasattr(exp, "strftime"): exp = exp.strftime("%m/%y")
        row_data["exp_lbl"].configure(text=str(exp))

        row_data["mrp_lbl"].configure(text=f"{float(product.get('mrp', 0)):.2f}")
        row_data["gst_lbl"].configure(text=f"{float(product.get('gst_percent', 12)):.0f}")

        rate = float(product.get("selling_price", product.get("mrp", 0)))
        row_data["rate_entry"].delete(0, "end"); row_data["rate_entry"].insert(0, f"{rate:.2f}")
        disc = float(product.get("discount_percent", 0))
        row_data["disc_entry"].delete(0, "end"); row_data["disc_entry"].insert(0, f"{disc:.1f}")

        self._recalculate_row(row_data)

    def _recalculate_row(self, row_data):
        try:
            qty = int(row_data["qty_entry"].get() or "0")
            rate = float(row_data["rate_entry"].get() or "0")
            disc = float(row_data["disc_entry"].get() or "0")
            row_data["amt_lbl"].configure(text=f"₹ {calculate_item_amount(qty, rate, disc):.2f}")
        except (ValueError, KeyError):
            row_data["amt_lbl"].configure(text="₹ 0.00")
        self._recalculate_totals()

    def _build_totals_section(self):
        self.totals_frame = ctk.CTkFrame(self.totals_container, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_CLR)
        self.totals_frame.pack(fill="both", expand=True)

        header = ctk.CTkFrame(self.totals_frame, fg_color="#F8FAFC", corner_radius=8)
        header.pack(fill="x", padx=2, pady=2)
        ctk.CTkLabel(header, text="Invoice Summary", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_DARK).pack(pady=10)

        summary = ctk.CTkFrame(self.totals_frame, fg_color="transparent")
        summary.pack(fill="x", padx=20, pady=15)

        labels = ["Subtotal", "Discount", "SGST", "CGST", "Total GST", "Grand Total"]
        self.total_labels = {}

        for lbl_text in labels:
            row = ctk.CTkFrame(summary, fg_color="transparent")
            row.pack(fill="x", pady=4)
            is_grand = (lbl_text == "Grand Total")
            if is_grand: ctk.CTkFrame(summary, fg_color=BORDER_CLR, height=1).pack(fill="x", pady=(10, 10))
            ctk.CTkLabel(row, text=lbl_text, font=ctk.CTkFont(size=12 if is_grand else 11, weight="bold" if is_grand else "normal"), text_color=TEXT_DARK if is_grand else TEXT_MUTED).pack(side="left")
            val_label = ctk.CTkLabel(row, text="₹ 0.00", font=ctk.CTkFont(size=16 if is_grand else 12, weight="bold" if is_grand else "normal"), text_color=ACCENT if is_grand else TEXT_DARK)
            val_label.pack(side="right")
            self.total_labels[lbl_text] = val_label

    def _recalculate_totals(self):
        items = []
        for row in self.product_rows:
            try:
                qty, rate, disc, gst = int(row["qty_entry"].get() or "0"), float(row["rate_entry"].get() or "0"), float(row["disc_entry"].get() or "0"), float(row["gst_lbl"].cget("text") or "0")
                if qty > 0 and rate > 0: items.append({"qty": qty, "rate": rate, "discount_percent": disc, "gst_percent": gst})
            except (ValueError, KeyError): continue

        if not items:
            for lbl in self.total_labels.values(): lbl.configure(text="₹ 0.00")
            return

        totals = calculate_invoice_totals(items)
        self.total_labels["Subtotal"].configure(text=f"₹ {totals['subtotal']:,.2f}")
        self.total_labels["Discount"].configure(text=f"₹ {totals['discount_amount']:,.2f}")
        self.total_labels["SGST"].configure(text=f"₹ {totals['sgst']:,.2f}")
        self.total_labels["CGST"].configure(text=f"₹ {totals['cgst']:,.2f}")
        self.total_labels["Total GST"].configure(text=f"₹ {totals['total_gst']:,.2f}")
        self.total_labels["Grand Total"].configure(text=f"₹ {totals['grand_total']:,.2f}")

    def _build_action_buttons(self):
        frame = ctk.CTkFrame(self.actions_container, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_CLR)
        frame.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(expand=True)

        ctk.CTkButton(
            inner, text="🧾  Generate Invoice & PDF", height=45, width=280,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            command=self._generate_invoice,
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            inner, text="🔄  Reset Form", height=35, width=280,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#475569",
            command=self._reset_form,
        ).pack()

    def _open_calendar(self):
        """Open a calendar popup to pick the invoice date (today or earlier)."""
        cal_win = ctk.CTkToplevel(self)
        cal_win.title("Select Invoice Date")
        cal_win.geometry("320x320")
        cal_win.transient(self.master)
        cal_win.grab_set()
        cal_win.resizable(False, False)

        # Center relative to main window
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 160
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 160
        cal_win.geometry(f"+{x}+{y}")

        # Parse current entry value as initial date
        try:
            init_date = datetime.strptime(self.date_entry.get().strip(), "%d/%m/%Y").date()
        except ValueError:
            init_date = date.today()

        cal = Calendar(
            cal_win, selectmode="day",
            year=init_date.year, month=init_date.month, day=init_date.day,
            maxdate=date.today(),
            date_pattern="dd/mm/yyyy",
            background="#1B4F6B", foreground="white",
            headersbackground="#3B82F6", headersforeground="white",
            selectbackground="#3B82F6", selectforeground="white",
            normalbackground="white", normalforeground="#111827",
            weekendbackground="#F1F5F9", weekendforeground="#111827",
            othermonthbackground="#F8FAFC", othermonthforeground="#94A3B8",
            othermonthwebackground="#F8FAFC", othermonthweforeground="#94A3B8",
            font=("Segoe UI", 11),
        )
        cal.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        def pick_date():
            selected = cal.get_date()
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, selected)
            cal_win.destroy()

        ctk.CTkButton(
            cal_win, text="✓  Select Date", height=36, width=140,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            command=pick_date,
        ).pack(pady=(5, 10))

    def _generate_invoice(self):
        if not self.selected_customer: return messagebox.showwarning("Missing Customer", "Please select a customer first.")

        # Validate invoice date: must be today or in the past
        raw_date = self.date_entry.get().strip()
        try:
            inv_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
        except ValueError:
            return messagebox.showerror("Invalid Date", "Invoice date must be in DD/MM/YYYY format.")
        if inv_date > date.today():
            return messagebox.showerror("Future Date", "Invoice date cannot be in the future. Please select today or an earlier date.")

        items = []
        for row in self.product_rows:
            if not row.get("batch_id"): continue
            try:
                qty, rate, disc = int(row["qty_entry"].get() or "0"), float(row["rate_entry"].get() or "0"), float(row["disc_entry"].get() or "0")
                if qty <= 0 or rate <= 0: continue
                prod = row.get("product_data", {})
                exp = prod.get("expiry_date", "")
                if hasattr(exp, "strftime"): exp = exp.strftime("%Y-%m-%d")
                items.append({
                    "batch_id": row["batch_id"], "product_name": prod.get("product_name", ""),
                    "batch_no": prod.get("batch_number", ""), "expiry_date": str(exp),
                    "qty": qty, "mrp": float(prod.get("mrp", 0)), "rate": rate,
                    "discount_percent": disc, "gst_percent": float(prod.get("gst_percent", 12)),
                })
            except (ValueError, KeyError): continue
        if not items: return messagebox.showwarning("No Products", "Please add at least one product.")
        for item in items:
            batch = get_batch_by_id(item["batch_id"])
            if batch and item["qty"] > batch["available_qty"]:
                return messagebox.showwarning("Insufficient Stock", f"Only {batch['available_qty']} available for {item['product_name']} (Batch: {item['batch_number']})")
        try:
            invoice = create_full_invoice(
                distributor_id=self.user["distributor_id"], user_id=self.user["user_id"],
                customer_license_no=self.selected_customer["license_no"], items=items,
                order_no=self.order_entry.get().strip(), lr_no=self.lr_entry.get().strip(),
                transport=self.transport_entry.get().strip(), payment_type=self.payment_var.get(),
                invoice_date=inv_date.strftime("%Y-%m-%d"),
            )
            customer = get_customer_by_license(self.selected_customer["license_no"])
            distributor = get_distributor_by_id(self.user["distributor_id"])
            pdf_path = generate_invoice_pdf(invoice, distributor, customer)
            if messagebox.askyesno("Invoice Created ✅", f"Invoice {invoice['invoice_no']} created successfully!\n\nGrand Total: ₹{float(invoice['grand_total']):,.2f}\nPDF saved at: {pdf_path}\n\nOpen PDF now?"):
                open_pdf(pdf_path)
            self._go_back()
        except Exception as e: messagebox.showerror("Error", f"Failed to create invoice:\n{e}")

    def _reset_form(self):
        for row in self.product_rows[:]: row["frame"].destroy()
        self.product_rows.clear(); self._add_product_row(); self.selected_customer = None
        self.cust_name_lbl.configure(text="No customer selected", text_color=TEXT_MUTED)
        self.cust_info_lbl.configure(text="Search and select a customer to populate their billing credentials.")
        self.order_entry.delete(0, "end"); self.lr_entry.delete(0, "end"); self.transport_entry.delete(0, "end")
        self._recalculate_totals()

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children(): widget.destroy()
        Dashboard(self.master, self.user, self.app).pack(fill="both", expand=True)
