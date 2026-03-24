"""
PharmIQ — Main Application Entry Point
Pharmaceutical Distribution Management System
"""

import customtkinter as ctk
from tkinter import messagebox
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import init_database
from ui.login_window import LoginWindow
from ui.dashboard import Dashboard


class PharmIQApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # ── Window setup ──
        self.title("PharmIQ — Pharmaceutical Distribution Management")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color="#0f0f1a")

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1200) // 2
        y = (self.winfo_screenheight() - 750) // 2
        self.geometry(f"+{x}+{y}")

        # App state
        self.current_user = None
        self.current_frame = None

        # CustomTkinter appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── Initialize database ──
        self._init_db()

        # ── Show login ──
        self.show_login()

    def _init_db(self):
        """Initialize the database schema and seed data."""
        try:
            init_database()
        except Exception as e:
            messagebox.showerror(
                "Database Error",
                f"Could not connect to MySQL database.\n\n"
                f"Please ensure MySQL is running and update db/config.py.\n\n"
                f"Error: {e}"
            )
            self.destroy()
            sys.exit(1)

    def show_login(self):
        """Show the login window."""
        self.current_user = None
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

        # Show login window directly in main frame
        self.current_frame = LoginWindow(self, on_login_success=self._on_login)
        self.current_frame.pack(fill="both", expand=True)

    def _on_login(self, user):
        """Handle successful login."""
        self.current_user = user

        # Remove placeholder
        if self.current_frame:
            self.current_frame.destroy()

        # Show dashboard
        self.current_frame = Dashboard(self, user, self)
        self.current_frame.pack(fill="both", expand=True)

    def show_dashboard(self):
        """Refresh dashboard."""
        if self.current_user:
            if self.current_frame:
                self.current_frame.destroy()
            self.current_frame = Dashboard(self, self.current_user, self)
            self.current_frame.pack(fill="both", expand=True)


def main():
    app = PharmIQApp()
    app.mainloop()


if __name__ == "__main__":
    main()
