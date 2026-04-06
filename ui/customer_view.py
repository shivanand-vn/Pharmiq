"""
Customer View — CustomTkinter frame for managing customers.
Features a 2-column layout with a list on the left and an add/edit form on the right.
Enhanced with structured address fields, inline validation, and Indian states dropdown.
"""

import customtkinter as ctk
from tkinter import messagebox
import re
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
WARN_BG = "#FEF3C7"
VALID_BORDER = "#10B981"
INVALID_BORDER = "#EF4444"

# ── Indian States / UTs ──
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman & Nicobar Islands", "Chandigarh", "Dadra & Nagar Haveli and Daman & Diu",
    "Delhi", "Jammu & Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

# ── Validation Patterns ──
RE_LICENSE = re.compile(r'^[A-Z]{2}-[A-Z0-9]{2,4}-\d{6}( ?/ ?\d{6})?$')
RE_CONTACT = re.compile(r'^[6-9]\d{9}$')
RE_NAME = re.compile(r'^[A-Za-z .&]{3,50}$')
RE_PINCODE = re.compile(r'^[1-9]\d{5}$')
RE_EMAIL = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class CustomerView(ctk.CTkFrame):
    """View to list, search, and manage customers inline."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self.editing_license = None
        self._search_job = None
        self._validation_state = {}

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── Top bar ──
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
            top, text="🏪 Customer Management",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Main 2-Column Split ──
        split_container = ctk.CTkFrame(self, fg_color="transparent")
        split_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Column (Table)
        self.left_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Right Column (Form) — wider for address fields
        self.right_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR, width=420)
        self.right_col.pack(side="right", fill="y")
        self.right_col.pack_propagate(False)

        self._build_table_area()
        self._build_form_area()

    def _build_table_area(self):
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

        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("License No", 120), ("Shop Name", 160), ("Contact", 100), ("City", 90), ("Actions", 140)
        ]

        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text != "Actions" else "center"
            ).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

    def _schedule_search(self, event=None):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(400, self._load_data)

    # ──────────────────────────────────────────────
    # FORM AREA
    # ──────────────────────────────────────────────
    def _build_form_area(self):
        self.form_title = ctk.CTkLabel(
            self.right_col, text="Add New Customer",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        self.form_title.pack(pady=(20, 10))

        form_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True)

        # ── Customer Details Section ──
        self._section_label(form_scroll, "Customer Details")

        self.f_license, self._v_license = self._add_field(
            form_scroll, "License No", "e.g. KA-AB1-123456", True)
        self.f_shop_name, self._v_shop = self._add_field(
            form_scroll, "Shop Name", "e.g. Name of the Pharmacy", True)
        self.f_owner_name, self._v_owner = self._add_field(
            form_scroll, "Owner Name", "e.g. Name of the Owner", True)
        self.f_mobile, self._v_mobile = self._add_field(
            form_scroll, "Contact Number", "e.g. 9876543210", True)
        self.f_email, self._v_email = self._add_field(
            form_scroll, "Email Address", "Optional", False)

        # ── Address Details Section ──
        self._section_label(form_scroll, "Address Details")

        self.f_addr1, self._v_addr1 = self._add_field(
            form_scroll, "Address Line 1", "Street / Building / Area", True)
        self.f_addr2, _ = self._add_field(
            form_scroll, "Address Line 2", "Landmark (Optional)", False)
        
        # City + PIN Code side-by-side
        row_cp = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row_cp.pack(padx=20, pady=(5, 2), fill="x")
        row_cp.columnconfigure(0, weight=1)
        row_cp.columnconfigure(1, weight=1)

        # City
        city_frame = ctk.CTkFrame(row_cp, fg_color="transparent")
        city_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._field_label(city_frame, "City", True)
        self.f_city = ctk.CTkEntry(
            city_frame, placeholder_text="City", height=38,
            font=ctk.CTkFont(size=12), fg_color=ENTRY_BG,
            border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
        )
        self.f_city.pack(fill="x")
        self._v_city = ctk.CTkLabel(city_frame, text="", font=ctk.CTkFont(size=10), height=14, anchor="w")
        self._v_city.pack(fill="x")

        # PIN Code
        pin_frame = ctk.CTkFrame(row_cp, fg_color="transparent")
        pin_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self._field_label(pin_frame, "PIN Code", True)
        self.f_pincode = ctk.CTkEntry(
            pin_frame, placeholder_text="6-digit PIN", height=38,
            font=ctk.CTkFont(size=12), fg_color=ENTRY_BG,
            border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
        )
        self.f_pincode.pack(fill="x")
        self._v_pincode = ctk.CTkLabel(pin_frame, text="", font=ctk.CTkFont(size=10), height=14, anchor="w")
        self._v_pincode.pack(fill="x")

        # District + State side-by-side
        row_ds = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row_ds.pack(padx=20, pady=(2, 2), fill="x")
        row_ds.columnconfigure(0, weight=1)
        row_ds.columnconfigure(1, weight=1)

        # District
        dist_frame = ctk.CTkFrame(row_ds, fg_color="transparent")
        dist_frame.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._field_label(dist_frame, "District", True)
        self.f_dist = ctk.CTkEntry(
            dist_frame, placeholder_text="District", height=38,
            font=ctk.CTkFont(size=12), fg_color=ENTRY_BG,
            border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
        )
        self.f_dist.pack(fill="x")
        self._v_dist = ctk.CTkLabel(dist_frame, text="", font=ctk.CTkFont(size=10), height=14, anchor="w")
        self._v_dist.pack(fill="x")

        # State dropdown
        state_frame = ctk.CTkFrame(row_ds, fg_color="transparent")
        state_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self._field_label(state_frame, "State", True)
        self.f_state = ctk.CTkComboBox(
            state_frame, values=INDIAN_STATES, height=38,
            font=ctk.CTkFont(size=12), fg_color=ENTRY_BG,
            border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
            corner_radius=6, dropdown_font=ctk.CTkFont(size=11),
            state="normal"
        )
        self.f_state.set("Karnataka")
        self.f_state.pack(fill="x")
        self._v_state = ctk.CTkLabel(state_frame, text="", font=ctk.CTkFont(size=10), height=14, anchor="w")
        self._v_state.pack(fill="x")

        # ── Buttons ──
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(15, 20))

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

        # Status message
        self.form_status = ctk.CTkLabel(
            form_scroll, text="", font=ctk.CTkFont(size=11),
            text_color=SUCCESS, height=20
        )
        self.form_status.pack(pady=(0, 10))

        # ── Bind real-time validation ──
        self._bind_validation()

    # ──────────────────────────────────────────────
    # FORM HELPERS
    # ──────────────────────────────────────────────
    def _section_label(self, parent, text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(padx=20, pady=(12, 2), fill="x")
        ctk.CTkLabel(
            frame, text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ACCENT, anchor="w"
        ).pack(side="left")
        ctk.CTkFrame(frame, fg_color=BORDER_CLR, height=1).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=1)

    def _field_label(self, parent, text, required):
        lbl_row = ctk.CTkFrame(parent, fg_color="transparent")
        lbl_row.pack(fill="x", pady=(0, 3))
        ctk.CTkLabel(lbl_row, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_DARK, anchor="w", height=14).pack(side="left")
        if required:
            ctk.CTkLabel(lbl_row, text=" *", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=DANGER, anchor="w", height=14).pack(side="left")

    def _add_field(self, parent, label_text, placeholder, required=True):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(padx=20, pady=(5, 2), fill="x")

        self._field_label(row, label_text, required)

        entry = ctk.CTkEntry(
            row, placeholder_text=placeholder, height=38,
            font=ctk.CTkFont(size=12), fg_color=ENTRY_BG,
            border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
        )
        entry.pack(fill="x")

        # Validation label
        vlabel = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=10), height=14, anchor="w")
        vlabel.pack(fill="x")
        return entry, vlabel

    # ──────────────────────────────────────────────
    # VALIDATION
    # ──────────────────────────────────────────────
    def _bind_validation(self):
        """Bind real-time validation to all fields."""
        self.f_license.bind("<KeyRelease>", lambda e: self._validate_license())
        self.f_license.bind("<FocusOut>", lambda e: self._validate_license())
        self.f_shop_name.bind("<KeyRelease>", lambda e: self._validate_name())
        self.f_shop_name.bind("<FocusOut>", lambda e: self._validate_name())
        self.f_owner_name.bind("<KeyRelease>", lambda e: self._validate_owner())
        self.f_owner_name.bind("<FocusOut>", lambda e: self._validate_owner())
        self.f_mobile.bind("<KeyRelease>", lambda e: self._validate_mobile())
        self.f_mobile.bind("<FocusOut>", lambda e: self._validate_mobile())
        self.f_email.bind("<KeyRelease>", lambda e: self._validate_email())
        self.f_email.bind("<FocusOut>", lambda e: self._validate_email())
        self.f_addr1.bind("<KeyRelease>", lambda e: self._validate_addr1())
        self.f_addr1.bind("<FocusOut>", lambda e: self._validate_addr1())
        self.f_city.bind("<KeyRelease>", lambda e: self._validate_city())
        self.f_city.bind("<FocusOut>", lambda e: self._validate_city())
        self.f_dist.bind("<KeyRelease>", lambda e: self._validate_dist())
        self.f_dist.bind("<FocusOut>", lambda e: self._validate_dist())
        self.f_pincode.bind("<KeyRelease>", lambda e: self._validate_pincode())
        self.f_pincode.bind("<FocusOut>", lambda e: self._validate_pincode())
        self.f_state.bind("<<ComboboxSelected>>", lambda e: self._validate_state())
        self.f_state.bind("<KeyRelease>", lambda e: self._validate_state())
        self.f_state.bind("<FocusOut>", lambda e: self._validate_state())

        # Auto-uppercase license number
        self.f_license.bind("<KeyRelease>", lambda e: self._auto_upper_license(), add="+")

    def _auto_upper_license(self):
        val = self.f_license.get()
        upper = val.upper()
        if val != upper:
            pos = self.f_license.index("insert")
            self.f_license.delete(0, "end")
            self.f_license.insert(0, upper)
            self.f_license.icursor(pos)

    def _set_valid(self, entry, vlabel, msg=""):
        entry.configure(border_color=VALID_BORDER)
        vlabel.configure(text=f"✓ {msg}" if msg else "", text_color=VALID_BORDER)
        self.after(10, self._update_save_btn)

    def _set_invalid(self, entry, vlabel, msg):
        entry.configure(border_color=INVALID_BORDER)
        vlabel.configure(text=f"✗ {msg}", text_color=INVALID_BORDER)
        self.after(10, self._update_save_btn)

    def _set_neutral(self, entry, vlabel):
        entry.configure(border_color=BORDER_CLR)
        vlabel.configure(text="")
        self.after(10, self._update_save_btn)

    def _validate_license(self):
        val = self.f_license.get().strip()
        if not val:
            self._set_neutral(self.f_license, self._v_license)
            self._validation_state["license"] = False
            return False
        if RE_LICENSE.match(val):
            self._set_valid(self.f_license, self._v_license, "Valid")
            self._validation_state["license"] = True
            return True
        self._set_invalid(self.f_license, self._v_license, "Format: KA-BG2-283573")
        self._validation_state["license"] = False
        return False

    def _validate_name(self):
        val = self.f_shop_name.get().strip()
        if not val:
            self._set_neutral(self.f_shop_name, self._v_shop)
            self._validation_state["name"] = False
            return False
        if RE_NAME.match(val):
            self._set_valid(self.f_shop_name, self._v_shop, "Valid")
            self._validation_state["name"] = True
            return True
        self._set_invalid(self.f_shop_name, self._v_shop, "3-50 chars, letters/space/./& only")
        self._validation_state["name"] = False
        return False

    def _validate_owner(self):
        val = self.f_owner_name.get().strip()
        if not val:
            self._set_neutral(self.f_owner_name, self._v_owner)
            self._validation_state["owner"] = False
            return False
        if RE_NAME.match(val):
            self._set_valid(self.f_owner_name, self._v_owner, "Valid")
            self._validation_state["owner"] = True
            return True
        self._set_invalid(self.f_owner_name, self._v_owner, "3-50 chars, letters/space/./& only")
        self._validation_state["owner"] = False
        return False

    def _validate_mobile(self):
        val = self.f_mobile.get().strip()
        if not val:
            self._set_neutral(self.f_mobile, self._v_mobile)
            self._validation_state["mobile"] = False
            return False
        if RE_CONTACT.match(val):
            self._set_valid(self.f_mobile, self._v_mobile, "Valid")
            self._validation_state["mobile"] = True
            return True
        self._set_invalid(self.f_mobile, self._v_mobile, "10 digits starting with 6-9")
        self._validation_state["mobile"] = False
        return False

    def _validate_email(self):
        val = self.f_email.get().strip()
        if not val:
            self._set_neutral(self.f_email, self._v_email)
            self._validation_state["email"] = True  # Optional
            return True
        if RE_EMAIL.match(val):
            self._set_valid(self.f_email, self._v_email, "Valid")
            self._validation_state["email"] = True
            return True
        self._set_invalid(self.f_email, self._v_email, "Enter a valid email")
        self._validation_state["email"] = False
        return False

    def _validate_addr1(self):
        val = self.f_addr1.get().strip()
        if not val:
            self._set_neutral(self.f_addr1, self._v_addr1)
            self._validation_state["addr1"] = False
            return False
        if len(val) >= 3:
            self._set_valid(self.f_addr1, self._v_addr1, "Valid")
            self._validation_state["addr1"] = True
            return True
        self._set_invalid(self.f_addr1, self._v_addr1, "At least 3 characters")
        self._validation_state["addr1"] = False
        return False

    def _validate_city(self):
        val = self.f_city.get().strip()
        if not val:
            self._set_neutral(self.f_city, self._v_city)
            self._validation_state["city"] = False
            return False
        if len(val) >= 2:
            self._set_valid(self.f_city, self._v_city, "Valid")
            self._validation_state["city"] = True
            return True
        self._set_invalid(self.f_city, self._v_city, "Required")
        self._validation_state["city"] = False
        return False

    def _validate_dist(self):
        val = self.f_dist.get().strip()
        if not val:
            self._set_neutral(self.f_dist, self._v_dist)
            self._validation_state["dist"] = False
            return False
        if len(val) >= 2:
            self._set_valid(self.f_dist, self._v_dist, "Valid")
            self._validation_state["dist"] = True
            return True
        self._set_invalid(self.f_dist, self._v_dist, "Required")
        self._validation_state["dist"] = False
        return False

    def _validate_state(self):
        val = self.f_state.get().strip()
        if not val:
            val = "Karnataka"
            self.f_state.set(val)
        if val and val in INDIAN_STATES:
            self._validation_state["state"] = True
            self._set_valid(self.f_state, self._v_state, "Valid")
            return True
        self._validation_state["state"] = False
        self._set_neutral(self.f_state, self._v_state)
        return False

    def _validate_pincode(self):
        val = self.f_pincode.get().strip()
        if not val:
            self._set_neutral(self.f_pincode, self._v_pincode)
            self._validation_state["pincode"] = False
            return False
        if RE_PINCODE.match(val):
            self._set_valid(self.f_pincode, self._v_pincode, "Valid")
            self._validation_state["pincode"] = True
            return True
        self._set_invalid(self.f_pincode, self._v_pincode, "6 digits, not starting with 0")
        self._validation_state["pincode"] = False
        return False

    def _update_save_btn(self):
        """Enable save only when all required fields are valid."""
        missing = []
        if not RE_LICENSE.match(self.f_license.get().strip()): missing.append("license")
        if not RE_NAME.match(self.f_shop_name.get().strip()): missing.append("name")
        if not RE_NAME.match(self.f_owner_name.get().strip()): missing.append("owner")
        if not RE_CONTACT.match(self.f_mobile.get().strip()): missing.append("mobile")
        
        email_val = self.f_email.get().strip()
        if email_val and not RE_EMAIL.match(email_val): missing.append("email")
            
        if len(self.f_addr1.get().strip()) < 3: missing.append("addr1")
        if len(self.f_city.get().strip()) < 2: missing.append("city")
        if len(self.f_dist.get().strip()) < 2: missing.append("dist")
        
        state_val = self.f_state.get().strip()
        if not state_val or state_val not in INDIAN_STATES: missing.append("state")
            
        if not RE_PINCODE.match(self.f_pincode.get().strip()): missing.append("pincode")

        # Update dictionary synchronicity so everything aligns perfectly
        for k in ["license", "name", "owner", "mobile", "email", "addr1", "city", "dist", "state", "pincode"]:
            self._validation_state[k] = (k not in missing)
        
        # Debugging step: Display missing fields in the form status
        if missing:
            self.form_status.configure(text=f"Missing: {', '.join(missing)}", text_color="#EF4444")
        else:
            self.form_status.configure(text="")
            
        all_valid = len(missing) == 0
        if all_valid:
            self.save_btn.configure(state="normal", fg_color=SUCCESS)
        else:
            self.save_btn.configure(state="disabled", fg_color="#9CA3AF")

    def _validate_all(self):
        """Run all validators and return True if form is valid."""
        results = [
            self._validate_license(),
            self._validate_name(),
            self._validate_owner(),
            self._validate_mobile(),
            self._validate_email(),
            self._validate_addr1(),
            self._validate_city(),
            self._validate_dist(),
            self._validate_state(),
            self._validate_pincode(),
        ]
        return all(results)

    # ──────────────────────────────────────────────
    # DATA LOADING
    # ──────────────────────────────────────────────
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
            ctk.CTkLabel(self.scroll, text="No active customers found.",
                         font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        cols = [("license_no", 120), ("shop_name", 160), ("mobile_no", 100), ("city", 90)]

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


    # ──────────────────────────────────────────────
    # EDIT / CLEAR / SAVE
    # ──────────────────────────────────────────────
    def _start_edit(self, row):
        self._clear_form()
        self.editing_license = row["license_no"]
        self.form_title.configure(text="Update Customer")
        self.save_btn.configure(text="Update")

        self.f_license.insert(0, row.get("license_no", ""))
        self.f_shop_name.insert(0, row.get("shop_name", ""))
        self.f_owner_name.insert(0, row.get("license_holder_name", "") or "")
        self.f_mobile.insert(0, row.get("mobile_no", ""))
        self.f_email.insert(0, row.get("email", "") or "")
        self.f_addr1.insert(0, row.get("address_line1", "") or "")
        self.f_addr2.insert(0, row.get("address_line2", "") or "")
        self.f_city.insert(0, row.get("city", "") or "")
        self.f_dist.insert(0, row.get("dist", "") or "")
        self.f_pincode.insert(0, row.get("pincode", "") or "")

        state_val = row.get("state", "")
        if state_val:
            self.f_state.set(state_val)

        # Run validation on all loaded fields
        self._validate_all()

    def _clear_form(self):
        self.editing_license = None
        self.form_title.configure(text="Add New Customer")
        self.save_btn.configure(text="Save Customer")
        self.form_status.configure(text="")
        self._validation_state.clear()

        for entry in [self.f_license, self.f_shop_name, self.f_owner_name, self.f_mobile, self.f_email,
                      self.f_addr1, self.f_addr2, self.f_city, self.f_dist, self.f_pincode]:
            entry.delete(0, "end")
            entry.configure(border_color=BORDER_CLR)

        self.f_state.set("Karnataka")
        self.f_state.configure(border_color=BORDER_CLR)

        # Clear validation labels
        for vlbl in [self._v_license, self._v_shop, self._v_owner, self._v_mobile, self._v_email,
                     self._v_addr1, self._v_city, self._v_dist, self._v_state, self._v_pincode]:
            vlbl.configure(text="")

        self._validate_all()
        self._update_save_btn()

    def _save_customer(self):
        if not self._validate_all():
            self.form_status.configure(text="⚠ Please fix all validation errors.", text_color=DANGER)
            return

        license_no = self.f_license.get().strip().upper()
        shop_name = self.f_shop_name.get().strip()
        owner_name = self.f_owner_name.get().strip()
        mobile = self.f_mobile.get().strip()
        email = self.f_email.get().strip()
        addr1 = self.f_addr1.get().strip()
        addr2 = self.f_addr2.get().strip()
        city = self.f_city.get().strip()
        dist = self.f_dist.get().strip()
        state = self.f_state.get().strip()
        pincode = self.f_pincode.get().strip()

        # Normalize license — trim extra spaces
        license_no = re.sub(r'\s+', ' ', license_no).strip()

        # Added confirmation dialog before saving
        action_text = "update" if self.editing_license else "add"
        msg = f"Are you sure you want to {action_text} customer '{shop_name}'?\nPlease verify the details before saving."
        if not messagebox.askyesno("Confirm Action", msg):
            return

        try:
            if self.editing_license:
                update_customer(
                    self.editing_license, license_no, shop_name,
                    name=owner_name, mobile=mobile, gst="", email=email,
                    address_line1=addr1, address_line2=addr2,
                    city=city, dist=dist, state=state, pincode=pincode
                )
                self.form_status.configure(text="✓ Customer updated successfully!", text_color=SUCCESS)
                messagebox.showinfo("Success", f"Customer '{shop_name}' updated successfully!")
            else:
                create_customer(
                    self.user["distributor_id"], license_no, shop_name,
                    name=owner_name, mobile=mobile, gst="", email=email,
                    address_line1=addr1, address_line2=addr2,
                    city=city, dist=dist, state=state, pincode=pincode
                )
                self.form_status.configure(text="✓ New customer added successfully!", text_color=SUCCESS)
                messagebox.showinfo("Success", f"New customer '{shop_name}' added successfully!")

            self._clear_form()
            self._load_data()

        except Exception as e:
            err = str(e).lower()
            if "duplicate entry" in err:
                self.form_status.configure(
                    text="✗ Customer with this License No already exists.", text_color=DANGER)
                messagebox.showerror("Duplicate License", f"A customer with License No '{license_no}' already exists in the system.")
            elif "foreign key constraint" in err or "1451" in err:
                self.form_status.configure(
                    text="✗ Cannot change License No — customer has linked invoices.", text_color=DANGER)
                messagebox.showwarning("Linked Records Found", 
                    "This customer has linked invoices. You can update other details, but the 'License No' cannot be changed because it would break historical billing data.")
            else:
                messagebox.showerror("Database Error", f"Failed to save customer:\n{e}")

    def _delete_customer(self, license_no):
        if messagebox.askyesno("Confirm", f"Are you sure you want to deactivate customer {license_no}?"):
            try:
                toggle_customer_status(license_no, 'inactive')
                self.form_status.configure(text="✓ Customer deactivated.", text_color=SUCCESS)

                if self.editing_license == license_no:
                    self._clear_form()

                self._load_data()
            except Exception as e:
                err = str(e).lower()
                if "foreign key constraint" in err or "1451" in err:
                    messagebox.showwarning("Cannot Deactivate",
                        "This customer has linked invoices and cannot be deactivated.")
                else:
                    messagebox.showerror("Error", f"Could not deactivate customer: {e}")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
