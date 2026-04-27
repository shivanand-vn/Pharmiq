"""
Dashboard — Main window after login with distributor branding.
Redesigned to match Pharmiq UI reference, fully dynamic.
"""

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image as PILImage
import os
import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import seaborn as sns

from models.distributor import get_distributor_by_id
from models.invoice import get_invoices_by_distributor
from models.dashboard_stats import (
    get_kpi_stats, get_sales_trend, get_product_distribution,
    get_low_stock_list, get_expiring_medicines
)


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

        # Logo and Title at top
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(25, 30), padx=20, anchor="w", fill="x")
        
        logo_icon = ctk.CTkLabel(logo_frame, text="💊", font=ctk.CTkFont(size=24))
        logo_icon.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            logo_frame, text="Pharmiq",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#FFFFFF"
        ).pack(side="left")

        # Navigation Items mapped to handlers and allowed roles
        role = self.user.get('role', 'Admin')
        all_nav_items = [
            ("Dashboard", "layout", True, self._go_dashboard, ["Admin", "Biller", "Accountant"]),
            ("Customers", "store", False, self._go_customers, ["Admin", "Biller"]),
            ("Billing/Invoices", "file-text", False, self._go_invoices, ["Admin", "Biller", "Accountant"]),
            ("Invoice History", "archive", False, self._go_invoice_history, ["Admin", "Biller", "Accountant"]),
            ("Payments", "credit-card", False, self._go_payments, ["Admin", "Accountant"]),
            ("Inventory", "package", False, self._go_inventory, ["Admin", "Accountant", "Biller"]),
            ("Returns", "rotate-ccw", False, self._go_returns, ["Admin", "Biller"]),
            ("Reports & Analytics", "bar-chart", False, self._show_reports, ["Admin", "Accountant"]),
            ("Users & Roles", "users", False, self._show_users, ["Admin"]),
            # Settings removed from sidebar
        ]
        nav_items = [item for item in all_nav_items if role in item[4]]

        icons = {
            "layout": "⊞", "store": "🏪", "box": "📦", "file-text": "📄",
            "archive": "📜", "credit-card": "💳", "package": "🗃", "rotate-ccw": "↩", "bar-chart": "📊", "users": "👥", "settings": "⚙"
        }

        # Narrow symbols need an extra space to visually align with double-width emojis
        narrow_icons = {"layout", "rotate-ccw", "settings"}

        for title, icon_key, is_active, handler, allowed in nav_items:
            bg_color = "#326F8A" if is_active else "transparent"
            hover_color = "#2A5A72"
            text_color = "#FFFFFF" if is_active else "#A8C5DA"
            
            icon_str = icons.get(icon_key, '')
            spacing = "   " if icon_key in narrow_icons else "  "
            
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon_str}{spacing}{title}",
                font=ctk.CTkFont(size=14, weight="bold" if is_active else "normal"),
                fg_color=bg_color,
                hover_color=hover_color,
                text_color=text_color,
                anchor="w",
                height=45,
                corner_radius=8,
                command=handler
            )
            btn.pack(pady=4, padx=15, fill="x")

        # Bottom: User info, then Logout
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", pady=20, padx=15, fill="x")

        # User info row first
        user_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        user_row.pack(fill="x", pady=(0, 12))

        avatar_lbl = ctk.CTkLabel(
            user_row, text="👤", width=36, height=36, 
            fg_color="#F8B195", corner_radius=18, text_color="#FFFFFF"
        )
        avatar_lbl.pack(side="left", padx=(0, 10))
        
        user_name = self.user.get('username', 'Admin User')[:12]
        ctk.CTkLabel(
            user_row, text=user_name,
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF"
        ).pack(side="left")

        # Logout button below user info
        ctk.CTkButton(
            bottom_frame, text="🚪  Logout",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#E74C3C", hover_color="#C0392B",
            text_color="#FFFFFF", corner_radius=8,
            height=40,
            command=self._logout,
        ).pack(fill="x")

    def _build_main_area(self):
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=0, column=1, sticky="nsew", padx=25, pady=(15, 25))
        
        main_content.columnconfigure(0, weight=7)
        main_content.columnconfigure(1, weight=3)
        main_content.rowconfigure(1, weight=1)

        # 1. Top Header (minimal spacer)
        header_frame = ctk.CTkFrame(main_content, fg_color="transparent", height=10)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # 2. Split into Left and Right Dash Panels
        left_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_panel.columnconfigure(0, weight=1)
        
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        right_panel.columnconfigure(0, weight=1)

        # FETCH DYNAMIC KPI DATA
        try:
            kpi_data = get_kpi_stats(self.user["distributor_id"])
        except Exception as e:
            kpi_data = {"total_sales": 0, "todays_revenue": 0, "active_customers": 0, "low_stock_count": 0}
            print("DB Error KPIs:", e)

        # --- LEFT PANEL ---
        # KPI Cards Row
        kpi_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 20))
        kpi_frame.columnconfigure((0,1,2,3), weight=1)

        kpis = [
            ("Total Sales", f"₹{float(kpi_data['total_sales']):,.0f}", "All time", "#FFFFFF", "#00ACC1", "↑", "#00838F", "💵"),
            ("Today's Revenue", f"₹{float(kpi_data['todays_revenue']):,.0f}", "Updated just now", "#FFFFFF", "#43A047", "↑", "#2E7D32", "📈"),
            ("Active Customers", f"{kpi_data['active_customers']:,}", "Active this month", "#FFFFFF", "#1E88E5", "↑", "#1565C0", "🤝"),
            ("Low Stock Alerts", f"{kpi_data['low_stock_count']:,}", "Needs attention", "#FFFFFF", "#E53935", "↓", "#C62828", "⚠️")
        ]

        for i, (title, val, sub, bg, color, trend_ic, tr_color, icon) in enumerate(kpis):
            card = ctk.CTkFrame(kpi_frame, fg_color=bg, corner_radius=16, border_width=1, border_color="#E5E7EB")
            card.grid(row=0, column=i, sticky="ew", padx=8)
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=(15, 5))
            
            trend_bg = "#F3F4F6"
            trend_lbl = ctk.CTkLabel(top, text=trend_ic, text_color=color, font=ctk.CTkFont(size=12, weight="bold"), width=20, height=20, corner_radius=10, fg_color=trend_bg)
            trend_lbl.pack(side="left")
            ctk.CTkLabel(top, text=f" {title}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#4B5563").pack(side="left", padx=5)
            
            ic_lbl = ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=16))
            ic_lbl.pack(side="right")

            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=22, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=15)
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=11), text_color=tr_color if "Needs" in sub or "+" in sub else "#6B7280", anchor="w").pack(fill="x", padx=15, pady=(0, 15))

        # Charts Row
        charts_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        charts_frame.pack(fill="x", pady=(0, 20))
        charts_frame.columnconfigure((0,1), weight=1)

        c1 = ctk.CTkFrame(charts_frame, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color="#E5E7EB")
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(c1, text="Sales Trend", font=ctk.CTkFont(size=15, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=15, pady=(15, 5))
        self._add_line_chart(c1)

        c2 = ctk.CTkFrame(charts_frame, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color="#E5E7EB")
        c2.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(c2, text="Product Distribution", font=ctk.CTkFont(size=15, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=15, pady=(15, 5))
        self._add_bar_chart(c2)

        # Recent Invoices Table
        inv_frame = ctk.CTkFrame(left_panel, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color="#E5E7EB")
        inv_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(inv_frame, text="Recent Invoices", font=ctk.CTkFont(size=16, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=20, pady=(20, 10))

        self.invoices_scroll = ctk.CTkScrollableFrame(inv_frame, fg_color="transparent")
        self.invoices_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self._load_recent_invoices()


        # --- RIGHT PANEL (NOTIFICATIONS) ---
        notif_frame = ctk.CTkFrame(right_panel, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color="#E5E7EB")
        notif_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(notif_frame, text="Notifications", font=ctk.CTkFont(size=16, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=20, pady=(20, 10))

        # Dynamic Low Stock
        ls_bg = ctk.CTkFrame(notif_frame, fg_color="#FEF2F2", corner_radius=8)
        ls_bg.pack(fill="x", padx=20, pady=(0, 10))
        
        ls_accent = ctk.CTkFrame(ls_bg, fg_color="#EF4444", width=4, corner_radius=4)
        ls_accent.pack(side="left", fill="y", pady=2, padx=(2, 0))
        
        ctk.CTkLabel(ls_bg, text="Low Stock", font=ctk.CTkFont(size=13, weight="bold"), text_color="#B91C1C", anchor="w").pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(ls_bg, text="⚠️", font=ctk.CTkFont(size=13), text_color="#D32F2F").pack(side="right", padx=10)

        try:
            ls_items = get_low_stock_list(self.user["distributor_id"])
        except Exception:
            ls_items = []
            
        if not ls_items:
            ctk.CTkLabel(notif_frame, text="All products are well stocked! ✅", font=ctk.CTkFont(size=12), text_color="#6B7280").pack(pady=5)
        else:
            for item in ls_items:
                it = ctk.CTkFrame(notif_frame, fg_color="transparent")
                it.pack(fill="x", padx=20, pady=2)
                p_name = str(item.get("product_name", "Unknown"))[:20] + " -"
                ctk.CTkLabel(it, text=p_name, font=ctk.CTkFont(size=12), text_color="#4B5563").pack(side="left")
                ctk.CTkLabel(it, text=f" {item.get('quantity', 0)} left", font=ctk.CTkFont(size=12, weight="bold"), text_color="#D32F2F").pack(side="left")

        # Dynamic Expiring Medicines
        ex_bg = ctk.CTkFrame(notif_frame, fg_color="#FEF2F2", corner_radius=8)
        ex_bg.pack(fill="x", padx=20, pady=(20, 10))
        
        ex_accent = ctk.CTkFrame(ex_bg, fg_color="#EF4444", width=4, corner_radius=4)
        ex_accent.pack(side="left", fill="y", pady=2, padx=(2, 0))
        
        ctk.CTkLabel(ex_bg, text="Expiring Medicines", font=ctk.CTkFont(size=13, weight="bold"), text_color="#B91C1C", anchor="w").pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(ex_bg, text="⚠️", font=ctk.CTkFont(size=13), text_color="#D32F2F").pack(side="right", padx=10)

        try:
            ex_items = get_expiring_medicines(self.user["distributor_id"])
        except Exception:
            ex_items = []
            
        if not ex_items:
            ctk.CTkLabel(notif_frame, text="No items expiring soon. ✅", font=ctk.CTkFont(size=12), text_color="#6B7280").pack(pady=5)
        else:
            for item in ex_items:
                it = ctk.CTkFrame(notif_frame, fg_color="transparent")
                it.pack(fill="x", padx=20, pady=2)
                p_name = str(item.get("product_name", "Unknown"))[:20] + " -"
                exp_dt = item.get("expiry_date", "")
                if hasattr(exp_dt, "strftime"):
                    exp_dt = exp_dt.strftime("%b %Y")
                ctk.CTkLabel(it, text=p_name, font=ctk.CTkFont(size=12), text_color="#4B5563").pack(side="left")
                ctk.CTkLabel(it, text=f" Exp {exp_dt}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#D32F2F").pack(side="left")

        ctk.CTkFrame(notif_frame, fg_color="transparent", height=10).pack()

        # Actions & User Management
        actions_card = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_card.pack(fill="x", pady=(0, 20))
        
        um_card = ctk.CTkFrame(right_panel, fg_color="#FFFFFF", corner_radius=16, border_width=1, border_color="#E5E7EB")
        um_card.pack(fill="x")
        
        role = self.user.get('role', 'Admin')
        
        ctk.CTkLabel(um_card, text="Role Information", font=ctk.CTkFont(size=16, weight="bold"), text_color="#111827", anchor="w").pack(fill="x", padx=20, pady=(20, 5))
        ctk.CTkLabel(um_card, text=f"Logged in as: {role}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#10B981", anchor="w").pack(fill="x", padx=20)
        ctk.CTkLabel(um_card, text="Access determined by role.", font=ctk.CTkFont(size=11), text_color="#6B7280", anchor="w").pack(fill="x", padx=20)
        
        if role == "Admin":
            ctk.CTkButton(
                um_card, text="Manage Users", 
                font=ctk.CTkFont(size=13, weight="bold"), fg_color="#F9FAFB", text_color="#374151",
                hover_color="#E5E7EB", corner_radius=12, height=35, border_width=1, border_color="#D1D5DB",
                command=self._show_users
            ).pack(side="right", padx=20, pady=(15, 20))
        else:
             ctk.CTkFrame(um_card, height=45, fg_color="transparent").pack(pady=(0, 15))

    def _add_line_chart(self, parent):
        sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0), "figure.facecolor": (0, 0, 0, 0)})
        fig = Figure(figsize=(4.5, 2.2), dpi=100)
        ax = fig.add_subplot(111)

        try:
            trend_data = get_sales_trend(self.user["distributor_id"], limit_months=12)
        except Exception:
            trend_data = []

        if trend_data:
            x = np.arange(len(trend_data))
            y = [float(row["total"] or 0) for row in trend_data]
            labels = [row["month_name"] for row in trend_data]
        else:
            x = np.linspace(0, 10, 100)
            y = np.sin(x*1.5)*3 + x*1.2 + 5
            labels = []

        sns.lineplot(x=x, y=y, ax=ax, color="#0EA5E9", linewidth=2.5)
        ax.fill_between(x, y, 0, color="#E0F2FE", alpha=0.4)

        if labels:
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8, color="#6B7280")
        
        ax.set_ylabel("Sales (₹)", fontsize=9, color="#6B7280")
        ax.tick_params(axis='y', labelsize=8, colors="#6B7280")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#E5E7EB')
        ax.spines['bottom'].set_color('#E5E7EB')

        fig.tight_layout(pad=1)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _add_bar_chart(self, parent):
        sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0), "figure.facecolor": (0, 0, 0, 0)})
        fig = Figure(figsize=(4.5, 2.2), dpi=100)
        ax = fig.add_subplot(111)
        ax.axis('off')

        try:
            dist_data = get_product_distribution(self.user["distributor_id"])
        except Exception:
            dist_data = []

        labels = []
        values = []
        if dist_data:
            total_sum = sum(float(r["total_qty"] or 0) for r in dist_data)
            if total_sum == 0: total_sum = 1 
            for r in dist_data:
                category = r["category"] if r["category"] else "Other"
                labels.append(category)
                percent = int(round((float(r["total_qty"] or 0) / total_sum) * 100))
                values.append(percent)
        else:
            labels = ['Antibiotics', 'Painkillers', 'Cardio', 'Diabetes']
            values = [86, 60, 40, 25]

        colors = ['#38BDF8', '#FBBF24', '#A78BFA', '#818CF8'][:len(labels)]
        if not colors:
            return

        sns.barplot(x=values, y=labels, ax=ax, palette=colors, orient='h', hue=labels, legend=False)

        for idx, (label, val) in enumerate(zip(labels, values)):
            ax.text(-2, idx, str(label)[:12], va='center', ha='right', fontsize=9, color="#6B7280")
            ax.text(val-2, idx, f"{val}%", va='center', ha='right', fontsize=9, color="#FFFFFF", fontweight="bold")

        ax.set_xlim(-30, 100)
        fig.tight_layout(pad=1)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_recent_invoices(self):
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

        header = ctk.CTkFrame(self.invoices_scroll, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", pady=(0, 8))
        header.pack_propagate(False)
        cols = [("Invoice No", 120), ("Customer", 200), ("Date", 120), ("Amount", 120), ("Status", 100)]
        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#4B5563", anchor="w" if text != "Status" else "center"
            ).pack(side="left", padx=10)

        def get_status_style(status, idx):
            options = {
                "Paid": ("Paid", "#059669", "#ECFDF5"),
                "Pending": ("Pending", "#D97706", "#FFFBEB"),
                "Partial": ("Partial", "#D97706", "#FFFBEB"),
                "Overdue": ("Overdue", "#DC2626", "#FEF2F2")
            }
            return options.get(status, options["Pending"])

        for idx, inv in enumerate(invoices):
            row_bg = "transparent" if idx % 2 == 0 else "#F9FAFB"
            row = ctk.CTkFrame(self.invoices_scroll, fg_color=row_bg, height=45, corner_radius=8)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            inv_date = inv.get("invoice_date", "")
            if hasattr(inv_date, "strftime"):
                inv_date = inv_date.strftime("%b %d, %Y")

            vals = [
                str(inv.get("invoice_no", "")).upper(),
                str(inv.get("customer_name", ""))[:25],
                str(inv_date),
                f"₹{float(inv.get('grand_total', 0)):,.0f}",
            ]
            for v, (col_name, w) in zip(vals, cols[:-1]):
                ctk.CTkLabel(
                    row, text=v, width=w, font=ctk.CTkFont(size=12), text_color="#1F2937",
                    anchor="w"
                ).pack(side="left", padx=10)

            stat_text, text_c, bg_c = get_status_style(inv.get("status", "Pending"), idx)
            badge_frame = ctk.CTkFrame(row, fg_color=bg_c, corner_radius=12, width=80, height=24)
            badge_frame.pack_propagate(False)
            badge_frame.pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(badge_frame, text=stat_text, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_c).pack(expand=True)

    # Sidebar Navigation Handlers
    def _go_dashboard(self):
        self.app.switch_view("Dashboard")

    def _go_customers(self):
        self.app.switch_view("CustomerView")

    def _go_products(self):
        self.app.switch_view("InventoryView")

    def _go_invoices(self):
        self.app.switch_view("InvoiceForm")

    def _go_inventory(self):
        self.app.switch_view("InventoryView")

    def _go_returns(self):
        self.app.switch_view("ReturnsView")

    def _go_invoice_history(self):
        self.app.switch_view("InvoiceHistoryView")

    def _go_payments(self):
        self.app.switch_view("PaymentsView")

    def _new_invoice(self):
        self.app.switch_view("InvoiceForm")

    def _add_stock(self):
        self.app.switch_view("InventoryView")

    def _add_party(self):
        messagebox.showinfo("Add Party", "Coming soon!")

    def _show_history(self):
        self.app.switch_view("InvoiceHistoryView")

    def _show_reports(self):
        self.app.switch_view("ReportsView")
        
    def _show_users(self):
        self.app.switch_view("UserView")
        
    def _show_settings(self):
        messagebox.showinfo("Settings", "Settings coming soon!")

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.show_login()
