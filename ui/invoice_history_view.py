"""
Invoice History View — Modern side-by-side dashboard for browsing and previewing invoices.
Includes an embedded live PDF previewer.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from models.invoice import search_invoice_history, get_invoice
from models.customer import get_customer_by_license
from models.distributor import get_distributor_by_id
from ui.invoice_preview import InvoicePreviewFrame
from services.pdf_generator import generate_invoice_pdf

# -- Constants --
BG_MAIN = "#F1F5F9"
CARD_BG = "#FFFFFF"
ACCENT = "#1B4F6B"
TEXT_DARK = "#1E293B"
TEXT_MUTED = "#64748B"
BORDER_CLR = "#CBD5E1"
SUCCESS = "#10B981"
WARNING = "#F59E0B"


class InvoiceHistoryView(ctk.CTkFrame):
    """Modern dashboard with split-pane layout: List on left, Embedded Preview on right."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_MAIN)
        self.user = user_context
        self.app = app_ref
        self.current_preview = None
        
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── Top Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color=CARD_BG, height=60, corner_radius=0)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        # Back Button
        ctk.CTkButton(
            toolbar, text="← Back", width=80, height=32,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color=TEXT_DARK,
            command=self._go_back
        ).pack(side="left", padx=20)

        title_lbl = ctk.CTkLabel(
            toolbar, text="📜  Invoice History",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT
        )
        title_lbl.pack(side="left", padx=10)

        # Search Bar
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._load_data())
        
        search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="🔍 Search No, Customer, GST...",
            width=300, height=36, corner_radius=18, border_width=1, border_color=BORDER_CLR,
            fg_color="#F8FAFC", text_color=TEXT_DARK, textvariable=self.search_var
        )
        search_entry.pack(side="right", padx=25)

        # ── Main Content Split Area ──
        self.main_split = ctk.CTkFrame(self, fg_color="transparent")
        self.main_split.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. Left Panel: Invoice List (compact)
        self.left_panel = ctk.CTkFrame(self.main_split, fg_color=CARD_BG, corner_radius=12)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Table Header (Compressed)
        header = ctk.CTkFrame(self.left_panel, fg_color="#F1F5F9", height=40, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Reduced widths for side-by-side
        self.cols = [
            ("Inv No", 80), ("Customer", 180), ("Date", 100), 
            ("Total", 90), ("Status", 80), ("View", 50)
        ]

        for text, w in self.cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text != "View" else "center"
            ).pack(side="left", padx=5)

        # Scrollable List
        self.list_frame = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. Right Panel: Embedded Preview
        self.right_panel = ctk.CTkFrame(self.main_split, fg_color=CARD_BG, corner_radius=12, width=750)
        self.right_panel.pack(side="left", fill="both", expand=False)
        self.right_panel.pack_propagate(False)
        
        # Placeholder for preview
        self.preview_placeholder = ctk.CTkLabel(
            self.right_panel, text="Select an invoice to view preview 📄",
            font=ctk.CTkFont(size=14), text_color=TEXT_MUTED
        )
        self.preview_placeholder.pack(expand=True)

    def _load_data(self):
        """Fetch invoices based on search query."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().strip()
        try:
            invoices = search_invoice_history(self.user["distributor_id"], query)
        except Exception as e:
            print("DB Error:", e)
            invoices = []

        if not invoices:
            ctk.CTkLabel(
                self.list_frame, text="No matches.",
                font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
            ).pack(pady=40)
            return

        for inv in invoices:
            self._create_row(inv)

    def _create_row(self, inv):
        row = ctk.CTkFrame(self.list_frame, fg_color="transparent", height=45)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        date_str = inv["invoice_date"]
        if hasattr(date_str, "strftime"):
             date_str = date_str.strftime("%b %d, %y")

        status_text = "Paid" if inv["payment_type"] in ["Cash", "UPI"] else "Pending"
        status_color = SUCCESS if status_text == "Paid" else WARNING
        status_bg = "#D1FAE5" if status_text == "Paid" else "#FEF3C7"

        # Content Row - Compact
        ctk.CTkLabel(row, text=inv["invoice_no"], width=80, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=inv["customer_name"][:20], width=180, font=ctk.CTkFont(size=12), text_color=TEXT_DARK, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=date_str, width=100, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"₹{int(float(inv['grand_total'])):,}", width=90, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(side="left", padx=5)
        
        # Status Badge
        badge = ctk.CTkFrame(row, fg_color=status_bg, corner_radius=10, width=70, height=22)
        badge.pack_propagate(False)
        badge.pack(side="left", padx=5)
        ctk.CTkLabel(badge, text=status_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=status_color).pack(expand=True)

        # View Button
        view_frame = ctk.CTkFrame(row, fg_color="transparent", width=50)
        view_frame.pack_propagate(False)
        view_frame.pack(side="left")

        view_btn = ctk.CTkButton(
            view_frame, text="      👁️", width=30, height=30, fg_color="#F1F5F9", hover_color="#E2E8F0",
            text_color=ACCENT, font=ctk.CTkFont(size=18), corner_radius=6,
            command=lambda i=inv: self._view_invoice(i), anchor="center"
        )
        view_btn.pack(expand=True)

    def _view_invoice(self, inv_meta):
        """Update the right panel with the invoice preview."""
        try:
            # Clear previous preview or placeholder
            for widget in self.right_panel.winfo_children():
                widget.destroy()

            invoice = get_invoice(inv_meta["invoice_no"])
            customer = get_customer_by_license(inv_meta["license_no"])
            distributor = get_distributor_by_id(self.user["distributor_id"])
            
            # Re-generate/Path the PDF
            pdf_path = generate_invoice_pdf(invoice, distributor, customer)
            
            # Create the embedded frame
            self.current_preview = InvoicePreviewFrame(
                self.right_panel, invoice, pdf_path, 
                fg_color="transparent", corner_radius=12
            )
            self.current_preview.pack(fill="both", expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preview:\n{e}")

    def _go_back(self):
        """Redirect back to primary dashboard."""
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        Dashboard(self.master, self.user, self.app).pack(fill="both", expand=True)
