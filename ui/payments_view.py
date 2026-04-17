"""
Payments View — Streamlined Customer Payments with Dynamic Sidebar.
All actions (Logs & Payment) happen on a single page.
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
        self._build_main_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=70)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(15, 5))
        header.pack_propagate(False)

        ctk.CTkButton(
            header, text="← Back", width=80, height=35,
            fg_color="transparent", text_color="#1B4F6B", border_width=1, border_color="#1B4F6B",
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

    def _build_main_content(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=30, pady=(10, 30))
        content.columnconfigure(0, weight=65) # Table
        content.columnconfigure(1, weight=35) # Side Panel
        content.rowconfigure(0, weight=1)

        # --- LEFT: CUSTOMER LIST ---
        table_container = ctk.CTkFrame(content, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        table_container.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        header_row = ctk.CTkFrame(table_container, fg_color="#F8FAFC", corner_radius=0, height=50)
        header_row.pack(fill="x", pady=(15, 5), padx=2)
        header_row.pack_propagate(False)
        
        cols = [("Customer Name", 280), ("Pending", 140), ("Action", 180)]
        for text, w in cols:
            ctk.CTkLabel(
                header_row, text=text, width=w,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#475569", anchor="w" if text != "Action" else "center"
            ).pack(side="left", padx=15)

        self.scroll_frame = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=2, pady=(0, 10))
        
        # --- RIGHT: SIDE PANEL ---
        self.side_panel = ctk.CTkFrame(content, fg_color="transparent")
        self.side_panel.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
        self._show_placeholder()
        self._refresh_customers()

    def _show_placeholder(self):
        for w in self.side_panel.winfo_children():
            w.destroy()
        
        ph = ctk.CTkFrame(self.side_panel, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        ph.pack(fill="both", expand=True)
        
        ctk.CTkLabel(ph, text="No Customer Selected", font=ctk.CTkFont(size=16, weight="bold"), text_color="#94A3B8").pack(expand=True)
        ctk.CTkLabel(ph, text="Click 📜 Logs or 💳 Pay to view details.", font=ctk.CTkFont(size=13), text_color="#CBD5E1").pack(expand=True, pady=(0, 100))

    def _refresh_customers(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
            
        try:
            customers = get_customer_payment_summary(self.user["distributor_id"])
        except:
            customers = []

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

            ctk.CTkLabel(row, text=c["shop_name"], width=280, anchor="w", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=15)
            
            balance = float(c['outstanding_balance'])
            balance_color = "#E11D48" if balance > 0 else "#10B981"
            ctk.CTkLabel(row, text=f"₹{balance:,.2f}", width=140, anchor="w", font=ctk.CTkFont(size=14, weight="bold"), text_color=balance_color).pack(side="left", padx=15)
            
            # Actions
            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=180)
            btn_frame.pack(side="left", padx=15)
            
            # Logs Button
            ctk.CTkButton(
                btn_frame, text="📜 Logs", width=80, height=30,
                fg_color="#F1F5F9", text_color="#475569", hover_color="#E2E8F0", corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda cust=c: self._update_panel(cust, "logs")
            ).pack(side="left", padx=(0, 5))
            
            # Pay Button
            ctk.CTkButton(
                btn_frame, text="💳 Pay", width=80, height=30,
                fg_color="#1B4F6B", hover_color="#0F364A", corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda cust=c: self._update_panel(cust, "pay")
            ).pack(side="left")

            ctk.CTkFrame(self.scroll_frame, fg_color="#F1F5F9", height=1).pack(fill="x", padx=10)

    def _update_panel(self, customer, mode):
        for w in self.side_panel.winfo_children():
            w.destroy()
            
        main_card = ctk.CTkFrame(self.side_panel, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#E2E8F0")
        main_card.pack(fill="both", expand=True)
        
        # Header / Mini-Summary
        header = ctk.CTkFrame(main_card, fg_color="#F8FAFC", corner_radius=12)
        header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(header, text=customer["shop_name"], font=ctk.CTkFont(size=16, weight="bold"), text_color="#1B4F6B").pack(anchor="w", padx=15, pady=(10, 2))
        
        pending = float(customer["outstanding_balance"])
        ctk.CTkLabel(header, text=f"Pending: ₹{pending:,.2f}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#E11D48" if pending > 0 else "#10B981").pack(anchor="w", padx=15, pady=(0, 10))

        if mode == "logs":
            self._render_logs_view(customer, main_card)
        else:
            self._render_pay_view(customer, main_card)

    def _render_logs_view(self, customer, container):
        ctk.CTkLabel(container, text="Payment History", font=ctk.CTkFont(size=14, weight="bold"), text_color="#64748B").pack(anchor="w", padx=20, pady=(5, 10))
        
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        
        try:
            payments = get_payment_history(customer["license_no"])
        except:
            payments = []
            
        if not payments:
            ctk.CTkLabel(scroll, text="No payment history.", text_color="#94A3B8").pack(pady=40)
            return

        for p in payments:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            dt = p["payment_date"]
            if hasattr(dt, "strftime"): dt = dt.strftime("%b %d, %Y")
            
            l_frame = ctk.CTkFrame(row, fg_color="transparent")
            l_frame.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(l_frame, text=dt, font=ctk.CTkFont(size=12), text_color="#64748B", anchor="w").pack(fill="x")
            ctk.CTkLabel(l_frame, text=p["payment_mode"], font=ctk.CTkFont(size=11), text_color="#94A3B8", anchor="w").pack(fill="x")
            
            ctk.CTkLabel(row, text=f"₹{float(p['amount']):,.2f}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10B981").pack(side="right", padx=10)
            ctk.CTkFrame(scroll, fg_color="#F1F5F9", height=1).pack(fill="x")

    def _render_pay_view(self, customer, container):
        ctk.CTkLabel(container, text="Record New Payment", font=ctk.CTkFont(size=14, weight="bold"), text_color="#64748B").pack(anchor="w", padx=20, pady=(5, 15))
        
        form_frame = ctk.CTkFrame(container, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20)
        
        ctk.CTkLabel(form_frame, text="Payment Amount", font=ctk.CTkFont(size=13, weight="bold"), text_color="#475569").pack(anchor="w")
        amt_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00", height=45, font=ctk.CTkFont(size=18, weight="bold"), corner_radius=8)
        amt_entry.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(form_frame, text="Payment Mode", font=ctk.CTkFont(size=13, weight="bold"), text_color="#475569").pack(anchor="w")
        mode_var = ctk.StringVar(value="Cash")
        mode_opt = ctk.CTkOptionMenu(form_frame, values=["Cash", "UPI", "Bank Transaction"], variable=mode_var, height=40, corner_radius=8, fg_color="#1B4F6B", button_color="#13415A")
        mode_opt.pack(fill="x", pady=(5, 20))
        
        ctk.CTkLabel(form_frame, text="Transaction Date", font=ctk.CTkFont(size=13, weight="bold"), text_color="#475569").pack(anchor="w")
        date_entry = ctk.CTkEntry(form_frame, height=40, corner_radius=8)
        date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        date_entry.pack(fill="x", pady=(5, 30))
        
        def do_submit():
            try:
                amount = float(amt_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid amount.")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be > 0.")
                return
                
            outstanding = float(customer["outstanding_balance"])
            if amount > outstanding + 0.01:
                messagebox.showerror("Error", f"Amount exceeds pending ₹{outstanding:,.2f}")
                return
            
            # Warning
            if not messagebox.askyesno("Confirm", f"Record payment of ₹{amount:,.2f} for {customer['shop_name']}?"):
                return

            try:
                record_payment(
                    distributor_id=self.user["distributor_id"],
                    customer_license_no=customer["license_no"],
                    amount=amount,
                    mode=mode_var.get(),
                    date=date_entry.get()
                )
                messagebox.showinfo("Success", "Payment recorded.")
                # Refresh everything
                self._refresh_customers()
                self._show_placeholder()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(
            form_frame, text="Record Payment", height=50,
            fg_color="#10B981", hover_color="#059669", corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=do_submit
        ).pack(fill="x", pady=(0, 20))

    def _go_dashboard(self):
        from ui.dashboard import Dashboard
        for w in self.master.winfo_children():
            w.destroy()
        view = Dashboard(self.master, self.user, self.app)
        view.pack(fill="both", expand=True)
