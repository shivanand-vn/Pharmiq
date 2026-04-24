"""
Reports View — UI for generating, previewing, and exporting various reports.
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import itertools
import threading
from datetime import datetime

from utils.async_db import async_db_call

class ReportsView(ctk.CTkFrame):
    """Main panel for generating and viewing reports."""

    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color="#F1F4F9")
        self.user = user_context
        self.app = app_ref
        self.distributor_id = self.user.get("distributor_id")
        
        # Access control check
        role = self.user.get('role', 'Biller')
        if role not in ["Admin", "Accountant"]:
            self._show_access_denied()
            return

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1) # The table area should expand

        # State Variables
        self.current_report_type = ctk.StringVar(value="Sales Report")
        self.fetched_data = [] # Raw list of tuples/dicts fetched from DB
        self.current_columns = [] # Titles of columns

        self._build_header()
        self._build_filters()
        self._build_table_area()
        
        # Initialize default view
        self._on_report_type_change()
        self._load_filter_data()

    def _show_access_denied(self):
        err_frame = ctk.CTkFrame(self, fg_color="transparent")
        err_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            err_frame, text="⛔ Access Denied", 
            font=ctk.CTkFont(size=24, weight="bold"), text_color="#E74C3C"
        ).pack(pady=(100, 10))
        ctk.CTkLabel(
            err_frame, text="You do not have permission to view Reports.", 
            font=ctk.CTkFont(size=14), text_color="#6C757D"
        ).pack()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12)
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(25, 10))
        
        ctk.CTkButton(
            header_frame, text="← Back", width=80, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=(20, 0), pady=12)
        
        title_lbl = ctk.CTkLabel(
            header_frame, text="📊 Reports & Analytics", 
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#1F2937"
        )
        title_lbl.pack(side="left", padx=20, pady=20)
        
        # Action Buttons
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right", padx=20, pady=20)
        
        self.btn_export_excel = ctk.CTkButton(
            actions_frame, text="⬇ Export Excel", 
            fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF",
            font=ctk.CTkFont(weight="bold"), corner_radius=8,
            command=self._export_excel, state="disabled"
        )
        self.btn_export_excel.pack(side="left", padx=5)
        
        self.btn_export_pdf = ctk.CTkButton(
            actions_frame, text="📄 Export PDF", 
            fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            font=ctk.CTkFont(weight="bold"), corner_radius=8,
            command=self._export_pdf, state="disabled"
        )
        self.btn_export_pdf.pack(side="left", padx=5)

    def _build_filters(self):
        self.filter_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12)
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 15))
        
        top_row = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(15, 10))
        
        # Report Type Dropdown
        ctk.CTkLabel(top_row, text="Report Type:", font=ctk.CTkFont(weight="bold"), text_color="#1F2937").pack(side="left", padx=(0, 10))
        self.report_type_menu = ctk.CTkOptionMenu(
            top_row, values=["Sales Report", "Detailed Invoice Report", "Inventory / Stock Report", "Expiry Report", "Return Report"],
            variable=self.current_report_type,
            command=self._on_report_type_change,
            width=220, fg_color="#F9FAFB", text_color="#1F2937",
            button_color="#E5E7EB", button_hover_color="#D1D5DB"
        )
        self.report_type_menu.pack(side="left")
        
        # Date Filters
        self.date_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        self.date_frame.pack(side="left", padx=15)
        ctk.CTkLabel(self.date_frame, text="From (YYYY-MM-DD):", text_color="#374151").pack(side="left", padx=5)
        self.from_date_entry = ctk.CTkEntry(self.date_frame, width=120, placeholder_text="YYYY-MM-DD", fg_color="#F9FAFB", border_color="#E5E7EB", text_color="#1F2937")
        self.from_date_entry.pack(side="left")
        
        ctk.CTkLabel(self.date_frame, text="To:", text_color="#374151").pack(side="left", padx=5)
        self.to_date_entry = ctk.CTkEntry(self.date_frame, width=120, placeholder_text="YYYY-MM-DD", fg_color="#F9FAFB", border_color="#E5E7EB", text_color="#1F2937")
        self.to_date_entry.pack(side="left")
        
        # Bottom Row for specific filters
        self.bot_row = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        self.bot_row.pack(fill="x", padx=20, pady=(0, 15))
        
        # Customer Filter
        self.customer_frame = ctk.CTkFrame(self.bot_row, fg_color="transparent")
        self.customer_frame.pack(side="left", padx=(0, 15))
        ctk.CTkLabel(self.customer_frame, text="Customer:", text_color="#374151").pack(side="left", padx=5)
        self.customer_entry = ctk.CTkComboBox(self.customer_frame, width=150, values=[""], fg_color="#F9FAFB", border_color="#E5E7EB", text_color="#1F2937")
        self.customer_entry.set("")
        self.customer_entry.pack(side="left")
        
        # Medicine Filter
        self.medicine_frame = ctk.CTkFrame(self.bot_row, fg_color="transparent")
        self.medicine_frame.pack(side="left", padx=15)
        ctk.CTkLabel(self.medicine_frame, text="Medicine:", text_color="#374151").pack(side="left", padx=5)
        self.medicine_entry = ctk.CTkComboBox(self.medicine_frame, width=150, values=[""], fg_color="#F9FAFB", border_color="#E5E7EB", text_color="#1F2937")
        self.medicine_entry.set("")
        self.medicine_entry.pack(side="left")
        
        # Status Filter
        self.status_frame = ctk.CTkFrame(self.bot_row, fg_color="transparent")
        self.status_frame.pack(side="left", padx=15)
        ctk.CTkLabel(self.status_frame, text="Status:", text_color="#374151").pack(side="left", padx=5)
        self.status_menu = ctk.CTkOptionMenu(
            self.status_frame, values=["All", "Paid", "Pending", "Cash", "Credit"],
            width=100, fg_color="#F9FAFB", text_color="#1F2937",
            button_color="#E5E7EB", button_hover_color="#D1D5DB"
        )
        self.status_menu.pack(side="left")
        
        # Expiry Days Filter (For Expiry Report)
        self.expiry_frame = ctk.CTkFrame(self.bot_row, fg_color="transparent")
        self.expiry_frame.pack(side="left", padx=15)
        ctk.CTkLabel(self.expiry_frame, text="Expiring in (Days):", text_color="#374151").pack(side="left", padx=5)
        self.expiry_days_entry = ctk.CTkEntry(self.expiry_frame, width=80, fg_color="#F9FAFB", border_color="#E5E7EB", text_color="#1F2937")
        self.expiry_days_entry.insert(0, "30")
        self.expiry_days_entry.pack(side="left")
        
        # Generate Button
        self.btn_generate = ctk.CTkButton(
            self.bot_row, text="Generate Preview", 
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            font=ctk.CTkFont(weight="bold"), corner_radius=8,
            command=self._generate_report
        )
        self.btn_generate.pack(side="right", padx=5)
        
        # Reset Button
        self.btn_reset = ctk.CTkButton(
            self.bot_row, text="↺ Reset", width=80,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            font=ctk.CTkFont(weight="bold"), corner_radius=8,
            command=self._reset_filters
        )
        self.btn_reset.pack(side="right", padx=5)

    def _on_report_type_change(self, *args):
        """Show/hide filters based on the selected report type."""
        rtype = self.current_report_type.get()
        
        # Hide all specific filters initially
        for frame in [self.date_frame, self.customer_frame, self.medicine_frame, self.status_frame, self.expiry_frame]:
            frame.pack_forget()
            
        # Re-pack based on type
        if rtype == "Sales Report":
            self.date_frame.pack(side="left", padx=15)
            self.customer_frame.pack(side="left", padx=(0, 15))
            self.medicine_frame.pack(side="left", padx=15)
        elif rtype == "Detailed Invoice Report":
            self.date_frame.pack(side="left", padx=15)
            self.customer_frame.pack(side="left", padx=(0, 15))
            self.medicine_frame.pack(side="left", padx=15)
        elif rtype == "Inventory / Stock Report":
            self.medicine_frame.pack(side="left", padx=(0, 15))
        elif rtype == "Expiry Report":
            self.expiry_frame.pack(side="left", padx=(0, 15))
            self.medicine_frame.pack(side="left", padx=15)
        elif rtype == "Return Report":
            self.date_frame.pack(side="left", padx=15)
            self.customer_frame.pack(side="left", padx=(0, 15))
            self.medicine_frame.pack(side="left", padx=15)

    def _reset_filters(self):
        """Reset all filter inputs to defaults."""
        self.from_date_entry.delete(0, "end")
        self.to_date_entry.delete(0, "end")
        self.customer_entry.set("")
        self.medicine_entry.set("")
        self.status_menu.set("All")
        self.expiry_days_entry.delete(0, "end")
        self.expiry_days_entry.insert(0, "30")
        
        # Clear table
        self.tree.delete(*self.tree.get_children())
        self.fetched_data = []
        self.table_lbl.configure(text="Data Preview (0 records)")
        self.btn_export_excel.configure(state="disabled")
        self.btn_export_pdf.configure(state="disabled")

    def _load_filter_data(self):
        from db.connection import fetch_all
        
        def fetch_filters():
            custs = fetch_all("SELECT shop_name FROM customers WHERE distributor_id = %s ORDER BY shop_name", (self.distributor_id,))
            meds = fetch_all("SELECT name FROM medicines ORDER BY name")
            return custs, meds
            
        def on_success(result):
            custs, meds = result
            cust_names = [c["shop_name"] for c in custs]
            med_names = [m["name"] for m in meds]
            
            if cust_names:
                self.customer_entry.configure(values=cust_names)
            if med_names:
                self.medicine_entry.configure(values=med_names)
                
        def on_error(e):
            print(f"Error loading filters in reports: {e}")
            
        async_db_call(self, fetch_filters, (), on_success, on_error)

    def _build_table_area(self):
        table_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12)
        table_container.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 25))
        
        table_container.columnconfigure(0, weight=1)
        table_container.rowconfigure(1, weight=1)
        
        # Header for the table
        self.table_lbl = ctk.CTkLabel(
            table_container, text="Data Preview (0 records)", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#374151"
        )
        self.table_lbl.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 0))
        
        # Treeview styling
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Reports.Treeview",
            background="#FFFFFF",
            foreground="#1F2937",
            rowheight=35,
            fieldbackground="#FFFFFF",
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Reports.Treeview.Heading",
            background="#F3F4F6",
            foreground="#374151",
            relief="flat",
            font=("Segoe UI", 11, "bold")
        )
        style.map("Reports.Treeview", background=[("selected", "#EFF6FF")], foreground=[("selected", "#1D4ED8")])
        style.map("Reports.Treeview.Heading", background=[('active', '#E5E7EB')])

        # Scrollbars
        scroll_y = ttk.Scrollbar(table_container)
        scroll_y.grid(row=1, column=1, sticky="ns", pady=10, padx=(0, 10))
        
        scroll_x = ttk.Scrollbar(table_container, orient="horizontal")
        scroll_x.grid(row=2, column=0, sticky="ew", padx=20)

        # Treeview
        self.tree = ttk.Treeview(
            table_container, 
            style="Reports.Treeview",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            selectmode="extended"
        )
        self.tree.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        self.tree.tag_configure("even", background="#F9FAFB")
        self.tree.tag_configure("odd", background="#FFFFFF")
        
        # Special highlighting tags
        self.tree.tag_configure("danger", foreground="#DC2626", font=("Segoe UI", 10, "bold"))  # For Expiry
        self.tree.tag_configure("warning", foreground="#D97706", font=("Segoe UI", 10, "bold")) # For Low Stock

    def _validate_dates(self):
        """Validates date formats if present. Returns (from_date, to_date) or raises ValueError."""
        fd = self.from_date_entry.get().strip()
        td = self.to_date_entry.get().strip()
        
        if fd:
            try:
                datetime.strptime(fd, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid From Date format. Use YYYY-MM-DD")
        else:
            fd = None
            
        if td:
            try:
                datetime.strptime(td, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid To Date format. Use YYYY-MM-DD")
        else:
            td = None
            
        if fd and td and fd > td:
            raise ValueError("'From' date should not be greater than 'To' date")
            
        return fd, td

    def _get_current_filters(self):
        try:
            fd, td = self._validate_dates()
        except:
            fd, td = None, None
        days_str = self.expiry_days_entry.get().strip()
        return {
            "from_date": fd,
            "to_date": td,
            "customer": self.customer_entry.get().strip(),
            "medicine": self.medicine_entry.get().strip(),
            "status": self.status_menu.get(),
            "expiry_days": int(days_str) if days_str.isdigit() else 30
        }

    def _generate_report(self):
        rtype = self.current_report_type.get()
        
        try:
            fd, td = self._validate_dates()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return
            
        filters = self._get_current_filters()

        # Update button text to loading if async
        self.btn_generate.configure(text="Generating...", state="disabled")
        self.update_idletasks() # Force UI update immediately

        PREVIEW_LIMIT = 200  # Limit preview rows for performance

        def fetch_report():
            from services.report_service import fetch_data, process_data, format_report_data, get_report_config
            raw_data = fetch_data(rtype, self.distributor_id, filters)
            processed_data = process_data(rtype, raw_data)
            table_data, totals = format_report_data(rtype, processed_data)
            config = get_report_config(rtype)
            return table_data, config, totals, len(table_data)

        def on_success(result):
            self.btn_generate.configure(text="Generate Preview", state="normal")
            table_data, config, totals, total_count = result
            
            self.current_columns = config["columns"]
            self.fetched_data = table_data
            
            # Limit preview for performance
            preview_data = table_data[:PREVIEW_LIMIT]
            if total_count > PREVIEW_LIMIT:
                self.table_lbl.configure(text=f"Data Preview (showing {PREVIEW_LIMIT} of {total_count} records)")
            self._render_table(preview_data, rtype)
            
            # Update label with totals info if total_count <= PREVIEW_LIMIT
            if total_count <= PREVIEW_LIMIT:
                self.table_lbl.configure(text=f"Data Preview ({total_count} records)")

        def on_error(e):
            self.btn_generate.configure(text="Generate Preview", state="normal")
            messagebox.showerror("Database Error", f"An error occurred while fetching the report:\n{str(e)}")

        async_db_call(self, fetch_report, (), on_success, on_error)


    def _render_table(self, data, rtype):
        """Render the fetched data into the treeview."""
        # Clear existing
        self.tree.delete(*self.tree.get_children())
        
        # Configure Columns
        self.tree["columns"] = self.current_columns
        self.tree["show"] = "headings"
        
        for col in self.current_columns:
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, minwidth=100, width=150, anchor="w")
            
        if not data:
            self.table_lbl.configure(text="Data Preview (0 records found)")
            self.btn_export_excel.configure(state="disabled")
            self.btn_export_pdf.configure(state="disabled")
            return
            
        self.table_lbl.configure(text=f"Data Preview ({len(data)} records)")
        self.btn_export_excel.configure(state="normal")
        self.btn_export_pdf.configure(state="normal")
        
        # Special header row formatting
        self.tree.tag_configure("header", font=("Segoe UI", 10, "bold"), background="#E5E7EB", foreground="#111827")
        
        for row in data:
            values = row.get("values", [])
            tag = row.get("tag", "even")
            if row.get("is_header"):
                self.tree.insert("", "end", values=values, tags=("header",))
            else:
                self.tree.insert("", "end", values=values, tags=(tag,))

    def _export_excel(self):
        if not self.fetched_data: return
        from services.report_service import generate_filename
        rtype = self.current_report_type.get()
        filters = self._get_current_filters()
        
        default_name = generate_filename(rtype, filters["from_date"], filters["to_date"], filters["customer"], "xlsx")
        
        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Export as Excel",
            initialfile=default_name
        )
        if file_path:
            self.btn_export_excel.configure(text="Exporting...", state="disabled")
            self.update_idletasks()
            
            def do_export():
                from services.report_service import generate_report
                return generate_report(rtype, "xlsx", filters, self.distributor_id, file_path)
            
            def on_done(result):
                self.btn_export_excel.configure(text="⬇ Export Excel", state="normal")
                success, msg = result
                if success:
                    messagebox.showinfo("Export Successful", f"Excel saved to:\n{file_path}")
                else:
                    messagebox.showerror("Export Failed", f"Could not save Excel:\n{msg}")
            
            def on_err(e):
                self.btn_export_excel.configure(text="⬇ Export Excel", state="normal")
                messagebox.showerror("Export Failed", str(e))
            
            async_db_call(self, do_export, (), on_done, on_err)

    def _export_pdf(self):
        if not self.fetched_data: return
        from services.report_service import generate_filename
        rtype = self.current_report_type.get()
        filters = self._get_current_filters()
        
        default_name = generate_filename(rtype, filters["from_date"], filters["to_date"], filters["customer"], "pdf")
        
        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Export as PDF",
            initialfile=default_name
        )
        if file_path:
            self.btn_export_pdf.configure(text="Exporting...", state="disabled")
            self.update_idletasks()
            
            def do_export():
                from services.report_service import generate_report
                return generate_report(rtype, "pdf", filters, self.distributor_id, file_path)
            
            def on_done(result):
                self.btn_export_pdf.configure(text="📄 Export PDF", state="normal")
                success, msg = result
                if success:
                    messagebox.showinfo("Export Successful", f"PDF saved to:\n{file_path}")
                else:
                    messagebox.showerror("Export Failed", f"Could not save PDF:\n{msg}")
            
            def on_err(e):
                self.btn_export_pdf.configure(text="📄 Export PDF", state="normal")
                messagebox.showerror("Export Failed", str(e))
            
            async_db_call(self, do_export, (), on_done, on_err)

    def _go_back(self):
        self.app.switch_view("Dashboard")
