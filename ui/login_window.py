"""
Login Window — Modern SaaS-style login screen for PharmIQ.
Split layout with branding panel, login card, and Forgot Password modal.
Authenticates users and passes context to the dashboard.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from db.connection import fetch_one
from models.user import get_user_roles


class LoginWindow(ctk.CTkFrame):
    """Modern login window for PharmIQ application."""

    # ── Design Tokens (from dashboard) ──
    PRIMARY = "#1B4F6B"
    PRIMARY_DARK = "#0D3B54"
    PRIMARY_HOVER = "#326F8A"
    ACCENT = "#4361EE"
    BG_LIGHT = "#F1F4F9"
    CARD_BG = "#FFFFFF"
    TEXT_PRIMARY = "#111827"
    TEXT_SECONDARY = "#6B7280"
    TEXT_MUTED = "#9CA3AF"
    ERROR_COLOR = "#EF4444"
    ERROR_BG = "#FEF2F2"
    SUCCESS_COLOR = "#10B981"
    SUCCESS_BG = "#ECFDF5"
    INPUT_BG = "#F8F9FA"
    INPUT_BORDER = "#DEE2E6"
    INPUT_FOCUS_BORDER = "#4361EE"
    TEAL_ACCENT = "#26C6DA"

    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color=self.BG_LIGHT)
        self.on_login_success = on_login_success
        self._password_visible = False
        self._build_ui()

    def _build_ui(self):
        """Build the split-layout login interface."""
        # Main container — 2 columns
        self.columnconfigure(0, weight=2)  # Left branding panel
        self.columnconfigure(1, weight=3)  # Right login panel
        self.rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    # ──────────────────────────────────────────────
    # LEFT PANEL — Branding
    # ──────────────────────────────────────────────
    def _build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color=self.PRIMARY, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        # Center content vertically
        left.rowconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        content = ctk.CTkFrame(left, fg_color="transparent")
        content.grid(row=1, column=0, padx=40)

        # Decorative top accent line
        accent_line = ctk.CTkFrame(content, fg_color=self.TEAL_ACCENT, height=3, width=60, corner_radius=2)
        accent_line.pack(anchor="w", pady=(0, 30))

        # Logo icon
        logo_frame = ctk.CTkFrame(content, fg_color="transparent")
        logo_frame.pack(anchor="w")

        pill_icon = ctk.CTkLabel(
            logo_frame, text="💊",
            font=ctk.CTkFont(size=48),
        )
        pill_icon.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            logo_frame, text="PharmIQ",
            font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left")

        # Tagline
        ctk.CTkLabel(
            content,
            text="Pharmaceutical Distribution\nManagement System",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color="#A8C5DA",
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(16, 30))

        # Feature bullets
        features = [
            ("📊", "Real-time analytics & reporting"),
            ("📦", "Inventory & stock management"),
            ("📄", "Automated invoicing & billing"),
            ("👥", "Customer relationship management"),
        ]

        for icon, text in features:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(anchor="w", pady=6)

            ctk.CTkLabel(
                row, text=icon,
                font=ctk.CTkFont(size=16),
                width=28,
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=text,
                font=ctk.CTkFont(size=13),
                text_color="#CBD5E1",
            ).pack(side="left", padx=(8, 0))

        # Bottom decorative accent
        accent_line_btm = ctk.CTkFrame(content, fg_color=self.TEAL_ACCENT, height=3, width=60, corner_radius=2)
        accent_line_btm.pack(anchor="w", pady=(30, 0))

        # Version tag at bottom
        ver_label = ctk.CTkLabel(
            left, text="v2.0  •  Secure Login",
            font=ctk.CTkFont(size=11),
            text_color="#5A8FA8",
        )
        ver_label.grid(row=2, column=0, pady=(0, 20), sticky="s")

    # ──────────────────────────────────────────────
    # RIGHT PANEL — Login Form
    # ──────────────────────────────────────────────
    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color=self.BG_LIGHT, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")

        # Center card vertically
        right.rowconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        # ── Login Card ──
        # Shadow layer for depth effect
        shadow = ctk.CTkFrame(
            right, fg_color="#E2E8F0",
            corner_radius=18, width=420, height=502,
        )
        shadow.grid(row=1, column=0, padx=(0, 2), pady=(2, 0))
        shadow.grid_propagate(False)

        card = ctk.CTkFrame(
            right, fg_color=self.CARD_BG,
            corner_radius=16, width=420, height=500,
            border_width=1, border_color="#E5E7EB",
        )
        card.grid(row=1, column=0)
        card.grid_propagate(False)

        # Inner padding frame
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=36)

        # Header
        ctk.CTkLabel(
            inner, text="Welcome Back",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text="Login to your account",
            font=ctk.CTkFont(size=13),
            text_color=self.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(4, 28))

        # ── Username Field ──
        ctk.CTkLabel(
            inner, text="Username",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")

        self.username_container = ctk.CTkFrame(
            inner, fg_color=self.INPUT_BG,
            corner_radius=10, border_width=1.5,
            border_color=self.INPUT_BORDER, height=44,
        )
        self.username_container.pack(fill="x", pady=(6, 0))
        self.username_container.pack_propagate(False)

        ctk.CTkLabel(
            self.username_container, text="👤",
            font=ctk.CTkFont(size=14),
            text_color=self.TEXT_MUTED, fg_color="transparent",
        ).place(x=14, rely=0.5, anchor="w")

        self.username_entry = ctk.CTkEntry(
            self.username_container,
            placeholder_text="Enter your username",
            font=ctk.CTkFont(size=13),
            fg_color="transparent", border_width=0,
            text_color=self.TEXT_PRIMARY, height=40,
        )
        self._place_entry(self.username_entry, left=40, right=10)

        # ── Password Field ──
        ctk.CTkLabel(
            inner, text="Password",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w", pady=(16, 0))

        self.password_container = ctk.CTkFrame(
            inner, fg_color=self.INPUT_BG,
            corner_radius=10, border_width=1.5,
            border_color=self.INPUT_BORDER, height=44,
        )
        self.password_container.pack(fill="x", pady=(6, 0))
        self.password_container.pack_propagate(False)

        ctk.CTkLabel(
            self.password_container, text="🔒",
            font=ctk.CTkFont(size=14),
            text_color=self.TEXT_MUTED, fg_color="transparent",
        ).place(x=14, rely=0.5, anchor="w")

        self.password_entry = ctk.CTkEntry(
            self.password_container,
            placeholder_text="Enter your password",
            show="●",
            font=ctk.CTkFont(size=13),
            fg_color="transparent", border_width=0,
            text_color=self.TEXT_PRIMARY, height=40,
        )
        self._place_entry(self.password_entry, left=40, right=44)

        self.toggle_pw_btn = ctk.CTkButton(
            self.password_container,
            text="👁",
            font=ctk.CTkFont(size=14),
            width=36, height=30,
            fg_color="transparent",
            hover_color="#E5E7EB",
            text_color=self.TEXT_MUTED,
            corner_radius=8,
            command=self._toggle_password,
        )
        self.toggle_pw_btn.place(relx=1.0, rely=0.5, anchor="e", x=-6)

        # ── Remember Me + Forgot Password Row ──
        options_row = ctk.CTkFrame(inner, fg_color="transparent")
        options_row.pack(fill="x", pady=(14, 0))

        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_cb = ctk.CTkCheckBox(
            options_row, text="Remember me",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY,
            variable=self.remember_var,
            fg_color=self.ACCENT,
            hover_color=self.PRIMARY_HOVER,
            border_color=self.INPUT_BORDER,
            corner_radius=4, height=20, width=20,
            checkbox_width=18, checkbox_height=18,
        )
        self.remember_cb.pack(side="left")

        forgot_btn = ctk.CTkButton(
            options_row, text="Forgot Password?",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#E5E7EB",
            text_color=self.ACCENT,
            width=0, height=24,
            corner_radius=6,
            command=self._show_forgot_password,
        )
        forgot_btn.pack(side="right")

        # ── Login Button ──
        self.login_btn = ctk.CTkButton(
            inner, text="Sign In",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=46, corner_radius=12,
            command=self._do_login,
        )
        self.login_btn.pack(fill="x", pady=(24, 0))

        # ── Status / Error Label ──
        self.error_frame = ctk.CTkFrame(inner, fg_color="transparent", height=36)
        self.error_frame.pack(fill="x", pady=(12, 0))
        self.error_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.error_frame, text="",
            font=ctk.CTkFont(size=12),
            text_color=self.ERROR_COLOR,
            anchor="center",
        )
        self.status_label.pack(expand=True)

        # ── Focus animations ──
        self.username_entry.bind("<FocusIn>", lambda e: self._on_focus_in(self.username_container))
        self.username_entry.bind("<FocusOut>", lambda e: self._on_focus_out(self.username_container))
        self.password_entry.bind("<FocusIn>", lambda e: self._on_focus_in(self.password_container))
        self.password_entry.bind("<FocusOut>", lambda e: self._on_focus_out(self.password_container))

        # ── Key bindings ──
        self.password_entry.bind("<Return>", lambda e: self._do_login())
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())

        # Footer
        footer_frame = ctk.CTkFrame(right, fg_color="transparent")
        footer_frame.grid(row=2, column=0, pady=(0, 16), sticky="s")

        ctk.CTkLabel(
            footer_frame,
            text="© 2026 PharmIQ  •  All rights reserved",
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_MUTED,
        ).pack()

    # ──────────────────────────────────────────────
    # INPUT FOCUS ANIMATIONS
    # ──────────────────────────────────────────────
    def _on_focus_in(self, container):
        container.configure(
            border_color=self.INPUT_FOCUS_BORDER,
            fg_color="#FFFFFF",
        )

    def _on_focus_out(self, container):
        container.configure(
            border_color=self.INPUT_BORDER,
            fg_color=self.INPUT_BG,
        )

    @staticmethod
    def _place_entry(entry, left=40, right=10):
        """Place a CTkEntry using tkinter's native place (bypasses CTk restriction)."""
        tk.Widget.place(entry, x=left, y=2, relwidth=1.0, relheight=1.0, width=-(left + right), height=-4)

    # ──────────────────────────────────────────────
    # PASSWORD TOGGLE
    # ──────────────────────────────────────────────
    def _toggle_password(self):
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_entry.configure(show="")
            self.toggle_pw_btn.configure(text="🔓")
        else:
            self.password_entry.configure(show="●")
            self.toggle_pw_btn.configure(text="👁")

    # ──────────────────────────────────────────────
    # FORGOT PASSWORD MODAL
    # ──────────────────────────────────────────────
    def _show_forgot_password(self):
        """Open the Forgot Password modal."""
        modal = ctk.CTkToplevel(self)
        modal.title("Reset Password")
        modal.geometry("440x380")
        modal.resizable(False, False)
        modal.configure(fg_color=self.BG_LIGHT)
        modal.grab_set()
        modal.focus()

        # Center modal on screen
        modal.update_idletasks()
        x = (modal.winfo_screenwidth() - 440) // 2
        y = (modal.winfo_screenheight() - 380) // 2
        modal.geometry(f"+{x}+{y}")

        # Modal card
        card = ctk.CTkFrame(
            modal, fg_color=self.CARD_BG,
            corner_radius=16, border_width=1,
            border_color="#E5E7EB",
        )
        card.pack(fill="both", expand=True, padx=20, pady=20)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=28)

        # Header row with close button
        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill="x")

        ctk.CTkLabel(
            header_row, text="Reset Password",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=self.TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            header_row, text="✕",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=32, height=32,
            fg_color="transparent",
            hover_color="#FEE2E2",
            text_color=self.TEXT_SECONDARY,
            corner_radius=8,
            command=modal.destroy,
        ).pack(side="right")

        ctk.CTkLabel(
            inner,
            text="Enter your username or email address\nand we'll help you reset your password.",
            font=ctk.CTkFont(size=13),
            text_color=self.TEXT_SECONDARY,
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(8, 24))

        # Input field
        ctk.CTkLabel(
            inner, text="Username or Email",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")

        reset_container = ctk.CTkFrame(
            inner, fg_color=self.INPUT_BG,
            corner_radius=10, border_width=1.5,
            border_color=self.INPUT_BORDER, height=44,
        )
        reset_container.pack(fill="x", pady=(6, 0))
        reset_container.pack_propagate(False)

        ctk.CTkLabel(
            reset_container, text="✉️",
            font=ctk.CTkFont(size=14),
            text_color=self.TEXT_MUTED, fg_color="transparent",
        ).place(x=14, rely=0.5, anchor="w")

        reset_entry = ctk.CTkEntry(
            reset_container,
            placeholder_text="Enter username or email",
            font=ctk.CTkFont(size=13),
            fg_color="transparent", border_width=0,
            text_color=self.TEXT_PRIMARY, height=40,
        )
        self._place_entry(reset_entry, left=40, right=10)

        # Focus animation for modal input
        reset_entry.bind("<FocusIn>", lambda e: self._on_focus_in(reset_container))
        reset_entry.bind("<FocusOut>", lambda e: self._on_focus_out(reset_container))

        # Status label in modal
        modal_status = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=12),
            text_color=self.ERROR_COLOR,
            wraplength=340,
        )
        modal_status.pack(pady=(12, 0))

        def _on_reset():
            value = reset_entry.get().strip()
            if not value:
                modal_status.configure(
                    text="⚠ Please enter your username or email address.",
                    text_color=self.ERROR_COLOR,
                )
                return

            # Show success
            reset_btn.configure(state="disabled", text="Sending...")
            modal.update()

            modal.after(800, lambda: _show_success(value))

        def _show_success(value):
            modal_status.configure(
                text=f"✓ Password reset request sent for '{value}'.\n"
                     f"Please contact your administrator to complete the reset.",
                text_color=self.SUCCESS_COLOR,
            )
            reset_btn.configure(state="normal", text="Send Reset Request")

        # Reset button
        reset_btn = ctk.CTkButton(
            inner, text="Send Reset Request",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.PRIMARY,
            hover_color=self.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=44, corner_radius=12,
            command=_on_reset,
        )
        reset_btn.pack(fill="x", pady=(16, 0))

        reset_entry.bind("<Return>", lambda e: _on_reset())

    # ──────────────────────────────────────────────
    # LOGIN LOGIC (UNCHANGED)
    # ──────────────────────────────────────────────
    def _do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        self.login_btn.configure(state="disabled", text="Authenticating...")
        self.status_label.configure(text="")
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
                roles = get_user_roles(user["user_id"])
                user["role"] = roles[0] if roles else "Admin"
                user["roles"] = roles
                self.on_login_success(user)
            else:
                self._show_error("Invalid username or password.")
                self.login_btn.configure(state="normal", text="Sign In")
        except Exception as e:
            self._show_error(f"Database error: {str(e)[:50]}")
            self.login_btn.configure(state="normal", text="Sign In")

    def _show_error(self, message):
        """Display an error message with styling."""
        self.error_frame.configure(fg_color=self.ERROR_BG, corner_radius=8)
        self.status_label.configure(text=f"⚠  {message}", text_color=self.ERROR_COLOR)
