"""
Payments View — Customer-wise payment tracking and FIFO allocation.
Redesigned with modern aesthetics and side-by-side layout.
"""

import customtkinter as ctk
from tkinter import messagebox
import datetime
from models.payment import (
    get_customer_payment_summary, get_invoices_for_customer,
    get_payment_history, record_payment
)

class PaymentsView(ctk.CTkFrame):
    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color="#F1F4F9")
        self.user = user_context
        self.app = app_ref
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self._build_header()
        self._build_customer_table()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=70)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Customer Payments",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1B4F6B"
        ).pack(side="left")

        # Search
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="🔍 Search customers by name...",
            width=350, height=40, corner_radius=20, border_width=0,
            fg_color="#FFFFFF"
        )
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_customers())

    def _build_customer_table(self):
        container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=15)
        container.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        
        # Table Header
        header_row = ctk.CTkFrame(container, fg_color="#F8FAFC", corner_radius=0, height=50)
        header_row.pack(fill="x", pady=(15, 5), padx=2)
        header_row.pack_propagate(False)
        
        cols = [
            ("Customer Name", 350),
            ("Total Invoiced", 150),
            ("Total Paid", 150),
            ("Pending", 150),
            ("Action", 120)
        ]
        
        for text, w in cols:
            ctk.CTkLabel(
                header_row, text=text, width=w,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#475569", anchor="w" if text != "Action" else "center"
            ).pack(side="left", padx=15)

        self.scroll_frame = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=2, pady=(0, 10))
        
        self._refresh_customers()

    def _refresh_customers(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
            
        try:
            customers = get_customer_payment_summary(self.user["distributor_id"])
        except Exception as e:
            print(f"Error fetching payments: {e}")
            customers = []

        query = self.search_entry.get().lower()
        if query:
            customers = [c for c in customers if query in c["shop_name"].lower()]

        if not customers:
            ctk.CTkLabel(self.scroll_frame, text="No customers found.", font=ctk.CTkFont(size=14), text_color="#94A3B8").pack(pady=40)
            return

        for c in customers:
            row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=55)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            
            # Hover effect
            def on_enter(e, r=row): r.configure(fg_color="#F8FAFC")
            def on_leave(e, r=row): r.configure(fg_color="transparent")
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)

            ctk.CTkLabel(row, text=c["shop_name"], width=350, anchor="w", font=ctk.CTkFont(size=15)).pack(side="left", padx=15)
            ctk.CTkLabel(row, text=f"₹{float(c['total_invoiced']):,.2f}", width=150, anchor="w", text_color="#334155").pack(side="left", padx=15)
            ctk.CTkLabel(row, text=f"₹{float(c['total_paid']):,.2f}", width=150, anchor="w", text_color="#10B981").pack(side="left", padx=15)
            
            balance = float(c['outstanding_balance'])
            balance_color = "#E11D48" if balance > 0 else "#10B981"
            ctk.CTkLabel(row, text=f"₹{balance:,.2f}", width=150, anchor="w", font=ctk.CTkFont(size=15, weight="bold"), text_color=balance_color).pack(side="left", padx=15)
            
            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=120)
            btn_frame.pack(side="left", padx=15)
            ctk.CTkButton(
                btn_frame, text="View / Pay", width=100, height=32,
                fg_color="#1B4F6B", hover_color="#0F364A", corner_radius=10,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda cust=c: self._show_detail(cust)
            ).pack(expand=True)

            ctk.CTkFrame(self.scroll_frame, fg_color="#F1F5F9", height=1).pack(fill="x", padx=15)

    def _show_detail(self, customer):
        for w in self.master.winfo_children():
            w.destroy()
        detail = CustomerPaymentDetail(self.master, self.user, self.app, customer)
        detail.pack(fill="both", expand=True)


