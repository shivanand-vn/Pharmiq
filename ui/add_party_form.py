"""
Add Party Form — CustomTkinter form for adding a new customer (party).
Refactored for a more attractive, modern, centered card layout.
"""

import customtkinter as ctk
from tkinter import messagebox
from db.connection import execute_query

# ── Colour palette ──
BG_DARK = "#F8F9FA"      # Main bg
CARD_BG = "#FFFFFF"      # White card
BORDER_CLR = "#E5E7EB"   # Light gray border
ACCENT = "#4361EE"       # Primary accent
TEXT_DARK = "#111827"    # Dark text
TEXT_MUTED = "#6B7280"   # Gray text
ENTRY_BG = "#F9FAFB"     # Off-white entry
SUCCESS = "#10B981"      # Green success
SUCCESS_HOV = "#059669"  # Green hover
DANGER = "#EF4444"       # Red asterisk


class AddPartyForm(ctk.CTkFrame):
    """Form to add a new customer (party)."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self._build_ui()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=60, border_width=1, border_color=BORDER_CLR)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back to Customers", width=140, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=20, pady=12)

        # ── Scrollable Center Container ──
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Center wrapping frame
        center_frame = ctk.CTkFrame(container, fg_color="transparent")
        center_frame.pack(fill="both", expand=True)
        ctk.CTkFrame(center_frame, fg_color="transparent", height=40).pack()

        # ── Form Card ──
        card = ctk.CTkFrame(center_frame, fg_color=CARD_BG, corner_radius=16,
                            border_width=1, border_color=BORDER_CLR)
        card.pack(pady=10)

        # Header inside Card
        ctk.CTkLabel(card, text="🏪 Add New Customer", font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT_DARK).pack(pady=(35, 5))
        ctk.CTkLabel(card, text="Enter customer details below.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=(0, 25))

        # Helper for vertical fields
        def add_v_entry(parent, label_text, placeholder="", required=True):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=50, pady=(8, 12), fill="x")

            lbl_row = ctk.CTkFrame(row, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(0, 6))
            
            ctk.CTkLabel(lbl_row, text=label_text, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(side="left")
            if required:
                ctk.CTkLabel(lbl_row, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w").pack(side="left")

            entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=45, width=420,
                                 font=ctk.CTkFont(size=14), fg_color=ENTRY_BG,
                                 border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=8)
            entry.pack()
            return entry

        # Fields
        self.license_entry = add_v_entry(card, "License No.", "e.g. KA-DW-1234", required=True)
        self.shop_name_entry = add_v_entry(card, "Shop Name", "e.g. Apollo Pharmacy", required=True)
        self.owner_name_entry = add_v_entry(card, "Owner / Holder Name", "e.g. John Smith", required=True)
        
        # Grid layout for smaller inputs side-by-side
        contact_row = ctk.CTkFrame(card, fg_color="transparent")
        contact_row.pack(padx=50, pady=(8, 12), fill="x")
        
        # Mobile
        m_frame = ctk.CTkFrame(contact_row, fg_color="transparent")
        m_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        lbl_m = ctk.CTkFrame(m_frame, fg_color="transparent")
        lbl_m.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(lbl_m, text="Mobile Number", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkLabel(lbl_m, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER).pack(side="left")
        self.mobile_entry = ctk.CTkEntry(m_frame, placeholder_text="Phone", height=45, font=ctk.CTkFont(size=14), fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=8)
        self.mobile_entry.pack(fill="x")

        # GST
        g_frame = ctk.CTkFrame(contact_row, fg_color="transparent")
        g_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))
        lbl_g = ctk.CTkFrame(g_frame, fg_color="transparent")
        lbl_g.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(lbl_g, text="GST Number", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK).pack(side="left")
        ctk.CTkLabel(lbl_g, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER).pack(side="left")
        self.gst_entry = ctk.CTkEntry(g_frame, placeholder_text="GSTIN", height=45, font=ctk.CTkFont(size=14), fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=8)
        self.gst_entry.pack(fill="x")

        # Optional Email & Required Address
        self.email_entry = add_v_entry(card, "Email Address", "e.g. contact@apollo.com", required=False)
        self.address_entry = add_v_entry(card, "Full Address", "123 Main St, City", required=True)

        ctk.CTkButton(
            card, text="Save Customer", height=50,
            font=ctk.CTkFont(size=15, weight="bold"), corner_radius=8,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._save_customer,
        ).pack(fill="x", padx=50, pady=(20, 40))

        # Bottom spacer
        ctk.CTkFrame(center_frame, fg_color="transparent", height=60).pack()

    def _save_customer(self):
        license_no = self.license_entry.get().strip()
        shop_name = self.shop_name_entry.get().strip()
        owner = self.owner_name_entry.get().strip()
        mobile = self.mobile_entry.get().strip()
        gst = self.gst_entry.get().strip()
        address = self.address_entry.get().strip()
        email = self.email_entry.get().strip()

        # Validate mandatory fields
        if not all([license_no, shop_name, owner, mobile, gst, address]):
            messagebox.showwarning("Incomplete", "Please fill in all the required fields (marked with *).")
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
                owner,
                mobile,
                gst,
                email,
                address
            ))

            messagebox.showinfo("Success", "New customer added successfully!")
            self._go_back()

        except Exception as e:
            if "Duplicate entry" in str(e).lower():
                messagebox.showerror("Error", "A customer with this License number already exists.")
            else:
                messagebox.showerror("Database Error", f"Failed to save customer:\n{e}")

    def _go_back(self):
        # Determine the previous view: usually we return to CustomerView.
        # But if the user navigated differently, returning to CustomerView is default intended behavior.
        from ui.customer_view import CustomerView
        for widget in self.master.winfo_children():
            widget.destroy()
        view = CustomerView(self.master, self.user, self.app)
        view.pack(fill="both", expand=True)
