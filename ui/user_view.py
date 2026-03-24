"""
User View — CustomTkinter frame for managing users and roles.
"""

import customtkinter as ctk
from tkinter import messagebox
from models.user import get_all_users_with_roles, update_user_status

# ── Colour palette ──
BG_DARK = "#F8F9FA"
CARD_BG = "#212529"
BORDER_CLR = "#DEE2E6"
ACCENT = "#4361EE"
TEXT_WHITE = "#212529"
TEXT_MUTED = "#868E96"
SUCCESS = "#2DC653"
DANGER = "#EF233C"


class UserView(ctk.CTkFrame):
    """View to list, search, and manage users and their roles."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref
        
        self.all_users = []
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
            top, text="👥  User & Role Management",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(15, 5))

        # Add User Button
        ctk.CTkButton(
            toolbar, text="+ Add User", height=35, font=ctk.CTkFont(size=12, weight="bold"), 
            corner_radius=8, fg_color=SUCCESS, hover_color="#208B3A", text_color="#FFFFFF",
            command=self._add_user
        ).pack(side="right")

        # ── Table Area ──
        table_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color=BORDER_CLR)
        table_container.pack(fill="both", expand=True, padx=15, pady=(10, 20))

        # Header
        header = ctk.CTkFrame(table_container, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        cols = [
            ("User ID", 100), ("Username", 200), ("Roles", 250), 
            ("Status", 120), ("Actions", 150)
        ]
        
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#4B5563", anchor="w" if text != "Actions" else "center"
            ).pack(side="left", padx=5)

        self.scroll = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_data(self):
        try:
            self.all_users = get_all_users_with_roles(self.user["distributor_id"])
        except Exception as e:
            self.all_users = []
            print(f"Error loading users: {e}")

        for widget in self.scroll.winfo_children():
            widget.destroy()

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
            status = str(row.get("status", "active")).title()

            vals = [
                (str(user_id), 100, TEXT_WHITE),
                (username, 200, TEXT_WHITE),
                (roles_str, 250, "#4B5563"),
                (status, 120, SUCCESS if status=="Active" else DANGER)
            ]

            for val, w, color in vals:
                ctk.CTkLabel(
                    frame, text=val, width=w, font=ctk.CTkFont(size=12, weight="bold" if w==120 else "normal"),
                    text_color=color, anchor="w"
                ).pack(side="left", padx=5)

            # Actions
            action_frame = ctk.CTkFrame(frame, width=150, fg_color="transparent")
            action_frame.pack_propagate(False)
            action_frame.pack(side="left", padx=5, pady=5)
            
            # Don't let user deactivate themselves if they are admin
            if user_id != self.user.get("user_id"):
                if status == "Active":
                    ctk.CTkButton(
                        action_frame, text="Deactivate", width=100, height=28,
                        font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6,
                        fg_color="#FEE2E2", hover_color="#FECACA", text_color="#991B1B",
                        command=lambda u=user_id: self._toggle_status(u, "inactive")
                    ).pack(expand=True)
                else:
                    ctk.CTkButton(
                        action_frame, text="Activate", width=100, height=28,
                        font=ctk.CTkFont(size=10, weight="bold"), corner_radius=6,
                        fg_color="#D1FAE5", hover_color="#A7F3D0", text_color="#065F46",
                        command=lambda u=user_id: self._toggle_status(u, "active")
                    ).pack(expand=True)
            else:
                ctk.CTkLabel(action_frame, text="Current User", font=ctk.CTkFont(size=11, slant="italic"), text_color=TEXT_MUTED).pack(expand=True)

    def _toggle_status(self, user_id, new_status):
        action = "deactivate" if new_status == "inactive" else "activate"
        if messagebox.askyesno("Confirm", f"Are you sure you want to {action} this user?"):
            try:
                update_user_status(user_id, new_status)
                self._load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Could not {action} user: {e}")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children():
            widget.destroy()
        dashboard = Dashboard(self.master, self.user, self.app)
        dashboard.pack(fill="both", expand=True)
        
    def _add_user(self):
        from ui.add_user_form import AddUserForm
        for widget in self.master.winfo_children():
            widget.destroy()
        form = AddUserForm(self.master, self.user, self.app)
        form.pack(fill="both", expand=True)
