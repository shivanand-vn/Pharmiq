"""
Login Window — CustomTkinter login screen for PharmIQ.
Authenticates users and passes context to the dashboard.
"""

import customtkinter as ctk
from tkinter import messagebox
from db.connection import fetch_one


class LoginWindow(ctk.CTkToplevel):
    """Login window for PharmIQ application."""

    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success

        # ── Window setup ──
        self.title("PharmIQ — Login")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(fg_color="#0f0f1a")

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 480) // 2
        y = (self.winfo_screenheight() - 520) // 2
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    def _build_ui(self):
        # ── Branding header ──
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="💊 PharmIQ",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#00d4ff",
        ).pack(pady=(20, 0))
        ctk.CTkLabel(
            header, text="Pharmaceutical Distribution Management",
            font=ctk.CTkFont(size=11), text_color="#888899",
        ).pack(pady=(2, 10))

        # ── Card frame ──
        card = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=16, border_width=1, border_color="#2a2a4a")
        card.pack(padx=40, pady=30, fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Sign In",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#ffffff",
        ).pack(pady=(30, 5))
        ctk.CTkLabel(
            card, text="Enter your credentials to continue",
            font=ctk.CTkFont(size=11), text_color="#888899",
        ).pack(pady=(0, 20))

        # Username
        ctk.CTkLabel(card, text="Username", font=ctk.CTkFont(size=12), text_color="#aabbcc",
                      anchor="w").pack(padx=30, anchor="w")
        self.username_entry = ctk.CTkEntry(
            card, placeholder_text="Enter username", height=40,
            font=ctk.CTkFont(size=13), corner_radius=10,
            fg_color="#0f0f1a", border_color="#2a2a4a", text_color="#ffffff",
        )
        self.username_entry.pack(padx=30, fill="x", pady=(4, 12))

        # Password
        ctk.CTkLabel(card, text="Password", font=ctk.CTkFont(size=12), text_color="#aabbcc",
                      anchor="w").pack(padx=30, anchor="w")
        self.password_entry = ctk.CTkEntry(
            card, placeholder_text="Enter password", show="●", height=40,
            font=ctk.CTkFont(size=13), corner_radius=10,
            fg_color="#0f0f1a", border_color="#2a2a4a", text_color="#ffffff",
        )
        self.password_entry.pack(padx=30, fill="x", pady=(4, 20))

        # Login button
        self.login_btn = ctk.CTkButton(
            card, text="Login", height=42,
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10,
            fg_color="#00d4ff", hover_color="#00a8cc", text_color="#0f0f1a",
            command=self._do_login,
        )
        self.login_btn.pack(padx=30, fill="x", pady=(5, 15))

        # Status label
        self.status_label = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=11), text_color="#ff4444",
        )
        self.status_label.pack(pady=(0, 15))

        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self._do_login())
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())

    def _do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.status_label.configure(text="Please enter both username and password.")
            return

        self.login_btn.configure(state="disabled", text="Authenticating...")
        self.update()

        try:
            user = fetch_one(
                """
                SELECT u.user_id, u.distributor_id, u.username, u.status
                FROM users u
                WHERE u.username = %s AND u.password = %s AND u.status = 'active'
                """,
                (username, password),
            )
            if user:
                # Check license
                license_info = fetch_one(
                    """
                    SELECT * FROM licenses
                    WHERE distributor_id = %s AND status = 'active'
                      AND expiry_date >= CURDATE()
                    ORDER BY expiry_date DESC LIMIT 1
                    """,
                    (user["distributor_id"],),
                )
                if license_info:
                    self.on_login_success(user)
                    self.destroy()
                else:
                    self.status_label.configure(text="License expired or inactive. Contact admin.")
            else:
                self.status_label.configure(text="Invalid username or password.")
        except Exception as e:
            self.status_label.configure(text=f"Database error: {str(e)[:50]}")
        finally:
            self.login_btn.configure(state="normal", text="Login")

    def _on_close(self):
        self.master.destroy()
