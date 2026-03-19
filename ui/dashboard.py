"""
Dashboard — Main window after login with distributor branding.
"""

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image as PILImage
import os

from models.distributor import get_distributor_by_id
from models.invoice import get_invoices_by_distributor


class Dashboard(ctk.CTkFrame):
    """Main dashboard frame showing distributor branding and navigation."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color="#0f0f1a")
        self.user = user_context
        self.app = app_ref
        self.distributor = get_distributor_by_id(self.user["distributor_id"])

        self._build_ui()

    def _build_ui(self):
        # ══════════════════════════════════════════════
        # TOP BAR: Branding
        # ══════════════════════════════════════════════
        top_bar = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0, height=70)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=15)

        logo_path = self.distributor.get("logo_path") if self.distributor else None
        if logo_path and os.path.exists(logo_path):
            try:
                img = PILImage.open(logo_path)
                logo_img = ctk.CTkImage(light_image=img, size=(45, 45))
                ctk.CTkLabel(logo_frame, image=logo_img, text="").pack(side="left", padx=(0, 10))
            except Exception:
                pass

        dist_name = self.distributor.get("name", "PharmIQ") if self.distributor else "PharmIQ"
        ctk.CTkLabel(
            logo_frame, text=f"💊 {dist_name}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#00d4ff",
        ).pack(side="left")

        # User info (right)
        user_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        user_frame.pack(side="right", padx=15)
        ctk.CTkLabel(
            user_frame, text=f"👤 {self.user.get('username', '')}",
            font=ctk.CTkFont(size=13), text_color="#aabbcc",
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            user_frame, text="Logout", width=70, height=30,
            font=ctk.CTkFont(size=11), corner_radius=8,
            fg_color="#333355", hover_color="#444466",
            command=self._logout,
        ).pack(side="left")

        # ══════════════════════════════════════════════
        # MAIN CONTENT
        # ══════════════════════════════════════════════
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # ── Welcome section ──
        welcome = ctk.CTkFrame(content, fg_color="#16213e", corner_radius=16,
                                border_width=1, border_color="#2a2a4a")
        welcome.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            welcome, text=f"Welcome to {dist_name}",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#ffffff",
        ).pack(pady=(20, 5), padx=20, anchor="w")

        dist_info = ""
        if self.distributor:
            if self.distributor.get("address"):
                dist_info += f"📍 {self.distributor['address']}\n"
            if self.distributor.get("gst_no"):
                dist_info += f"🏛️ GSTIN: {self.distributor['gst_no']}    "
            if self.distributor.get("drug_license_no"):
                dist_info += f"📋 D.L. No: {self.distributor['drug_license_no']}"

        if dist_info:
            ctk.CTkLabel(
                welcome, text=dist_info,
                font=ctk.CTkFont(size=11), text_color="#7788aa",
                justify="left",
            ).pack(pady=(0, 15), padx=20, anchor="w")

        # ── Action buttons ──
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))

        buttons = [
            ("📝  New Invoice", "#00d4ff", "#00a8cc", self._new_invoice),
            ("📋  Invoice History", "#6c5ce7", "#5a4bd1", self._show_history),
            ("📊  Reports", "#00b894", "#00a381", self._show_reports),
        ]

        for i, (text, fg, hover, cmd) in enumerate(buttons):
            btn = ctk.CTkButton(
                btn_frame, text=text, height=55, width=200,
                font=ctk.CTkFont(size=14, weight="bold"), corner_radius=12,
                fg_color=fg, hover_color=hover, text_color="#ffffff",
                command=cmd,
            )
            btn.grid(row=0, column=i, padx=8, sticky="ew")
        btn_frame.columnconfigure((0, 1, 2), weight=1)

        # ── Recent invoices ──
        recent_frame = ctk.CTkFrame(content, fg_color="#16213e", corner_radius=16,
                                     border_width=1, border_color="#2a2a4a")
        recent_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            recent_frame, text="📄 Recent Invoices",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffffff",
        ).pack(pady=(15, 10), padx=15, anchor="w")

        self.invoices_scroll = ctk.CTkScrollableFrame(
            recent_frame, fg_color="transparent",
        )
        self.invoices_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._load_recent_invoices()

    def _load_recent_invoices(self):
        """Load and display recent invoices."""
        for widget in self.invoices_scroll.winfo_children():
            widget.destroy()

        try:
            invoices = get_invoices_by_distributor(self.user["distributor_id"], limit=20)
        except Exception:
            invoices = []

        if not invoices:
            ctk.CTkLabel(
                self.invoices_scroll, text="No invoices yet. Click 'New Invoice' to create one!",
                font=ctk.CTkFont(size=12), text_color="#666688",
            ).pack(pady=30)
            return

        # Header
        header = ctk.CTkFrame(self.invoices_scroll, fg_color="#1a1a2e", corner_radius=8, height=35)
        header.pack(fill="x", pady=(0, 5))
        header.pack_propagate(False)
        cols = [("Invoice No", 0.15), ("Date", 0.15), ("Customer", 0.35),
                ("Amount", 0.15), ("Payment", 0.10), ("Action", 0.10)]
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#aabbcc",
            ).pack(side="left", expand=True)

        # Rows
        for inv in invoices:
            row = ctk.CTkFrame(self.invoices_scroll, fg_color="#0f0f1a", corner_radius=6, height=32)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            inv_date = inv.get("invoice_date", "")
            if hasattr(inv_date, "strftime"):
                inv_date = inv_date.strftime("%d/%m/%Y")

            vals = [
                str(inv.get("invoice_no", "")),
                str(inv_date),
                str(inv.get("customer_name", ""))[:30],
                f"₹{float(inv.get('grand_total', 0)):,.2f}",
                str(inv.get("payment_type", "")),
            ]
            for v in vals:
                ctk.CTkLabel(
                    row, text=v, font=ctk.CTkFont(size=10), text_color="#ccccdd",
                ).pack(side="left", expand=True)

            # View PDF button
            inv_id = inv.get("invoice_id")
            ctk.CTkButton(
                row, text="PDF", width=40, height=24,
                font=ctk.CTkFont(size=10), corner_radius=6,
                fg_color="#333355", hover_color="#444466",
                command=lambda iid=inv_id: self._view_invoice_pdf(iid),
            ).pack(side="left", padx=5)

    def _new_invoice(self):
        """Open the invoice creation form."""
        from ui.invoice_form import InvoiceForm
        # Clear content and show form
        for widget in self.winfo_children():
            widget.destroy()
        form = InvoiceForm(self, self.user, self.distributor, self.app)
        form.pack(fill="both", expand=True)

    def _show_history(self):
        messagebox.showinfo("Invoice History", "Invoice history view coming soon!")

    def _show_reports(self):
        messagebox.showinfo("Reports", "Reports module coming soon!")

    def _view_invoice_pdf(self, invoice_id):
        """Generate and open PDF for an existing invoice."""
        from models.invoice import get_invoice
        from models.customer import get_customer_by_license
        from services.pdf_generator import generate_invoice_pdf, open_pdf

        try:
            invoice = get_invoice(invoice_id)
            if not invoice:
                messagebox.showerror("Error", "Invoice not found.")
                return
            customer = get_customer_by_license(invoice["customer_license_no"])
            pdf_path = generate_invoice_pdf(invoice, self.distributor, customer)
            open_pdf(pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")

    def _logout(self):
        """Handle logout."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.show_login()
