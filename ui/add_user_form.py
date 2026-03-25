"""
Add User Form — CustomTkinter form for adding a new user and assigning a role.
Refactored for a more attractive, modern, centered card layout.
"""

import customtkinter as ctk
from tkinter import messagebox
from models.user import create_user

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


class AddUserForm(ctk.CTkFrame):
    """Form to add a new user and role."""

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
            top, text="← Back to Users", width=120, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=20, pady=12)

        # ── Scrollable Center Container ──
        # In case the screen is small, allowing scrolling is safer
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)
        # We use a dummy frame to center the card
        center_frame = ctk.CTkFrame(container, fg_color="transparent")
        center_frame.pack(fill="both", expand=True)
        
        # spacer to push down slightly
        ctk.CTkFrame(center_frame, fg_color="transparent", height=40).pack()

        # ── Form Card ──
        card = ctk.CTkFrame(center_frame, fg_color=CARD_BG, corner_radius=16,
                            border_width=1, border_color=BORDER_CLR)
        card.pack(pady=10) # Centered horizontally by default because we didn't specify fill/anchor
        
        # Header inside Card
        ctk.CTkLabel(card, text="👤 Create New User", font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT_DARK).pack(pady=(35, 5))
        ctk.CTkLabel(card, text="Enter the user's details and assign a role.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=(0, 25))

        # Helper for vertical fields
        def add_v_entry(parent, label_text, placeholder="", show="", width=420):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=50, pady=(8, 12))
            ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 6))
            entry = ctk.CTkEntry(row, placeholder_text=placeholder, show=show, height=45, width=width,
                                 font=ctk.CTkFont(size=14), fg_color=ENTRY_BG,
                                 border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=8)
            entry.pack()
            return entry

        # Layout fields
        self.name_entry = add_v_entry(card, "Full Name (Optional)", "e.g. Jane Doe")
        self.mobile_entry = add_v_entry(card, "Mobile No (Optional)", "e.g. 9876543210")
        
        # Divider
        ctk.CTkFrame(card, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=50, pady=15)

        self.username_entry = add_v_entry(card, "Username (Required)", "e.g. janedoe")
        
        # Group Password Fields side-by-side
        pass_row = ctk.CTkFrame(card, fg_color="transparent")
        pass_row.pack(padx=50, pady=(8, 12), fill="x")
        
        # Left Pass
        p1 = ctk.CTkFrame(pass_row, fg_color="transparent")
        p1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(p1, text="Password (Required)", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 6))
        self.password_entry = ctk.CTkEntry(p1, placeholder_text="••••••••", show="●", height=45,
                                font=ctk.CTkFont(size=14), fg_color=ENTRY_BG,
                                border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=8)
        self.password_entry.pack(fill="x")

        # Right Pass
        p2 = ctk.CTkFrame(pass_row, fg_color="transparent")
        p2.pack(side="right", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(p2, text="Confirm Password", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 6))
        self.confirm_entry = ctk.CTkEntry(p2, placeholder_text="••••••••", show="●", height=45,
                                font=ctk.CTkFont(size=14), fg_color=ENTRY_BG,
                                border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=8)
        self.confirm_entry.pack(fill="x")

        # Role Selection
        role_row = ctk.CTkFrame(card, fg_color="transparent")
        role_row.pack(padx=50, pady=(8, 15), fill="x")
        ctk.CTkLabel(role_row, text="Select User Role", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_DARK, anchor="w").pack(fill="x", pady=(0, 6))
        
        self.role_var = ctk.StringVar(value="Biller")
        self.role_menu = ctk.CTkOptionMenu(
            role_row, variable=self.role_var, values=["Admin", "Biller", "Accountant"],
            fg_color=ENTRY_BG, button_color=ACCENT, button_hover_color="#3A0CA3", text_color=TEXT_DARK, 
            dropdown_text_color="#000000", height=45, corner_radius=8
        )
        self.role_menu.pack(fill="x")

        # ── Submit Button ──
        ctk.CTkButton(
            card, text="Create User Account", height=50,
            font=ctk.CTkFont(size=15, weight="bold"), corner_radius=8,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._save_user,
        ).pack(fill="x", padx=50, pady=(20, 40))

        # Bottom spacer for scrolling
        ctk.CTkFrame(center_frame, fg_color="transparent", height=60).pack()

    def _save_user(self):
        name = self.name_entry.get().strip()
        mobile = self.mobile_entry.get().strip()
        username = self.username_entry.get().strip()
        pwd = self.password_entry.get()
        confirm = self.confirm_entry.get()
        role = self.role_var.get()

        if not username or not pwd:
            messagebox.showwarning("Incomplete", "Username and Password are required.")
            return

        if pwd != confirm:
            messagebox.showwarning("Mismatch", "Passwords do not match.")
            return

        try:
            create_user(self.user["distributor_id"], username, pwd, role, name, mobile)
            messagebox.showinfo("Success", f"User '{username}' created successfully with role: {role}.")
            self._go_back()
        except ValueError as ve:
            messagebox.showwarning("Validation Error", str(ve))
        except Exception as e:
            if "Duplicate entry" in str(e).lower():
                messagebox.showerror("Error", "This username is already taken. Please choose another.")
            else:
                messagebox.showerror("Database Error", f"Failed to create user:\n{e}")

    def _go_back(self):
        from ui.user_view import UserView
        for widget in self.master.winfo_children():
            widget.destroy()
        view = UserView(self.master, self.user, self.app)
        view.pack(fill="both", expand=True)
