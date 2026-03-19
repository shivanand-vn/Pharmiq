"""
Invoice Preview — Dialog for viewing generated invoice PDF.
"""

import customtkinter as ctk
from tkinter import messagebox
import os

from services.pdf_generator import open_pdf, print_pdf


class InvoicePreview(ctk.CTkToplevel):
    """Preview dialog showing invoice PDF path with Open/Print buttons."""

    def __init__(self, master, invoice, pdf_path):
        super().__init__(master)
        self.invoice = invoice
        self.pdf_path = pdf_path

        self.title(f"Invoice {invoice.get('invoice_no', '')} — Preview")
        self.geometry("500x350")
        self.resizable(False, False)
        self.configure(fg_color="#0f0f1a")

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 350) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="🧾 Invoice Generated Successfully!",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#00d4ff",
        ).pack(pady=12)

        # Info card
        card = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=12,
                             border_width=1, border_color="#2a2a4a")
        card.pack(padx=20, pady=15, fill="both", expand=True)

        details = [
            ("Invoice No:", self.invoice.get("invoice_no", "")),
            ("Date:", str(self.invoice.get("invoice_date", ""))),
            ("Grand Total:", f"₹ {float(self.invoice.get('grand_total', 0)):,.2f}"),
            ("Payment:", self.invoice.get("payment_type", "")),
            ("PDF File:", os.path.basename(self.pdf_path) if self.pdf_path else "N/A"),
        ]

        for label, value in details:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11),
                          text_color="#888899", width=100, anchor="e").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=11, weight="bold"),
                          text_color="#ffffff", anchor="w").pack(side="left", padx=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="📂  Open PDF", height=40, width=140,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
            fg_color="#00d4ff", hover_color="#00a8cc", text_color="#0f0f1a",
            command=self._open,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🖨️  Print", height=40, width=100,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
            fg_color="#6c5ce7", hover_color="#5a4bd1",
            command=self._print,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Close", height=40, width=80,
            font=ctk.CTkFont(size=12), corner_radius=10,
            fg_color="#333355", hover_color="#444466",
            command=self.destroy,
        ).pack(side="right", padx=5)

    def _open(self):
        try:
            open_pdf(self.pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open PDF:\n{e}")

    def _print(self):
        try:
            print_pdf(self.pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot print:\n{e}")
