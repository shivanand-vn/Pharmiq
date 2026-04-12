"""
Returns View — Specialized module for processing customer returns against specific invoices.
Strictly enforces expiry and quantity validation.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from models.returns import get_returnable_invoice, create_return

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
WARNING = "#F59E0B"
DANGER = "#EF4444"


class ReturnsView(ctk.CTkFrame):
    """Integrated Returns Module with strict validation."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref
        
        self.current_invoice = None
        self.item_rows = []  # List of row data for validation and calculation

        self._build_ui()

    def _build_ui(self):
        # -- Top bar --
        top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=60, border_width=1, border_color=BORDER_CLR)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=80, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            top, text="↩️  Process Customer Return",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # -- Search & Invoice Meta Section --
        search_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_CLR)
        search_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(search_frame, text="Select Invoice:", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(side="left", padx=(20, 10), pady=20)
        
        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Enter Invoice No (e.g. I_001)...",
            width=300, height=40, font=ctk.CTkFont(size=13),
            fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK
        )
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<Return>", lambda e: self._search_invoice())

        ctk.CTkButton(
            search_frame, text="🔍 Fetch Items", width=140, height=40,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF",
            command=self._search_invoice
        ).pack(side="left", padx=10)

        self.info_lbl = ctk.CTkLabel(search_frame, text="Please search an invoice to begin", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED)
        self.info_lbl.pack(side="right", padx=20)

        # -- Items Table Area --
        self.table_container = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_CLR)
        self.table_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Header
        header = ctk.CTkFrame(self.table_container, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=15)
        header.pack_propagate(False)

        cols = [
            ("Medicine Name", 240), ("Batch", 100), ("Sold", 60), ("Already Ret.", 90), ("Expiry", 100), ("Return Qty", 80), ("Status", 150)
        ]
        for text, w in cols:
            ctk.CTkLabel(header, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED, anchor="w").pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # -- Bottom Summary & Finalize --
        self.bottom_bar = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=80, border_width=1, border_color=BORDER_CLR)
        self.bottom_bar.pack(fill="x", side="bottom")
        self.bottom_bar.pack_propagate(False)

        self.refund_lbl = ctk.CTkLabel(self.bottom_bar, text="Total Refund: ₹ 0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color=SUCCESS)
        self.refund_lbl.pack(side="left", padx=40)

        self.submit_btn = ctk.CTkButton(
            self.bottom_bar, text="Process Return ✅", width=240, height=45,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            fg_color=SUCCESS, hover_color="#059669", text_color="#FFFFFF",
            state="disabled",
            command=self._confirm_return
        )
        self.submit_btn.pack(side="right", padx=40)

    def _search_invoice(self):
        inv_no = self.search_entry.get().strip()
        if not inv_no: return

        try:
            data = get_returnable_invoice(inv_no, self.user["distributor_id"])
            if not data:
                messagebox.showerror("Not Found", f"Invoice '{inv_no}' not found for this account.")
                return

            self.current_invoice = data
            self.info_lbl.configure(text=f"🏥 {data['shop_name']} | 📅 {data['invoice_date']}", text_color=TEXT_DARK)
            self._load_items()
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    def _load_items(self):
        for widget in self.scroll.winfo_children(): widget.destroy()
        self.item_rows = []
        today = date.today()

        for item in self.current_invoice['items']:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            # Policy calculations
            exp_date = item['expiry_date']
            is_expired = exp_date <= today
            max_returnable = item['sold_qty'] - item['returned_quantity']
            
            # Styling for expired items
            if is_expired: row.configure(fg_color="#FFF5F5")

            # Columns
            ctk.CTkLabel(row, text=str(item['product_name'])[:30], width=240, font=ctk.CTkFont(size=11), text_color=TEXT_DARK, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=item['batch_no'], width=100, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(item['sold_qty']), width=60, font=ctk.CTkFont(size=11), text_color=TEXT_DARK).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(item['returned_quantity']), width=90, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left", padx=5)
            
            exp_str = exp_date.strftime("%d-%m-%Y")
            ctk.CTkLabel(row, text=exp_str, width=100, font=ctk.CTkFont(size=11, weight="bold" if is_expired else "normal"), 
                         text_color=DANGER if is_expired else TEXT_DARK).pack(side="left", padx=5)

            # Return Input
            qty_var = ctk.StringVar(value="0")
            qty_entry = ctk.CTkEntry(row, width=80, height=28, textvariable=qty_var, font=ctk.CTkFont(size=11), fg_color="#FFFFFF", border_color=BORDER_CLR)
            qty_entry.pack(side="left", padx=5)
            
            status_text = "Return Allowed"
            status_color = SUCCESS
            
            if is_expired:
                qty_entry.configure(state="disabled", fg_color="#F3F4F6")
                status_text = "Expired – Blocked"
                status_color = DANGER
            elif max_returnable <= 0:
                qty_entry.configure(state="disabled", fg_color="#F3F4F6")
                status_text = "Max Returned Reached"
                status_color = WARNING
            
            ctk.CTkLabel(row, text=status_text, width=150, font=ctk.CTkFont(size=10, weight="bold"), text_color=status_color).pack(side="left", padx=5)

            self.item_rows.append({
                "item": item,
                "qty_var": qty_var,
                "max": max_returnable,
                "expired": is_expired
            })
            
            qty_var.trace_add("write", lambda *args: self._update_refund())

        self.submit_btn.configure(state="normal" if self.item_rows else "disabled")

    def _update_refund(self):
        total = 0.0
        for row in self.item_rows:
            try:
                if row['expired']: continue
                qty = int(row['qty_var'].get() or 0)
                if 0 < qty <= row['max']:
                    total += qty * float(row['item']['trp'])
            except ValueError: pass
        self.refund_lbl.configure(text=f"Total Refund: ₹ {total:,.2f}")

    def _confirm_return(self):
        final_items = []
        total_refund = 0.0
        
        for row in self.item_rows:
            try:
                qty_str = row['qty_var'].get().strip()
                if not qty_str or qty_str == "0": continue
                
                qty = int(qty_str)
                if qty < 0: raise ValueError
                
                if qty > row['max']:
                    messagebox.showerror("Error", f"Quantity for {row['item']['product_name']} exceeds balance ({row['max']}).")
                    return
                
                if qty > 0:
                    refund = qty * float(row['item']['trp'])
                    final_items.append({
                        "invoice_item_id": row['item']['item_id'],
                        "batch_id": row['item']['batch_id'],
                        "quantity": qty,
                        "refund_amount": refund
                    })
                    total_refund += refund
            except ValueError:
                messagebox.showerror("Invalid Input", f"Please enter a valid number for {row['item']['product_name']}.")
                return

        if not final_items:
            messagebox.showwarning("Empty Return", "No items selected for return.")
            return

        msg = f"Process return for {len(final_items)} items?\n\nTotal Refund: ₹ {total_refund:,.2f}\n\nStrict stock & invoice records will be updated."
        if not messagebox.askyesno("Confirm Return", msg): return

        try:
            return_data = {
                "invoice_no": self.current_invoice['invoice_no'],
                "customer_license_no": self.current_invoice['customer_license_no'],
                "user_id": self.user['user_id'],
                "return_date": date.today().strftime("%Y-%m-%d"),
                "total_refund": total_refund
            }
            create_return(return_data, final_items)
            messagebox.showinfo("Success", f"Return successfully processed.\nRefund amount: ₹ {total_refund:,.2f}")
            self._search_invoice()  # Refresh state
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process return: {e}")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children(): widget.destroy()
        Dashboard(self.master, self.user, self.app).pack(fill="both", expand=True)
