"""
Payments View — Streamlined Customer Payments with Descriptive Sidebar.
Restores the "described sections" experience within the sidebar.
"""

import customtkinter as ctk
from tkinter import messagebox
import datetime
from models.payment import (
    get_customer_payment_summary, get_invoices_for_customer,
    get_payment_history, record_payment
)
from utils.async_db import async_db_call

class PaymentsView(ctk.CTkFrame):
    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color="#F1F4F9")
        self.user = user_context
        self.app = app_ref
        self._after_ids = []
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self._build_header()
        self._build_main_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=70)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(15, 5))
        header.pack_propagate(False)

        ctk.CTkButton(
            header, text="← Back", width=80, height=35,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            border_width=1, border_color="#E2E8F0",
            corner_radius=10, font=ctk.CTkFont(weight="bold"),
            command=self._go_dashboard
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="  Customer Payments",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#1B4F6B"
        ).pack(side="left", padx=10)

        # Search
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="🔍 Search customers by name...",
            width=350, height=42, corner_radius=21, border_width=0,
            fg_color="#FFFFFF"
        )
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_customers())
        
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event=None):
        if event and event.widget == self:
            for aid in self._after_ids[:]:
                try: self.after_cancel(aid)
                except Exception: pass
            self._after_ids.clear()

    def _safe_focus(self, widget):
        try:
            if self.winfo_exists() and widget and widget.winfo_exists():
                widget.focus()
        except: pass

    def _build_main_content(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=30, pady=(10, 30))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(0, weight=1)

        # --- LEFT: CUSTOMER LIST ---
        table_container = ctk.CTkFrame(content, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        table_container.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        header_row = ctk.CTkFrame(table_container, fg_color="#F8FAFC", corner_radius=0, height=50)
        header_row.pack(fill="x", pady=(15, 5), padx=2)
        header_row.pack_propagate(False)
        
        cols = [("Customer Name", 280), ("Total Paid", 100), ("Pending", 100), ("Total", 100), ("Action", 140)]
        for text, w in cols:
            ctk.CTkLabel(
                header_row, text=text, width=w,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#475569", anchor="w" if text != "Action" else "center"
            ).pack(side="left", padx=15)

        self.scroll_frame = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=2, pady=(0, 10))
        
        # --- RIGHT: SIDE PANEL (SCROLLABLE) ---
        self.side_panel = ctk.CTkScrollableFrame(content, fg_color="transparent", label_text="", width=420)
        self.side_panel.grid(row=0, column=1, sticky="nsew", padx=0)
        
        self._show_placeholder()
        self._refresh_customers()

    def _show_placeholder(self):
        for w in self.side_panel.winfo_children():
            w.destroy()
        
        ph = ctk.CTkFrame(self.side_panel, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0", height=600)
        ph.pack(fill="both", expand=True)
        ph.pack_propagate(False)
        
        ctk.CTkLabel(ph, text="No Customer Selected", font=ctk.CTkFont(size=16, weight="bold"), text_color="#94A3B8").pack(expand=True)
        ctk.CTkLabel(ph, text="Click 📜 Logs or 💳 Pay to view descriptive details.", font=ctk.CTkFont(size=13), text_color="#CBD5E1").pack(expand=True, pady=(0, 200))

    def _refresh_customers(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
            
        def fetch_data():
            return get_customer_payment_summary(self.user["distributor_id"])
            
        def on_success(result):
            customers = result

            query = self.search_entry.get().lower()
            if query:
                customers = [c for c in customers if query in c["shop_name"].lower()]

            for c in customers:
                row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=55)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)
                
                # Hover effect
                def on_enter(e, r=row): r.configure(fg_color="#F8FAFC")
                def on_leave(e, r=row): r.configure(fg_color="transparent")
                row.bind("<Enter>", on_enter)
                row.bind("<Leave>", on_leave)

                ctk.CTkLabel(row, text=c["shop_name"], width=280, anchor="w", font=ctk.CTkFont(size=14, weight="bold"), text_color="black").pack(side="left", padx=15)
                
                ctk.CTkLabel(row, text=f"₹{float(c['total_paid']):,.2f}", width=100, anchor="w", font=ctk.CTkFont(size=14), text_color="#10B981").pack(side="left", padx=15)
                
                balance = float(c['outstanding_balance'])
                balance_color = "#E11D48" if balance > 0 else "#10B981"
                ctk.CTkLabel(row, text=f"₹{balance:,.2f}", width=100, anchor="w", font=ctk.CTkFont(size=14, weight="bold"), text_color=balance_color).pack(side="left", padx=15)
                
                ctk.CTkLabel(row, text=f"₹{float(c['total_invoiced']):,.2f}", width=100, anchor="w", font=ctk.CTkFont(size=14), text_color="#1B4F6B").pack(side="left", padx=15)
                
                # Actions
                btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=180)
                btn_frame.pack(side="left", padx=15)
                # Logs Button
                ctk.CTkButton(
                    btn_frame, text="Logs", width=65, height=30,
                    fg_color="#F1F5F9", text_color="#475569", hover_color="#E2E8F0", corner_radius=8,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    command=lambda cust=c: self._update_panel(cust, "logs")
                ).pack(side="left", padx=(0, 5))
                
                # Pay Button
                ctk.CTkButton(
                    btn_frame, text="Pay", width=65, height=30,
                    fg_color="#1B4F6B", hover_color="#0F364A", corner_radius=8,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    command=lambda cust=c: self._update_panel(cust, "pay")
                ).pack(side="left")

                ctk.CTkFrame(self.scroll_frame, fg_color="#F1F5F9", height=1).pack(fill="x", padx=10)

        def on_error(e):
            print(f"Error loading customers: {e}")
            pass

        async_db_call(self, fetch_data, (), on_success, on_error)

    def _build_card(self, title, icon):
        card = ctk.CTkFrame(self.side_panel, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        card.pack(fill="x", pady=(0, 15))
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(header, text=f"{icon} {title}", font=ctk.CTkFont(size=15, weight="bold"), text_color="#1E293B").pack(side="left")
        return card

    def _update_panel(self, customer, mode):
        for w in self.side_panel.winfo_children():
            w.destroy()
            
        # 1. Summary Card
        summ_card = self._build_card("Financial Summary", "📊")
        pending = float(customer["outstanding_balance"])
        
        pb = ctk.CTkFrame(summ_card, fg_color="#FFF1F2", corner_radius=10)
        pb.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(pb, text=customer["shop_name"], font=ctk.CTkFont(size=14, weight="bold"), text_color="#1B4F6B").pack(pady=(10, 2))
        ctk.CTkLabel(pb, text=f"Pending: ₹{pending:,.2f}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#E11D48").pack(pady=(0, 10))

        for l, v, c in [("Total Invoiced", f"₹{float(customer['total_invoiced']):,.2f}", "#64748B"), ("Total Paid", f"₹{float(customer['total_paid']):,.2f}", "#10B981")]:
            f = ctk.CTkFrame(summ_card, fg_color="transparent")
            f.pack(fill="x", padx=25, pady=3)
            ctk.CTkLabel(f, text=l, font=ctk.CTkFont(size=12), text_color="#64748B").pack(side="left")
            ctk.CTkLabel(f, text=v, font=ctk.CTkFont(size=13, weight="bold"), text_color=c).pack(side="right")
        ctk.CTkFrame(summ_card, fg_color="transparent", height=10).pack()

        # 2. Invoice History Card (Always present for context)
        inv_card = self._build_card("Invoice History", "📄")
        self._render_invoice_history(customer, inv_card)

        # 3. Mode-specific Card
        if mode == "logs":
            log_card = self._build_card("Payment logs", "📜")
            self._render_payment_logs(customer, log_card)
        else:
            form_card = self._build_card("Record New Payment", "💸")
            self._render_payment_form(customer, form_card)

    def _render_invoice_history(self, customer, card):
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=15, pady=(0, 15))
        
        try:
            invoices = get_invoices_for_customer(customer["license_no"])
        except: invoices = []

        if not invoices:
            ctk.CTkLabel(container, text="No invoices found.", text_color="#94A3B8").pack(pady=10)
            return

        h = ctk.CTkFrame(container, fg_color="#F8FAFC", height=30)
        h.pack(fill="x", pady=5)
        for t, w in [("Inv No", 80), ("Date", 80), ("Status", 80)]:
            ctk.CTkLabel(h, text=t, width=w, font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748B").pack(side="left", padx=5)

        for inv in invoices[:5]: # Show last 5
            row = ctk.CTkFrame(container, fg_color="transparent", height=30)
            row.pack(fill="x")
            ctk.CTkLabel(row, text=inv["invoice_no"], width=80, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            dt = inv["invoice_date"]
            if hasattr(dt, "strftime"): dt = dt.strftime("%d/%m/%y")
            ctk.CTkLabel(row, text=dt, width=80, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            
            st = inv["status"]
            txt_c = "#059669" if st=="Paid" else "#D97706" if st=="Partial" else "#DC2626"
            ctk.CTkLabel(row, text=st, width=80, font=ctk.CTkFont(size=10, weight="bold"), text_color=txt_c).pack(side="left", padx=5)

    def _render_payment_logs(self, customer, card):
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=15, pady=(0, 15))
        
        try:
            payments = get_payment_history(customer["license_no"])
        except: payments = []

        if not payments:
            ctk.CTkLabel(container, text="No payments recorded.", text_color="#94A3B8").pack(pady=10)
            return

        for p in payments[:10]:
            row = ctk.CTkFrame(container, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            dt = p["payment_date"]
            if hasattr(dt, "strftime"): dt = dt.strftime("%b %d, %Y")
            
            l = ctk.CTkFrame(row, fg_color="transparent")
            l.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(l, text=dt, font=ctk.CTkFont(size=11), text_color="#64748B", anchor="w").pack(fill="x")
            ctk.CTkLabel(l, text=p["payment_mode"], font=ctk.CTkFont(size=10), text_color="#94A3B8", anchor="w").pack(fill="x")
            
            ctk.CTkLabel(row, text=f"₹{float(p['amount']):,.0f}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#10B981").pack(side="right", padx=5)
            ctk.CTkFrame(container, fg_color="#F1F5F9", height=1).pack(fill="x")

    def _render_payment_form(self, customer, card):
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(container, text="Amount", font=ctk.CTkFont(size=12, weight="bold"), text_color="#475569").pack(anchor="w")
        
        # Numeric validation
        vcmd = (self.register(self._validate_numeric), '%P')
        amt_entry = ctk.CTkEntry(
            container, placeholder_text="0.00", height=40, 
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#FFFFFF", border_color="#E2E8F0",
            validate='key', validatecommand=vcmd
        )
        amt_entry.pack(fill="x", pady=(2, 12))
        
        mode_var = ctk.StringVar(value="Cash")
        ctk.CTkOptionMenu(container, values=["Cash", "UPI", "Bank"], variable=mode_var, height=35, fg_color="#1B4F6B").pack(fill="x", pady=10)
        
        dt_entry = ctk.CTkEntry(
            container, height=35, fg_color="#FFFFFF", border_color="#E2E8F0",
            text_color="black"
        )
        dt_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        dt_entry.configure(state="readonly")
        dt_entry.pack(fill="x", pady=10)
        
        def do_submit():
            try:
                amt = float(amt_entry.get())
            except:
                messagebox.showerror("Error", "Invalid amount.")
                return
            if amt <= 0:
                messagebox.showerror("Error", "Amount > 0 required.")
                return
            out = float(customer["outstanding_balance"])
            if amt > out + 0.01:
                messagebox.showerror("Error", f"Exceeds pending ₹{out:,.2f}")
                return
            if not messagebox.askyesno("Confirm", f"Record ₹{amt:,.2f} for {customer['shop_name']}?"):
                return
            try:
                record_payment(self.user["distributor_id"], customer["license_no"], amt, mode_var.get(), dt_entry.get())
                messagebox.showinfo("Success", "Payment recorded.")
                self._refresh_customers()
                self._update_panel(customer, "logs") # Switch to logs to show result
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(container, text="Confirm Payment", height=45, fg_color="#10B981", font=ctk.CTkFont(weight="bold"), command=do_submit).pack(fill="x", pady=(10, 0))

    def _validate_numeric(self, P):
        if P == "" or P == ".":
            return True
        try:
            float(P)
            return True
        except ValueError:
            return False

    def _go_dashboard(self):
        self.app.switch_view("Dashboard")
