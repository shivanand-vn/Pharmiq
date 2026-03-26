"""
Customer View — CustomTkinter frame for managing customers.
Features a 2-column layout with a list on the left and an add/edit form on the right.
"""

import customtkinter as ctk
from tkinter import messagebox
from models.customer import search_customers, create_customer, update_customer, toggle_customer_status

# ── Colour palette ──
BG_DARK = "#F8F9FA"
CARD_BG = "#FFFFFF"
BORDER_CLR = "#E5E7EB"
ACCENT = "#4361EE"
ACCENT_HOVER = "#3A0CA3"
TEXT_DARK = "#111827"
TEXT_MUTED = "#6B7280"
ENTRY_BG = "#F9FAFB"
SUCCESS = "#10B981"
SUCCESS_HOV = "#059669"
DANGER = "#EF4444"


class CustomerView(ctk.CTkFrame):
    """View to list, search, and manage customers inline."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref
        
        self.editing_license = None # Tracks if we are editing an existing customer
        self._search_job = None # Debounce timer ID
        
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=60, border_width=1, border_color=BORDER_CLR)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back to Dashboard", width=140, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            top, text="🏪 Customer Management",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Main 2-Column Split ──
        split_container = ctk.CTkFrame(self, fg_color="transparent")
        split_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Column (Table)
        self.left_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Right Column (Form)
        self.right_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR, width=380)
        self.right_col.pack(side="right", fill="y")
        self.right_col.pack_propagate(False) # Keep fixed width

        self._build_table_area()
        self._build_form_area()

    def _build_table_area(self):
        # Toolbar
        toolbar = ctk.CTkFrame(self.left_col, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=15)

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search customers...",
            width=300, height=40, font=ctk.CTkFont(size=13), corner_radius=8, 
            fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK
        )
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", self._schedule_search)

        # Header
        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("License No", 120), ("Customer Name", 200), ("Contact No", 110), ("Actions", 140)
        ]
        
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text != "Actions" else "center"
            ).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

    def _schedule_search(self, event=None):
        """Debounce the search input."""
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(400, self._load_data)

    def _build_form_area(self):
        # Header
        self.form_title = ctk.CTkLabel(self.right_col, text="Add New Customer", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK)
        self.form_title.pack(pady=(25, 20))
        
        # Scrollable form container just in case height is limited
        form_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True)

        def add_v_entry(parent, label_text, placeholder, required=True):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=25, pady=(5, 10), fill="x")

            lbl_row = ctk.CTkFrame(row, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(lbl_row, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
            if required:
                ctk.CTkLabel(lbl_row, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w", height=15).pack(side="left")

            entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=40, font=ctk.CTkFont(size=13), 
                                 fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6)
            entry.pack(fill="x")
            return entry

        self.f_license = add_v_entry(form_scroll, "License No", "e.g. KA-DW-1234", True)
        self.f_shop_name = add_v_entry(form_scroll, "Customer / Shop Name", "e.g. Apollo Pharmacy", True)
        self.f_mobile = add_v_entry(form_scroll, "Contact Number", "e.g. 9876543210", True)
        self.f_address = add_v_entry(form_scroll, "Address", "Full Address", True)
        self.f_email = add_v_entry(form_scroll, "Email Address", "Optional", False)

        # Button Area
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(20, 20))
        
        self.save_btn = ctk.CTkButton(
            btn_frame, text="Save Customer", height=40,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._save_customer
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.clear_btn = ctk.CTkButton(
            btn_frame, text="Clear", height=40,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._clear_form
        )
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

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

        cols = [("license_no", 120), ("shop_name", 200), ("mobile_no", 110)]

        for row in customers:
            frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
            frame.pack(fill="x", pady=2)
            frame.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=5)

            for key, w in cols:
                val = str(row.get(key) or "N/A")[:25]
                ctk.CTkLabel(
                    frame, text=val, width=w, font=ctk.CTkFont(size=12),
                    text_color=TEXT_DARK, anchor="w"
                ).pack(side="left", padx=5)

            # Actions
            action_frame = ctk.CTkFrame(frame, width=140, fg_color="transparent")
            action_frame.pack_propagate(False)
            action_frame.pack(side="left", padx=5, pady=5)
            
            ctk.CTkButton(
                action_frame, text="Edit", width=60, height=28,
                font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6,
                fg_color="#DBEAFE", hover_color="#BFDBFE", text_color="#1E3A8A",
                command=lambda r=row: self._start_edit(r)
            ).pack(side="left", padx=(0, 5))

            ctk.CTkButton(
                action_frame, text="Del", width=60, height=28,
                font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6,
                fg_color="#FEE2E2", hover_color="#FECACA", text_color="#991B1B",
                command=lambda l=row["license_no"]: self._delete_customer(l)
            ).pack(side="left")

    def _start_edit(self, row):
        self._clear_form()
        self.editing_license = row["license_no"]
        self.form_title.configure(text="Update Customer")
        self.save_btn.configure(text="Update")
        
        self.f_license.insert(0, row.get("license_no", ""))
        self.f_shop_name.insert(0, row.get("shop_name", ""))
        self.f_mobile.insert(0, row.get("mobile_no", ""))
        self.f_address.insert(0, row.get("address", ""))
        self.f_email.insert(0, row.get("email", ""))
        
    def _clear_form(self):
        self.editing_license = None
        self.form_title.configure(text="Add New Customer")
        self.save_btn.configure(text="Save Customer")
        
        for entry in [self.f_license, self.f_shop_name, self.f_mobile, self.f_address, self.f_email]:
            entry.delete(0, 'end')

    def _save_customer(self):
        license_no = self.f_license.get().strip()
        shop_name = self.f_shop_name.get().strip()
        mobile = self.f_mobile.get().strip()
        address = self.f_address.get().strip()
        email = self.f_email.get().strip()

        # Validate mandatory fields
        if not all([license_no, shop_name, mobile, address]):
            messagebox.showwarning("Incomplete", "Please fill in all the required fields (marked with *).")
            return

        try:
            if self.editing_license:
                update_customer(self.editing_license, license_no, shop_name, name="", mobile=mobile, gst="", email=email, address=address)
                messagebox.showinfo("Success", "Customer updated successfully!")
            else:
                create_customer(self.user["distributor_id"], license_no, shop_name, name="", mobile=mobile, gst="", email=email, address=address)
                messagebox.showinfo("Success", "New customer added successfully!")
                
            self._clear_form()
            self._load_data()

        except Exception as e:
            if "Duplicate entry" in str(e).lower():
                messagebox.showerror("Error", "A customer with this License number already exists.")
            else:
                messagebox.showerror("Database Error", f"Failed to save customer:\n{e}")

    def _delete_customer(self, license_no):
        if messagebox.askyesno("Confirm", f"Are you sure you want to deactivate customer {license_no}?"):
            try:
                toggle_customer_status(license_no, 'inactive')
                messagebox.showinfo("Success", "Customer deactivated.")
                
                # If editing this customer, clear form
                if self.editing_license == license_no:
                    self._clear_form()
                    
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Could not deactivate customer: {e}")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