class CustomerPaymentDetail(ctk.CTkFrame):
    def __init__(self, master, user_context, app_ref, customer):
        super().__init__(master, fg_color="#F1F4F9")
        self.user = user_context
        self.app = app_ref
        self.customer = customer
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        header.pack_propagate(False)

        ctk.CTkButton(
            header, text="← Back to List", width=110, height=35,
            fg_color="transparent", text_color="#1B4F6B", border_width=1, border_color="#1B4F6B",
            corner_radius=10, font=ctk.CTkFont(weight="bold"),
            command=self._go_back
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"  {self.customer['shop_name']}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#1B4F6B"
        ).pack(side="left", padx=15)

    def _build_content(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        content.columnconfigure(0, weight=7)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(0, weight=1)

        # --- LEFT COLUMN: HISTORY ---
        left_col = ctk.CTkFrame(content, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        left_col.columnconfigure(0, weight=1)
        left_col.rowconfigure(1, weight=1)

        # Invoice Card
        inv_card = ctk.CTkFrame(left_col, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        inv_card.pack(fill="both", expand=True, pady=(0, 15))
        
        ctk.CTkLabel(inv_card, text="📄 Invoice History", font=ctk.CTkFont(size=17, weight="bold"), text_color="#1E293B").pack(anchor="w", padx=25, pady=(20, 10))
        
        self.inv_scroll = ctk.CTkScrollableFrame(inv_card, fg_color="transparent")
        self.inv_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        self._load_invoices()

        # Payment Card
        pay_card = ctk.CTkFrame(left_col, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        pay_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(pay_card, text="📜 Payment Logs", font=ctk.CTkFont(size=17, weight="bold"), text_color="#1E293B").pack(anchor="w", padx=25, pady=(20, 10))
        
        self.pay_scroll = ctk.CTkScrollableFrame(pay_card, fg_color="transparent")
        self.pay_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 20))
        self._load_payments()

        # --- RIGHT COLUMN: SUMMARY & FORM ---
        right_col = ctk.CTkFrame(content, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        right_col.columnconfigure(0, weight=1)

        # Summary Card
        summ_card = ctk.CTkFrame(right_col, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        summ_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(summ_card, text="Summary", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1E293B").pack(anchor="w", padx=20, pady=(15, 5))
        
        # Pending Highlight
        pending_box = ctk.CTkFrame(summ_card, fg_color="#FFF1F2", corner_radius=10)
        pending_box.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(pending_box, text="Pending Amount", font=ctk.CTkFont(size=13), text_color="#BE123C").pack(pady=(12, 0))
        ctk.CTkLabel(pending_box, text=f"₹{float(self.customer['outstanding_balance']):,.2f}", font=ctk.CTkFont(size=24, weight="bold"), text_color="#E11D48").pack(pady=(0, 12))

        for label, val, color in [("Total Invoiced", f"₹{float(self.customer['total_invoiced']):,.2f}", "#64748B"), ("Total Paid", f"₹{float(self.customer['total_paid']):,.2f}", "#10B981")]:
            f = ctk.CTkFrame(summ_card, fg_color="transparent")
            f.pack(fill="x", padx=25, pady=5)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12), text_color="#64748B").pack(side="left")
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=13, weight="bold"), text_color=color).pack(side="right")
        
        ctk.CTkFrame(summ_card, fg_color="transparent", height=15).pack()

        # Payment Form Card
        form_card = ctk.CTkFrame(right_col, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        form_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(form_card, text="💸 Record New Payment", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1B4F6B").pack(anchor="w", padx=20, pady=(20, 15))
        
        container = ctk.CTkFrame(form_card, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20)
        
        ctk.CTkLabel(container, text="Payment Amount", font=ctk.CTkFont(size=13, weight="bold"), text_color="#475569").pack(anchor="w")
        self.amount_entry = ctk.CTkEntry(container, placeholder_text="0.00", height=45, font=ctk.CTkFont(size=18, weight="bold"), corner_radius=8, fg_color="#F8FAFC", border_width=1)
        self.amount_entry.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(container, text="Payment Mode", font=ctk.CTkFont(size=13, weight="bold"), text_color="#475569").pack(anchor="w")
        self.mode_var = ctk.StringVar(value="Cash")
        self.mode_opt = ctk.CTkOptionMenu(container, values=["Cash", "UPI", "Bank Transaction"], variable=self.mode_var, height=40, corner_radius=8, fg_color="#1B4F6B", button_color="#13415A")
        self.mode_opt.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(container, text="Transaction Date", font=ctk.CTkFont(size=13, weight="bold"), text_color="#475569").pack(anchor="w")
        self.date_entry = ctk.CTkEntry(container, height=40, corner_radius=8, fg_color="#F8FAFC", border_width=1)
        self.date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.date_entry.pack(fill="x", pady=(5, 30))
        
        self.submit_btn = ctk.CTkButton(
            container, text="Confirm & Record Payment", height=50,
            fg_color="#10B981", hover_color="#059669", corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._submit_payment
        )
        self.submit_btn.pack(fill="x", pady=(0, 20))

    def _load_invoices(self):
        try:
            invoices = get_invoices_for_customer(self.customer["license_no"])
        except:
            invoices = []
            
        if not invoices:
            ctk.CTkLabel(self.inv_scroll, text="No invoices found for this customer.", font=ctk.CTkFont(size=13), text_color="#94A3B8").pack(pady=40)
            return

        # Header Row
        h = ctk.CTkFrame(self.inv_scroll, fg_color="#F1F5F9", height=40, corner_radius=8)
        h.pack(fill="x", pady=(0, 10))
        h.pack_propagate(False)
        for t, w in [("Inv No", 120), ("Date", 120), ("Grand Total", 140), ("Paid", 120), ("Status", 100)]:
            ctk.CTkLabel(h, text=t, width=w, font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B", anchor="w" if t != "Status" else "center").pack(side="left", padx=10)

        for inv in invoices:
            row = ctk.CTkFrame(self.inv_scroll, fg_color="transparent", height=45)
            row.pack(fill="x")
            
            ctk.CTkLabel(row, text=inv["invoice_no"], width=120, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            dt = inv["invoice_date"]
            if hasattr(dt, "strftime"): dt = dt.strftime("%d %b %Y")
            ctk.CTkLabel(row, text=dt, width=120, anchor="w", text_color="#475569").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"₹{float(inv['grand_total']):,.2f}", width=140, anchor="w", text_color="#1E293B").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"₹{float(inv['paid_amount']):,.2f}", width=120, anchor="w", text_color="#10B981").pack(side="left", padx=10)
            
            # Badge
            st = inv["status"]
            colors = {
                "Paid": ("#059669", "#D1FAE5"),
                "Partial": ("#D97706", "#FEF3C7"),
                "Pending": ("#DC2626", "#FEE2E2")
            }
            txt_c, bg_c = colors.get(st, ("#64748B", "#F1F5F9"))
            badge = ctk.CTkFrame(row, fg_color=bg_c, corner_radius=12, width=80, height=24)
            badge.pack_propagate(False)
            badge.pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(badge, text=st, font=ctk.CTkFont(size=11, weight="bold"), text_color=txt_c).pack(expand=True)
            
            ctk.CTkFrame(self.inv_scroll, fg_color="#F1F5F9", height=1).pack(fill="x", padx=5)

    def _load_payments(self):
        try:
            payments = get_payment_history(self.customer["license_no"])
        except:
            payments = []
            
        if not payments:
            ctk.CTkLabel(self.pay_scroll, text="No payment history available.", font=ctk.CTkFont(size=13), text_color="#94A3B8").pack(pady=40)
            return

        h = ctk.CTkFrame(self.pay_scroll, fg_color="#F1F5F9", height=40, corner_radius=8)
        h.pack(fill="x", pady=(0, 10))
        h.pack_propagate(False)
        for t, w in [("Transaction Date", 180), ("Amount Received", 180), ("Payment Mode", 150)]:
            ctk.CTkLabel(h, text=t, width=w, font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748B", anchor="w").pack(side="left", padx=15)

        for p in payments:
            row = ctk.CTkFrame(self.pay_scroll, fg_color="transparent", height=45)
            row.pack(fill="x")
            
            dt = p["payment_date"]
            if hasattr(dt, "strftime"): dt = dt.strftime("%d %b %Y, %I:%M %p") if isinstance(dt, datetime.datetime) else dt.strftime("%d %b %Y")
            ctk.CTkLabel(row, text=dt, width=180, anchor="w", text_color="#475569").pack(side="left", padx=15)
            ctk.CTkLabel(row, text=f"₹{float(p['amount']):,.2f}", width=180, anchor="w", text_color="#10B981", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=15)
            ctk.CTkLabel(row, text=p["payment_mode"], width=150, anchor="w", text_color="#334155").pack(side="left", padx=15)
            
            ctk.CTkFrame(self.pay_scroll, fg_color="#F1F5F9", height=1).pack(fill="x", padx=5)

    def _submit_payment(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid numeric amount.")
            return
            
        if amount <= 0:
            messagebox.showerror("Invalid Amount", "Please enter an amount greater than zero.")
            return
            
        outstanding = float(self.customer["outstanding_balance"])
        if amount > outstanding + 0.01:
            messagebox.showerror("Limit Exceeded", f"Payment cannot exceed the pending amount (₹{outstanding:,.2f}).")
            return
            
        mode = self.mode_var.get()
        date_str = self.date_entry.get()

        # --- WARNING/CONFIRMATION ---
        confirm = messagebox.askyesno(
            "Confirm Payment",
            f"Are you sure you want to record this payment?\n\n"
            f"Customer: {self.customer['shop_name']}\n"
            f"Amount: ₹{amount:,.2f}\n"
            f"Mode: {mode}\n\n"
            "This action will update the balance of the oldest pending invoices."
        )
        
        if not confirm:
            return

        try:
            record_payment(
                distributor_id=self.user["distributor_id"],
                customer_license_no=self.customer["license_no"],
                amount=amount,
                mode=mode,
                date=date_str
            )
            messagebox.showinfo("Success", "Payment successfully recorded and allocated.")
            self._refresh_view()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record payment: {e}")

    def _refresh_view(self):
        try:
            # Re-fetch summary data for this customer
            summaries = get_customer_payment_summary(self.user["distributor_id"])
            for s in summaries:
                if s["license_no"] == self.customer["license_no"]:
                    self.customer = s
                    break
        except:
            pass
            
        for w in self.master.winfo_children():
            w.destroy()
        self.__init__(self.master, self.user, self.app, self.customer)
        self.pack(fill="both", expand=True)

    def _go_back(self):
        for w in self.master.winfo_children():
            w.destroy()
        view = PaymentsView(self.master, self.user, self.app)
        view.pack(fill="both", expand=True)
