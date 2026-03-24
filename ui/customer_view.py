"""
Customer View — CustomTkinter frame for managing customers.
Features search and basic management actions.
"""

import customtkinter as ctk
from tkinter import messagebox
from models.customer import search_customers
from db.connection import execute_query

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
ENTRY_BG = "#FFFFFF"
SUCCESS = "#2DC653"
DANGER = "#EF233C"


class CustomerView(ctk.CTkFrame):
    """View to list, search, and manage customers."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref
        
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#212529", corner_radius=0, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=80, height=30,
            font=ctk.CTkFont(size=11), corner_radius=8,
            fg_color="#E9ECEF", hover_color="#CED4DA", text_color="#212529",
            command=self._go_back,
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top, text="🏪  Customer Management",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(15, 5))

        # Search
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search name, license or phone...",
            width=300, height=35, corner_radius=8, fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_WHITE
        )
        search_entry.pack(side="left", padx=(0, 10))
        search_entry.bind("<KeyRelease>", lambda e: self._load_data())

        # Add Customer Button
        ctk.CTkButton(
            toolbar, text="+ Add Customer", height=35, font=ctk.CTkFont(size=12, weight="bold"), 
            corner_radius=8, fg_color=SUCCESS, hover_color="#208B3A", text_color="#FFFFFF",
            command=self._add_customer
        ).pack(side="right")

        # ── Table Area ──
        table_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color=BORDER_CLR)
        table_container.pack(fill="both", expand=True, padx=15, pady=(10, 20))

        # Header
        header = ctk.CTkFrame(table_container, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        cols = [
            ("License No", 150), ("Shop Name", 250), ("Owner", 180), 
            ("Mobile", 120), ("GSTIN", 150), ("Actions", 100)
        ]
        
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#4B5563", anchor="w" if text != "Actions" else "center"
            ).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_data(self):
        query = self.search_var.get().strip()
        try:
            customers = search_customers(self.user["distributor_id"], query)
        except Exception as e:
            customers = []
            print(f"Error loading customers: {e}")

        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not customers:
            ctk.CTkLabel(self.scroll, text="No active customers found.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        cols = [("license_no", 150), ("shop_name", 250), ("license_holder_name", 180), ("mobile_no", 120), ("gst_no", 150)]

        for row in customers:
            frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
            frame.pack(fill="x", pady=2)
            frame.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color="#F3F4F6", height=1).pack(fill="x", padx=10)

            for key, w in cols:
                val = str(row.get(key) or "N/A")[:30]
                ctk.CTkLabel(
                    frame, text=val, width=w, font=ctk.CTkFont(size=12),
                    text_color=TEXT_WHITE, anchor="w"
                ).pack(side="left", padx=5)

            # Actions
            action_frame = ctk.CTkFrame(frame, width=100, fg_color="transparent")
            action_frame.pack_propagate(False)
            action_frame.pack(side="left", padx=5, pady=5)
            
            ctk.CTkButton(
                action_frame, text="Deactivate", width=80, height=28,
                font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6,
                fg_color="#FEE2E2", hover_color="#FECACA", text_color="#991B1B",
                command=lambda l=row["license_no"]: self._delete_customer(l)
            ).pack(expand=True)

    def _delete_customer(self, license_no):
        if messagebox.askyesno("Confirm", f"Are you sure you want to deactivate customer {license_no}?"):
            try:
                execute_query("UPDATE customers SET status = 'inactive' WHERE license_no = %s", (license_no,))
                messagebox.showinfo("Success", "Customer deactivated.")
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete customer: {e}")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
        
    def _add_customer(self):
        from ui.add_party_form import AddPartyForm
        for widget in self.master.winfo_children():
            widget.destroy()
        form = AddPartyForm(self.master, self.user, self.app)
        form.pack(fill="both", expand=True)
