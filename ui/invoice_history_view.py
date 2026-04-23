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
from utils.async_db import async_db_call

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
        self._row_pool = []
        self._search_job = None
        self._after_ids = []
        
        self._build_ui()
        self._load_data()
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event=None):
        if event and event.widget == self:
            for aid in self._after_ids[:]:
                try: self.after_cancel(aid)
                except Exception: pass
            self._after_ids.clear()
            self._search_job = None

    def _schedule_search(self, event=None):
        if self._search_job:
            try: self.after_cancel(self._search_job)
            except Exception: pass
        self._search_job = self.after(400, self._load_data)
        self._after_ids.append(self._search_job)

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
        self.search_var.trace_add("write", lambda *args: self._schedule_search())
        
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
        for item in self._row_pool:
            item["frame"].pack_forget()

        if not hasattr(self, '_loading_lbl'):
            self._loading_lbl = ctk.CTkLabel(self.list_frame, text="Loading...", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self._loading_lbl.pack(pady=40)
        
        if hasattr(self, '_no_data_lbl') and self._no_data_lbl.winfo_exists():
            self._no_data_lbl.pack_forget()

        query = self.search_var.get().strip()
        
        async_db_call(
            self,
            search_invoice_history,
            (self.user["distributor_id"], query),
            success_callback=self._on_data_loaded,
            error_callback=lambda e: print("DB Error:", e)
        )

    def _on_data_loaded(self, invoices):
        if hasattr(self, '_loading_lbl') and self._loading_lbl.winfo_exists():
            self._loading_lbl.pack_forget()

        if not invoices:
            if not hasattr(self, '_no_data_lbl'):
                self._no_data_lbl = ctk.CTkLabel(self.list_frame, text="No matches.", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
            self._no_data_lbl.pack(pady=40)
            return

        while len(self._row_pool) < len(invoices):
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent", height=45)
            row.pack_propagate(False)

            labels = {}
            labels["invoice_no"] = ctk.CTkLabel(row, text="", width=80, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w")
            labels["invoice_no"].pack(side="left", padx=5)
            
            labels["customer_name"] = ctk.CTkLabel(row, text="", width=180, font=ctk.CTkFont(size=12), text_color=TEXT_DARK, anchor="w")
            labels["customer_name"].pack(side="left", padx=5)
            
            labels["date"] = ctk.CTkLabel(row, text="", width=100, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, anchor="w")
            labels["date"].pack(side="left", padx=5)
            
            labels["total"] = ctk.CTkLabel(row, text="", width=90, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w")
            labels["total"].pack(side="left", padx=5)

            badge_frame = ctk.CTkFrame(row, corner_radius=10, width=70, height=22)
            badge_frame.pack_propagate(False)
            badge_frame.pack(side="left", padx=5)
            badge_lbl = ctk.CTkLabel(badge_frame, text="", font=ctk.CTkFont(size=10, weight="bold"))
            badge_lbl.pack(expand=True)

            view_frame = ctk.CTkFrame(row, fg_color="transparent", width=50)
            view_frame.pack_propagate(False)
            view_frame.pack(side="left")

            view_btn = ctk.CTkButton(
                view_frame, text="      👁️", width=30, height=30, fg_color="#F1F5F9", hover_color="#E2E8F0",
                text_color=ACCENT, font=ctk.CTkFont(size=18), corner_radius=6, anchor="center"
            )
            view_btn.pack(expand=True)

            self._row_pool.append({
                "frame": row,
                "labels": labels,
                "badge_frame": badge_frame,
                "badge_lbl": badge_lbl,
                "view_btn": view_btn
            })

        for idx, inv in enumerate(invoices):
            pool_item = self._row_pool[idx]
            pool_item["frame"].pack(fill="x", pady=1)

            date_str = inv["invoice_date"]
            if hasattr(date_str, "strftime"):
                date_str = date_str.strftime("%b %d, %y")

            pool_item["labels"]["invoice_no"].configure(text=inv["invoice_no"])
            pool_item["labels"]["customer_name"].configure(text=inv["customer_name"][:20])
            pool_item["labels"]["date"].configure(text=date_str)
            pool_item["labels"]["total"].configure(text=f"₹{int(float(inv['grand_total'])):,}")

            status_text = "Paid" if inv["payment_type"] in ["Cash", "UPI"] else "Pending"
            status_color = SUCCESS if status_text == "Paid" else WARNING
            status_bg = "#D1FAE5" if status_text == "Paid" else "#FEF3C7"

            pool_item["badge_frame"].configure(fg_color=status_bg)
            pool_item["badge_lbl"].configure(text=status_text, text_color=status_color)

            pool_item["view_btn"].configure(command=lambda i=inv: self._view_invoice(i))

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
        self.app.switch_view("Dashboard")
