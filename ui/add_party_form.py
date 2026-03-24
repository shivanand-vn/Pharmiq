"""
Add Party Form — CustomTkinter form for adding a new customer (party).
"""

import customtkinter as ctk
from tkinter import messagebox
from db.connection import execute_query

# ── Colour palette ──
BG_DARK = "#F8F9FA"
CARD_BG = "#212529"
BORDER_CLR = "#DEE2E6"
ACCENT = "#4361EE"
ACCENT_HOVER = "#3A0CA3"
TEXT_WHITE = "#212529"
TEXT_MUTED = "#868E96"
ENTRY_BG = "#F8F9FA"
SUCCESS = "#2DC653"


class AddPartyForm(ctk.CTkFrame):
    """Form to add a new customer (party)."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self._build_ui()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#212529", corner_radius=0, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=80, height=30,
            font=ctk.CTkFont(size=11), corner_radius=8,
            fg_color="#E9ECEF", hover_color="#CED4DA",
            command=self._go_back,
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top, text="👥  Add New Party (Customer)",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Form Content ──
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_CLR)
        card.pack(fill="x", padx=10, pady=20)

        # Helper for fields
        def add_entry(parent, label_text, placeholder=""):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row, text=label_text, width=150, anchor="w",
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left")
            entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=35,
                                 font=ctk.CTkFont(size=12), fg_color=ENTRY_BG,
                                 border_color=BORDER_CLR, text_color=TEXT_WHITE)
            entry.pack(side="left", fill="x", expand=True)
            return entry

        self.license_entry = add_entry(card, "License No. (Required)", "e.g. KA-DW-1234")
        self.shop_name_entry = add_entry(card, "Shop Name (Required)")
        self.owner_name_entry = add_entry(card, "Owner / Holder Name")
        self.mobile_entry = add_entry(card, "Mobile Number")
        self.gst_entry = add_entry(card, "GST Number")
        self.email_entry = add_entry(card, "Email Address")
        self.address_entry = add_entry(card, "Full Address")

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame, text="✅  Save Customer", height=45, width=200,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            fg_color=SUCCESS, hover_color="#208B3A", text_color=TEXT_WHITE,
            command=self._save_customer,
        ).pack(side="left", padx=5)

    def _save_customer(self):
        license_no = self.license_entry.get().strip()
        shop_name = self.shop_name_entry.get().strip()

        if not license_no or not shop_name:
            messagebox.showwarning("Incomplete", "License No. and Shop Name are required.")
            return

        try:
            query = """
                INSERT INTO customers 
                (license_no, distributor_id, shop_name, license_holder_name, 
                 mobile_no, gst_no, email, address, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
            """
            execute_query(query, (
                license_no,
                self.user["distributor_id"],
                shop_name,
                self.owner_name_entry.get().strip(),
                self.mobile_entry.get().strip(),
                self.gst_entry.get().strip(),
                self.email_entry.get().strip(),
                self.address_entry.get().strip()
            ))

            messagebox.showinfo("Success", "New customer added successfully!")
            self._go_back()

        except Exception as e:
            if "Duplicate entry" in str(e):
                messagebox.showerror("Error", "A customer with this License number already exists.")
            else:
                messagebox.showerror("Database Error", f"Failed to save customer:\n{e}")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
