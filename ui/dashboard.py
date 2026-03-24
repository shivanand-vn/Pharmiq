"""
Dashboard — Main window after login with distributor branding.
Redesigned to match Pharmiq UI reference.
"""

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image as PILImage
import os
import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from models.distributor import get_distributor_by_id
from models.invoice import get_invoices_by_distributor


class Dashboard(ctk.CTkFrame):
    """Main dashboard frame showing distributor branding and navigation, redesigned."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color="#F1F4F9")
        self.user = user_context
        self.app = app_ref
        self.distributor = get_distributor_by_id(self.user["distributor_id"])

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        # Sidebar Container
        sidebar_bg = "#1B4F6B"  # Teal/Blue primary color
        self.sidebar = ctk.CTkFrame(self, fg_color=sidebar_bg, corner_radius=0, width=240)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo and Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(25, 30), padx=20, anchor="w", fill="x")
        
        # Pill placeholder for logo icon
        logo_icon = ctk.CTkLabel(logo_frame, text="💊", font=ctk.CTkFont(size=24))
        logo_icon.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            logo_frame, text="Pharmiq",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#FFFFFF"
        ).pack(side="left")

        # Navigation Items
        nav_items = [
            ("Dashboard", "layout", True),
            ("Customers", "store", False),
            ("Products", "box", False),
            ("Billing/Invoices", "file-text", False),
            ("Inventory/Stock", "package", False),
            ("Reports & Analytics", "bar-chart", False),
            ("Users & Roles", "users", False),
            ("Settings", "settings", False)
        ]

        # Use unicode characters as simple icons or simple text
        icons = {
            "layout": "⊞", "store": "🏪", "box": "📦", "file-text": "📄",
            "package": "🗃️", "bar-chart": "📊", "users": "👥", "settings": "⚙️"
        }

        for title, icon_key, is_active in nav_items:
            bg_color = "#326F8A" if is_active else "transparent"
            hover_color = "#326F8A"
            text_color = "#FFFFFF" if is_active else "#A8C5DA"
            
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icons.get(icon_key, '')}  {title}",
                font=ctk.CTkFont(size=14, weight="bold" if is_active else "normal"),
                fg_color=bg_color,
                hover_color=hover_color,
                text_color=text_color,
                anchor="w",
                height=45,
                corner_radius=8,
            )
            btn.pack(pady=4, padx=15, fill="x")

        # Bottom Profile Section
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", pady=20, padx=15, fill="x")
        
        # Dummy avatar
        avatar_lbl = ctk.CTkLabel(
            bottom_frame, text="👤", width=36, height=36, 
            fg_color="#F8B195", corner_radius=18, text_color="#FFFFFF"
        )
        avatar_lbl.pack(side="left", padx=(0, 10))
        
        user_name = self.user.get('username', 'Admin User')
        ctk.CTkLabel(
            bottom_frame, text=user_name,
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF"
        ).pack(side="left")
        
        ctk.CTkButton(
            bottom_frame, text="˅", width=20, fg_color="transparent", 
            text_color="#FFFFFF", hover_color="#326F8A", command=self._logout
        ).pack(side="right")

    def _build_main_area(self):
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=0, column=1, sticky="nsew", padx=25, pady=(15, 25))
        
        main_content.columnconfigure(0, weight=7)
        main_content.columnconfigure(1, weight=3)
        main_content.rowconfigure(1, weight=1)

        # 1. Top Header
        header_frame = ctk.CTkFrame(main_content, fg_color="transparent", height=50)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        header_frame.pack_propagate(False)

        # Search bar
        search_entry = ctk.CTkEntry(
            header_frame, placeholder_text="🔍 Search customers, products, or orders...",
            width=400, height=40, corner_radius=20, border_width=0, fg_color="#FFFFFF",
            text_color="#495057"
        )
        search_entry.pack(side="left")

        # Right Icons
        right_icons = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_icons.pack(side="right")

        ctk.CTkLabel(right_icons, text="🔔", font=ctk.CTkFont(size=20), text_color="#6C757D").pack(side="left", padx=10)
        ctk.CTkLabel(right_icons, text="❓", font=ctk.CTkFont(size=20), text_color="#6C757D").pack(side="left", padx=10)
        
        prof_frame = ctk.CTkFrame(right_icons, fg_color="transparent")
        prof_frame.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(prof_frame, text="👤", width=32, height=32, corner_radius=16, fg_color="#F8B195").pack(side="left")
        info = ctk.CTkFrame(prof_frame, fg_color="transparent")
        info.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(info, text="Admin", font=ctk.CTkFont(size=13, weight="bold"), text_color="#212529", height=15).pack(anchor="w")
        ctk.CTkLabel(info, text="Pharmiq", font=ctk.CTkFont(size=11), text_color="#6C757D", height=15).pack(anchor="w")

        # 2. Split into Left and Right Dash Panels
        left_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_panel.columnconfigure(0, weight=1)
        
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        right_panel.columnconfigure(0, weight=1)

        # --- LEFT PANEL ---
        # KPI Cards Row
        kpi_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 20))
        kpi_frame.columnconfigure((0,1,2,3), weight=1)

        kpis = [
            ("Total Sales", "$1,500,000", "+12% vs last month", "#E0F7FA", "#00ACC1", "↑", "#00838F", "💵"),
            ("Today's Revenue", "$50,000", "Updated just now", "#E8F5E9", "#43A047", "↑", "#2E7D32", "📈"),
            ("Active Customers", "1,200", "80 new this month", "#E3F2FD", "#1E88E5", "↑", "#1565C0", "🤝"),
            ("Low Stock Alerts", "25", "Needs attention", "#FFEBEE", "#E53935", "↓", "#C62828", "⚠️")
        ]

        for i, (title, val, sub, bg, color, trend_ic, tr_color, icon) in enumerate(kpis):
            card = ctk.CTkFrame(kpi_frame, fg_color=bg, corner_radius=16)
            card.grid(row=0, column=i, sticky="ew", padx=5)
            
            # Top row of card (Title + Icon)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(15, 5))
            
            trend_lbl = ctk.CTkLabel(top, text=trend_ic, text_color=color, font=ctk.CTkFont(size=12, weight="bold"), width=20, height=20, corner_radius=10, fg_color="#FFFFFF")
            trend_lbl.pack(side="left")
            ctk.CTkLabel(top, text=f" {title}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1F2937").pack(side="left", padx=5)
            
            ic_lbl = ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=16))
            ic_lbl.pack(side="right")

            # Value
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=26, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=15)
            # Subtitle
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=11), text_color=tr_color if "Needs" in sub or "+" in sub else "#6B7280", anchor="w").pack(fill="x", padx=15, pady=(0, 15))


        # Charts Row
        charts_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        charts_frame.pack(fill="x", pady=(0, 20))
        charts_frame.columnconfigure((0,1), weight=1)

        # Chart 1: Sales Trend
        c1 = ctk.CTkFrame(charts_frame, fg_color="#FFFFFF", corner_radius=16)
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(c1, text="Sales Trend", font=ctk.CTkFont(size=15, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=15, pady=(15, 5))
        self._add_line_chart(c1)

        # Chart 2: Product Distribution
        c2 = ctk.CTkFrame(charts_frame, fg_color="#FFFFFF", corner_radius=16)
        c2.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(c2, text="Product Distribution", font=ctk.CTkFont(size=15, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=15, pady=(15, 5))
        self._add_bar_chart(c2)

        # Recent Invoices Table
        inv_frame = ctk.CTkFrame(left_panel, fg_color="#FFFFFF", corner_radius=16)
        inv_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(inv_frame, text="Recent Invoices", font=ctk.CTkFont(size=16, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=20, pady=(20, 10))

        self.invoices_scroll = ctk.CTkScrollableFrame(inv_frame, fg_color="transparent")
        self.invoices_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self._load_recent_invoices()


        # --- RIGHT PANEL ---
        # Notifications
        notif_frame = ctk.CTkFrame(right_panel, fg_color="#FFFFFF", corner_radius=16)
        notif_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(notif_frame, text="Notifications", font=ctk.CTkFont(size=16, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=20, pady=(20, 10))

        # Low Stock Alert Section
        ls_bg = ctk.CTkFrame(notif_frame, fg_color="#FFEBEE", corner_radius=8)
        ls_bg.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(ls_bg, text="Low Stock", font=ctk.CTkFont(size=13, weight="bold"), text_color="#D32F2F", anchor="w").pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(ls_bg, text="⚠️", font=ctk.CTkFont(size=13), text_color="#D32F2F").pack(side="right", padx=10)

        for _ in range(4):
            it = ctk.CTkFrame(notif_frame, fg_color="transparent")
            it.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(it, text="Amoxicillin 500mg -", font=ctk.CTkFont(size=12), text_color="#4B5563").pack(side="left")
            ctk.CTkLabel(it, text=" 5 Units left", font=ctk.CTkFont(size=12, weight="bold"), text_color="#D32F2F").pack(side="left")
            ctk.CTkLabel(it, text="(Reorder)", font=ctk.CTkFont(size=11), text_color="#2196F3").pack(side="right")

        # Expiring Medicines Alert
        ex_bg = ctk.CTkFrame(notif_frame, fg_color="#FFEBEE", corner_radius=8)
        ex_bg.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(ex_bg, text="Expiring Medicines", font=ctk.CTkFont(size=13, weight="bold"), text_color="#D32F2F", anchor="w").pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(ex_bg, text="⚠️", font=ctk.CTkFont(size=13), text_color="#D32F2F").pack(side="right", padx=10)

        for _ in range(3):
            it = ctk.CTkFrame(notif_frame, fg_color="transparent")
            it.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(it, text="Ibuprofen 200mg -", font=ctk.CTkFont(size=12), text_color="#4B5563").pack(side="left")
            ctk.CTkLabel(it, text=" Expiring Dec 2024", font=ctk.CTkFont(size=12, weight="bold"), text_color="#D32F2F").pack(side="left")

        ctk.CTkFrame(notif_frame, fg_color="transparent", height=10).pack() # spacer

        # Actions Card
        actions_card = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_card.pack(fill="x", pady=(0, 20))
        
        btn_create = ctk.CTkButton(
            actions_card, text="Create Invoice", 
            font=ctk.CTkFont(size=15, weight="bold"), fg_color="#FFFFFF", text_color="#111827",
            hover_color="#F3F4F6", corner_radius=12, height=50, border_width=1, border_color="#E5E7EB",
            command=self._new_invoice
        )
        btn_create.pack(fill="x", pady=(0, 15))
        
        # User Management Card
        um_card = ctk.CTkFrame(right_panel, fg_color="#FFFFFF", corner_radius=16)
        um_card.pack(fill="x")
        ctk.CTkLabel(um_card, text="User Management", font=ctk.CTkFont(size=16, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(um_card, text="3 Roles: Admin, Biller, Accountant", font=ctk.CTkFont(size=12), text_color="#6B7280", anchor="w").pack(fill="x", padx=20)
        
        ctk.CTkButton(
            um_card, text="Add User", 
            font=ctk.CTkFont(size=14, weight="bold"), fg_color="#F9FAFB", text_color="#374151",
            hover_color="#E5E7EB", corner_radius=8, height=40, border_width=1, border_color="#D1D5DB",
            command=self._add_party
        ).pack(side="right", padx=20, pady=(15, 20))


    def _add_line_chart(self, parent):
        fig = Figure(figsize=(4.5, 2.2), dpi=100)
        ax = fig.add_subplot(111)
        ax.axis('off')  # Turn off axes for clean look
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FFFFFF')

        # Dummy data matching image curve somewhat
        x = np.linspace(0, 10, 100)
        y = np.sin(x)*0.5 + np.exp(x*0.1) + np.random.normal(0,0.05,100)
        # Smooth and make it look like chart
        y = (np.sin(x*1.5)*3) + (x*1.2) + 5
        # Ensure positive
        y = np.clip(y, 2, 20)

        ax.plot(x, y, color="#26C6DA", linewidth=2.5)
        ax.fill_between(x, y, 0, color="#E0F7FA", alpha=0.5)

        fig.tight_layout(pad=1)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _add_bar_chart(self, parent):
        fig = Figure(figsize=(4.5, 2.2), dpi=100)
        ax = fig.add_subplot(111)
        ax.axis('off')
        fig.patch.set_facecolor('#FFFFFF')
        ax.set_facecolor('#FFFFFF')

        labels = ['Antibiotics', 'Painkillers', 'Cardiovascular', 'Diabetes']
        values = [86, 60, 40, 25]  # Values
        colors = ['#29B6F6', '#FFA726', '#AB47BC', '#5C6BC0']

        y_pos = np.arange(len(labels))
        ax.barh(y_pos, values, color=colors, height=0.5, edgecolor="none")
        ax.invert_yaxis()

        # Add text labels manually
        for idx, (label, val) in enumerate(zip(labels, values)):
            ax.text(-2, idx, label, va='center', ha='right', fontsize=9, color="#4B5563")
            ax.text(val-2, idx, f"{val}%", va='center', ha='right', fontsize=9, color="#FFFFFF", fontweight="bold")

        ax.set_xlim(-30, 100) # Give space for text on left
        fig.tight_layout(pad=1)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_recent_invoices(self):
        """Load and display recent invoices mapping to new table layout."""
        for widget in self.invoices_scroll.winfo_children():
            widget.destroy()

        try:
            invoices = get_invoices_by_distributor(self.user["distributor_id"], limit=10)
        except Exception:
            invoices = []

        if not invoices:
            ctk.CTkLabel(
                self.invoices_scroll, text="No recent invoices.",
                font=ctk.CTkFont(size=13), text_color="#6B7280",
            ).pack(pady=30)
            return

        # Header Row
        header = ctk.CTkFrame(self.invoices_scroll, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", pady=(0, 8))
        header.pack_propagate(False)
        cols = [("Invoice ID", 120), ("Customer", 200), ("Date", 120), ("Amount", 120), ("Status", 100)]
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#4B5563", anchor="w" if text != "Status" else "center"
            ).pack(side="left", padx=10)

        # Map dummy status if needed based on real payment string or randomly
        def get_status_style(pay_type, idx):
            # Just distributing statuses for UI sake if real doesn't map perfectly
            options = [
                ("Paid", "#10B981", "#D1FAE5"),
                ("Pending", "#F59E0B", "#FEF3C7"),
                ("Overdue", "#EF4444", "#FEE2E2")
            ]
            pt = str(pay_type).lower()
            if "cash" in pt or "upi" in pt: return options[0]
            if "credit" in pt: return options[1]
            return options[idx % 3]

        for idx, inv in enumerate(invoices):
            row = ctk.CTkFrame(self.invoices_scroll, fg_color="transparent", height=45)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            
            # Add thin bottom border separator by placing a line frame
            ctk.CTkFrame(self.invoices_scroll, fg_color="#F3F4F6", height=1).pack(fill="x", padx=10)

            inv_date = inv.get("invoice_date", "")
            if hasattr(inv_date, "strftime"):
                inv_date = inv_date.strftime("%b %d, %Y")

            vals = [
                str(inv.get("invoice_no", "")).upper(),
                str(inv.get("customer_name", ""))[:25],
                str(inv_date),
                f"${float(inv.get('grand_total', 0)):,.0f}",
            ]
            for v, (col_name, w) in zip(vals, cols[:-1]):
                ctk.CTkLabel(
                    row, text=v, width=w, font=ctk.CTkFont(size=12), text_color="#1F2937",
                    anchor="w"
                ).pack(side="left", padx=10)

            # Status Badge
            stat_text, text_c, bg_c = get_status_style(inv.get("payment_type", ""), idx)
            badge_frame = ctk.CTkFrame(row, fg_color=bg_c, corner_radius=12, width=80, height=24)
            badge_frame.pack_propagate(False)
            badge_frame.pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(badge_frame, text=stat_text, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_c).pack(expand=True)

    def _new_invoice(self):
        from ui.invoice_form import InvoiceForm
        for widget in self.winfo_children():
            widget.destroy()
        form = InvoiceForm(self, self.user, self.distributor, self.app)
        form.pack(fill="both", expand=True)

    def _add_stock(self):
        from ui.add_stock_form import AddStockForm
        for widget in self.winfo_children():
            widget.destroy()
        form = AddStockForm(self.master, self.user, self.app)
        form.pack(fill="both", expand=True)

    def _add_party(self):
        from ui.add_party_form import AddPartyForm
        for widget in self.winfo_children():
            widget.destroy()
        form = AddPartyForm(self.master, self.user, self.app)
        form.pack(fill="both", expand=True)

    def _show_history(self):
        messagebox.showinfo("Invoice History", "Invoice history view coming soon!")

    def _show_reports(self):
        messagebox.showinfo("Reports", "Reports module coming soon!")

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.show_login()
