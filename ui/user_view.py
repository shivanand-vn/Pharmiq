"""
User View — CustomTkinter frame for managing users and roles.
"""

import customtkinter as ctk
import re
from tkinter import messagebox
from models.user import get_all_users_with_roles, update_user_status, create_user, update_user
from utils.async_db import async_db_call

# ── Colour palette ──
BG_DARK = "#F8F9FA"
CARD_BG = "#FFFFFF"
BORDER_CLR = "#DEE2E6"
ACCENT = "#4361EE"
TEXT_DARK = "#212529"
TEXT_MUTED = "#868E96"
SUCCESS = "#10B981"
DANGER = "#EF4444"
INPUT_BG = "#F8F9FA"

class UserView(ctk.CTkFrame):
    """View to list and manage users and their roles side-by-side."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref
        
        self.all_users = []
        self.editing_user_id = None
        self._password_visible = False
        
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── Top bar ──
        top = ctk.CTkFrame(self, fg_color="#212529", corner_radius=0, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        if self.user.get("role") != "Admin":
            ctk.CTkLabel(
                self, text="🚫 403 Forbidden\n\nAccess denied. Admin privileges required.",
                font=ctk.CTkFont(size=18, weight="bold"), text_color=DANGER
            ).pack(expand=True)
            return

        ctk.CTkButton(
            top, text="← Back", width=80, height=30,
            font=ctk.CTkFont(size=11), corner_radius=8,
            fg_color="#E9ECEF", hover_color="#CED4DA", text_color="#212529",
            command=self._go_back,
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            top, text="👥  User & Role Management",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Split Layout Container ──
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        main_container.columnconfigure(0, weight=7)
        main_container.columnconfigure(1, weight=3)
        main_container.rowconfigure(0, weight=1)

        self.left_col = ctk.CTkFrame(main_container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_CLR)
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.right_col = ctk.CTkFrame(main_container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_CLR)
        self.right_col.grid(row=0, column=1, sticky="nsew")

        self._build_table_area()
        self._build_form_area()

    def _build_table_area(self):
        ctx_title = ctk.CTkLabel(
            self.left_col, text="User List",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        ctx_title.pack(anchor="w", padx=20, pady=(20, 10))

        # Header
        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("User ID", 80), ("Username", 150), ("Roles", 150), 
            ("Status", 100), ("Actions", 160)
        ]
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text != "Actions" else "center"
            ).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading users...", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.loading_lbl.pack(pady=40)

    def _build_form_area(self):
        self.form_title = ctk.CTkLabel(
            self.right_col, text="Add User",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        self.form_title.pack(pady=(25, 5))

        ctk.CTkLabel(
            self.right_col, text="Create users and assign roles for system access",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        ).pack(pady=(0, 15))

        form_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True)

        def add_field(parent, label_text, placeholder, required=False):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=20, pady=(4, 8), fill="x")

            lbl_row = ctk.CTkFrame(row, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(0, 3))
            ctk.CTkLabel(lbl_row, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
            if required:
                ctk.CTkLabel(lbl_row, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w", height=15).pack(side="left")

            entry = ctk.CTkEntry(
                row, placeholder_text=placeholder, height=38, font=ctk.CTkFont(size=12),
                fg_color=INPUT_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
            )
            entry.pack(fill="x")
            entry.bind("<KeyRelease>", self._validate_form)
            return entry

        self.f_name = add_field(form_scroll, "Full Name", "E.g. John Doe", False)
        self.f_mobile = add_field(form_scroll, "Mobile Number", "10-digit number", False)
        self.f_username = add_field(form_scroll, "Username", "Unique identifier", True)
        self.f_email = add_field(form_scroll, "Email Address", "user@domain.com", True)
        
        # Password Field
        pw_row = ctk.CTkFrame(form_scroll, fg_color="transparent")
        pw_row.pack(padx=20, pady=(4, 8), fill="x")
        lbl_p_row = ctk.CTkFrame(pw_row, fg_color="transparent")
        lbl_p_row.pack(fill="x", pady=(0, 3))
        ctk.CTkLabel(lbl_p_row, text="Password", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
        ctk.CTkLabel(lbl_p_row, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w", height=15).pack(side="left")

        pw_container = ctk.CTkFrame(pw_row, fg_color=INPUT_BG, corner_radius=6, border_width=1, border_color=BORDER_CLR, height=38)
        pw_container.pack(fill="x")
        pw_container.pack_propagate(False)

        self.f_password = ctk.CTkEntry(
            pw_container, placeholder_text="Min 6 chars, letters & numbers", show="●",
            font=ctk.CTkFont(size=12), fg_color="transparent", border_width=0, text_color=TEXT_DARK
        )
        self.f_password.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.f_password.bind("<KeyRelease>", self._validate_form)

        self.btn_toggle_pw = ctk.CTkButton(
            pw_container, text="👁", width=30, height=30, fg_color="transparent", hover_color="#E5E7EB", text_color=TEXT_MUTED,
            command=self._toggle_password
        )
        self.btn_toggle_pw.pack(side="right", padx=(0, 5))
        
        self.f_confirm = add_field(form_scroll, "Confirm Password", "Re-enter password", True)

        # Combo fields
        def add_combo(parent, label_text, opts):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(padx=20, pady=(4, 8), fill="x")
            ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(fill="x", pady=(0, 3))
            combo = ctk.CTkComboBox(
                row, values=opts, height=38, font=ctk.CTkFont(size=12),
                fg_color=INPUT_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, button_color=ACCENT, button_hover_color=ACCENT
            )
            combo.pack(fill="x")
            combo.configure(command=lambda _: self._validate_form())
            return combo

        self.f_role = add_combo(form_scroll, "Role *", ["Admin", "Biller", "Accountant"])
        self.f_role.set("Biller")
        
        self.f_status = add_combo(form_scroll, "Status *", ["Active", "Inactive"])
        self.f_status.set("Active")

        self.user_lbl = ctk.CTkLabel(form_scroll, text="", font=ctk.CTkFont(size=11, slant="italic"), text_color=TEXT_MUTED)
        self.user_lbl.pack(pady=5)

        # Buttons
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.save_btn = ctk.CTkButton(
            btn_frame, text="Create User", height=42,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
            fg_color="#D1D5DB", hover_color="#D1D5DB", text_color="#FFFFFF",
            command=self._save_user, state="disabled"
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.clear_btn = ctk.CTkButton(
            btn_frame, text="Reset", height=42,
            font=ctk.CTkFont(size=13), corner_radius=10,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._clear_form
        )
        self.clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _toggle_password(self):
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.f_password.configure(show="")
            self.f_confirm.configure(show="")
            self.btn_toggle_pw.configure(text="🔓")
        else:
            self.f_password.configure(show="●")
            self.f_confirm.configure(show="●")
            self.btn_toggle_pw.configure(text="👁")

    def _validate_form(self, event=None):
        name = self.f_name.get().strip()
        mobile = self.f_mobile.get().strip()
        user = self.f_username.get().strip()
        em = self.f_email.get().strip()
        pw = self.f_password.get()
        cpw = self.f_confirm.get()
        role = self.f_role.get()

        errors = []

        # Name
        if name:
            if re.match(r"^[a-zA-Z\s]{1,50}$", name):
                self.f_name.configure(border_color=SUCCESS)
            else:
                self.f_name.configure(border_color=DANGER)
                errors.append("Name should contain only letters")
        else:
            self.f_name.configure(border_color=BORDER_CLR)

        # Mobile
        if mobile:
            if re.match(r"^[6-9]\d{9}$", mobile):
                self.f_mobile.configure(border_color=SUCCESS)
            else:
                self.f_mobile.configure(border_color=DANGER)
                errors.append("Valid 10-digit mobile number starting with 6-9")
        else:
            self.f_mobile.configure(border_color=BORDER_CLR)

        # Username
        if len(user) >= 3 and " " not in user:
            self.f_username.configure(border_color=SUCCESS)
        else:
            if user:
                self.f_username.configure(border_color=DANGER)
            else:
                self.f_username.configure(border_color=BORDER_CLR)
            errors.append("Username min 3 chars, no spaces")

        # Email
        if em and re.match(r"^[^@]+@[^@]+\.[^@]+$", em):
            self.f_email.configure(border_color=SUCCESS)
        else:
            if em:
                self.f_email.configure(border_color=DANGER)
            else:
                self.f_email.configure(border_color=BORDER_CLR)
            errors.append("Valid email required")

        # Password
        if self.editing_user_id and not pw:
            # OK to leave blank on edit
            self.f_password.master.configure(border_color=BORDER_CLR)
            self.f_confirm.configure(border_color=BORDER_CLR)
        else:
            if len(pw) >= 6 and re.search(r"[a-zA-Z]", pw) and re.search(r"\d", pw):
                self.f_password.master.configure(border_color=SUCCESS)
            else:
                if pw:
                    self.f_password.master.configure(border_color=DANGER)
                else: 
                    self.f_password.master.configure(border_color=BORDER_CLR)
                errors.append("Password must have letter+number (min 6)")
                
            if pw == cpw and pw:
                self.f_confirm.configure(border_color=SUCCESS)
            else:
                if cpw:
                    self.f_confirm.configure(border_color=DANGER)
                else:
                    self.f_confirm.configure(border_color=BORDER_CLR)
                errors.append("Passwords must match")

        if not role:
            errors.append("Role is required")

        if errors:
            self.user_lbl.configure(text=errors[-1], text_color=DANGER)
            self.save_btn.configure(state="disabled", fg_color="#D1D5DB", hover_color="#D1D5DB")
        else:
            self.user_lbl.configure(text="Form Valid", text_color=SUCCESS)
            self.save_btn.configure(state="normal", fg_color=SUCCESS, hover_color="#059669")

    def _load_data(self):
        # Clear previous rows from the scroll, safely
        for widget in self.scroll.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass
                
        def fetch_users():
            return get_all_users_with_roles(self.user["distributor_id"])
            
        def on_success(result):
            self.all_users = result

            if not self.all_users:
                ctk.CTkLabel(self.scroll, text="No users found.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
                return

            for row in self.all_users:
                frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
                frame.pack(fill="x", pady=2)
                frame.pack_propagate(False)
                ctk.CTkFrame(self.scroll, fg_color="#F3F4F6", height=1).pack(fill="x", padx=10)

                user_id = row.get("user_id")
                username = str(row.get("username", ""))
                roles_str = ", ".join(row.get("roles", [])) or "No Role"
                status = str(row.get("status", "active"))

                st_color = SUCCESS if status.lower() == "active" else DANGER

                vals = [
                    (f"U_{user_id:03d}", 80, TEXT_DARK),
                    (username, 150, TEXT_DARK),
                    (roles_str, 150, "#4B5563"),
                    (status.title(), 100, st_color)
                ]

                for val, w, color in vals:
                    ctk.CTkLabel(
                        frame, text=val, width=w, font=ctk.CTkFont(size=12, weight="bold" if w==100 else "normal"),
                        text_color=color, anchor="w"
                    ).pack(side="left", padx=5)

                # Actions
                action_frame = ctk.CTkFrame(frame, width=160, fg_color="transparent")
                action_frame.pack_propagate(False)
                action_frame.pack(side="left", padx=5, pady=5)
                
                ctk.CTkButton(
                    action_frame, text="✎", width=36, height=28,
                    font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6,
                    fg_color="#DBEAFE", hover_color="#BFDBFE", text_color="#1E3A8A",
                    command=lambda r=row: self._start_edit(r)
                ).pack(side="left", padx=(0, 4))
                
                if user_id != self.user.get("user_id"):
                    if status.lower() == "active":
                        ctk.CTkButton(
                            action_frame, text="Deactivate", width=95, height=28,
                            font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6,
                            fg_color="#FEE2E2", hover_color="#FECACA", text_color="#991B1B",
                            command=lambda u=user_id: self._toggle_status(u, "inactive")
                        ).pack(side="left")
                    else:
                        ctk.CTkButton(
                            action_frame, text="Activate", width=95, height=28,
                            font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6,
                            fg_color="#D1FAE5", hover_color="#A7F3D0", text_color="#065F46",
                            command=lambda u=user_id: self._toggle_status(u, "active")
                        ).pack(side="left")

        def on_error(e):
            self.all_users = []
            ctk.CTkLabel(self.scroll, text=f"Failed to load users: {e}", font=ctk.CTkFont(size=13), text_color=DANGER).pack(pady=40)
                        
        async_db_call(self, fetch_users, (), on_success, on_error)

    def _start_edit(self, row):
        self._clear_form()
        self.editing_user_id = row["user_id"]
        
        self.form_title.configure(text="Edit User")
        self.save_btn.configure(text="Update User")
        
        self.f_username.insert(0, row.get("username", ""))
        self.f_username.configure(state="disabled", fg_color="#E5E7EB", text_color=TEXT_MUTED)
        
        self.f_name.insert(0, row.get("name") or "")
        self.f_mobile.insert(0, row.get("mobile_no") or "")
        self.f_email.insert(0, row.get("email") or "")
        
        roles = row.get("roles", [])
        if roles:
            self.f_role.set(roles[0])
            
        self.f_status.set(str(row.get("status", "active")).title())
        
        self.user_lbl.configure(text="Leave password blank to keep current.", text_color=TEXT_MUTED)
        self._validate_form()

    def _clear_form(self):
        self.editing_user_id = None
        self.form_title.configure(text="Add User")
        self.save_btn.configure(text="Create User")
        self.user_lbl.configure(text="")
        
        self.f_username.configure(state="normal", fg_color=INPUT_BG, text_color=TEXT_DARK)
        
        for e in [self.f_name, self.f_mobile, self.f_username, self.f_email, self.f_password, self.f_confirm]:
            e.delete(0, "end")
            try:
                e.configure(border_color=BORDER_CLR)
            except ValueError:
                pass
        self.f_password.master.configure(border_color=BORDER_CLR)
            
        self.f_role.set("Biller")
        self.f_status.set("Active")
        self._validate_form()

    def _save_user(self):
        name = self.f_name.get().strip()
        mob = self.f_mobile.get().strip()
        uname = self.f_username.get().strip()
        em = self.f_email.get().strip()
        pw = self.f_password.get()
        role = self.f_role.get()
        stat = self.f_status.get().lower()

        if self.editing_user_id:
            if not messagebox.askyesno("Confirm Update", "Are you sure you want to update this user?"):
                return
            try:
                update_user(self.user.get("role", ""), self.editing_user_id, role, em, name, mob, stat, pw if pw else None)
                messagebox.showinfo("Success", "User updated successfully.")
                self._clear_form()
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update user: {e}")
        else:
            if not messagebox.askyesno("Confirm Creation", "Are you sure you want to create this user?"):
                return
            try:
                create_user(self.user.get("role", ""), self.user["distributor_id"], uname, role, em, pw, name, mob, stat)
                messagebox.showinfo("Success", "User created successfully.")
                self._clear_form()
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create user: {e}")

    def _toggle_status(self, user_id, new_status):
        action = "deactivate" if new_status == "inactive" else "activate"
        if messagebox.askyesno("Confirm", f"Are you sure you want to {action} this user?"):
            try:
                update_user_status(self.user.get("role", ""), user_id, new_status)
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Could not {action} user: {e}")

    def _go_back(self):
        self.app.switch_view("Dashboard")
