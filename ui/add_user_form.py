"""
Add User Form — CustomTkinter form for adding a new user and assigning a role.
"""

import customtkinter as ctk
from tkinter import messagebox
from models.user import create_user

# ── Colour palette ──
BG_DARK = "#F8F9FA"
CARD_BG = "#212529"
BORDER_CLR = "#DEE2E6"
ACCENT = "#4361EE"
TEXT_WHITE = "#212529"
TEXT_MUTED = "#868E96"
ENTRY_BG = "#F8F9FA"
SUCCESS = "#2DC653"


class AddUserForm(ctk.CTkFrame):
    """Form to add a new user and role."""

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
            fg_color="#E9ECEF", hover_color="#CED4DA", text_color="#212529",
            command=self._go_back,
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top, text="👥  Add New User",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Form Content ──
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_CLR)
        card.pack(fill="x", padx=10, pady=20)

        def add_entry(parent, label_text, placeholder="", show=""):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row, text=label_text, width=150, anchor="w",
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left")
            entry = ctk.CTkEntry(row, placeholder_text=placeholder, show=show, height=35,
                                 font=ctk.CTkFont(size=12), fg_color=ENTRY_BG,
                                 border_color=BORDER_CLR, text_color=TEXT_WHITE)
            entry.pack(side="left", fill="x", expand=True)
            return entry

        self.username_entry = add_entry(card, "Username (Required)")
        self.password_entry = add_entry(card, "Password (Required)", show="●")
        self.confirm_entry = add_entry(card, "Confirm Password", show="●")

        # Role Dropdown
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row, text="Select Role", width=150, anchor="w",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left")
        
        self.role_var = ctk.StringVar(value="Biller")
        self.role_menu = ctk.CTkOptionMenu(
            row, variable=self.role_var, values=["Admin", "Biller", "Accountant"],
            fg_color=ENTRY_BG, button_color=ACCENT, text_color=TEXT_WHITE, height=35
        )
        self.role_menu.pack(side="left", fill="x", expand=True)

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame, text="✅  Create User", height=45, width=200,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            fg_color=SUCCESS, hover_color="#208B3A", text_color="#FFFFFF",
            command=self._save_user,
        ).pack(side="left", padx=5)

    def _save_user(self):
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
            create_user(self.user["distributor_id"], username, pwd, role)
            messagebox.showinfo("Success", f"User '{username}' created with role '{role}'.")
            self._go_back()
        except Exception as e:
            if "Duplicate entry" in str(e).lower():
                messagebox.showerror("Error", "This username is already taken.")
            else:
                messagebox.showerror("Database Error", f"Failed to create user:\n{e}")

    def _go_back(self):
        from ui.user_view import UserView
        for widget in self.master.winfo_children():
            widget.destroy()
        view = UserView(self.master, self.user, self.app)
        view.pack(fill="both", expand=True)

