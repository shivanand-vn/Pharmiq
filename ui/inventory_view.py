"""
Inventory View — Refactored for combined Medicine/Inventory flow.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
import re

from models.product import (
    get_inventory_list, 
    check_batch_exists, 
    add_new_stock,
    create_medicine,
    update_medicine_pricing
)
from db.connection import execute_query, fetch_all

# -- Colour palette --
BG_DARK = "#F8F9FA"
CARD_BG = "#FFFFFF"
BORDER_CLR = "#E5E7EB"
ACCENT = "#4361EE"
ACCENT_HOVER = "#3A0CA3"
TEXT_DARK = "#111827"
TEXT_MUTED = "#6B7280"
ENTRY_BG = "#F9FAFB"
SUCCESS = "#10B981"
SUCCESS_HOV = "#059669"
WARNING = "#F59E0B"
DANGER = "#EF4444"


class InventoryView(ctk.CTkFrame):
    def __init__(self, master, user_context, app_ref):
        super().__init__(master, fg_color=BG_DARK)
        self.user = user_context
        self.app = app_ref

        self.inventory_data = []
        self.medicines = []
        self.suppliers = []
        
        self.is_new_medicine_mode = False
        self._after_ids = []

        self._build_ui()
        self._load_data()
        self.bind("<Destroy>", self._cleanup)

    def _cleanup(self, event=None):
        if event.widget == self:
            for aid in self._after_ids:
                try: self.after_cancel(aid)
                except Exception: pass
            self._after_ids.clear()
            
    def _safe_focus(self, widget):
        if self.winfo_exists() and widget and widget.winfo_exists():
            try: widget.focus()
            except Exception: pass

    def _build_ui(self):
        # -- Top bar --
        top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=60, border_width=1, border_color=BORDER_CLR)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkButton(
            top, text="← Back", width=80, height=36,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=8,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._go_back,
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            top, text="📦  Inventory Management",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=10)

        # -- Main 2-Column Split --
        split_container = ctk.CTkFrame(self, fg_color="transparent")
        split_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Column (Table)
        self.left_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Right Column (Form)
        self.right_col = ctk.CTkFrame(split_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER_CLR, width=380)
        self.right_col.pack(side="right", fill="y")
        self.right_col.pack_propagate(False)

        self._build_table_area()
        self._build_form_area()

    def _build_table_area(self):
        toolbar = ctk.CTkFrame(self.left_col, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=15)

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            toolbar, textvariable=self.search_var, placeholder_text="🔍 Search batch or medicine...",
            width=280, height=38, font=ctk.CTkFont(size=12), corner_radius=8,
            fg_color=ENTRY_BG, border_color=BORDER_CLR, text_color=TEXT_DARK
        )
        search_entry.pack(side="left", padx=(0, 8))
        search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        ctk.CTkLabel(toolbar, text="Stock managed batch-wise", font=ctk.CTkFont(size=11, slant="italic"), text_color=TEXT_MUTED).pack(side="right", padx=10)

        header = ctk.CTkFrame(self.left_col, fg_color="#F3F4F6", corner_radius=8, height=40)
        header.pack(fill="x", padx=15, pady=(0, 5))
        header.pack_propagate(False)

        cols = [
            ("Medicine Name", 160), ("Batch Number", 100), ("Supplier", 120), 
            ("Expiry", 85), ("Qty", 50), ("TRP", 80), ("MRP", 80), ("Status", 90), ("", 110)
        ]

        for text, w in cols:
            ctk.CTkLabel(
                header, text=text, width=w, font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_MUTED, anchor="w" if text not in ["Qty", "TRP", "MRP", "Status", ""] else "center"
            ).pack(side="left", padx=3)

        self.scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.loading_lbl = ctk.CTkLabel(self.scroll, text="Loading inventory...", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.loading_lbl.pack(pady=40)

    def _build_form_area(self):
        self.form_header_row = ctk.CTkFrame(self.right_col, fg_color="transparent")
        self.form_header_row.pack(fill="x", padx=20, pady=(25, 10))
        
        self.form_title = ctk.CTkLabel(
            self.form_header_row, text="Add Inventory",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_DARK
        )
        self.form_title.pack(side="left")

        self.toggle_mode_btn = ctk.CTkButton(
            self.form_header_row, text="➕ Add New Medicine", height=28, width=130,
            font=ctk.CTkFont(size=11, weight="bold"), corner_radius=6,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._toggle_mode
        )
        self.toggle_mode_btn.pack(side="right")

        self.form_scroll = ctk.CTkScrollableFrame(self.right_col, fg_color="transparent")
        self.form_scroll.pack(fill="both", expand=True)

        self.field_frames = {}

        def add_field(key, label_text, widget_type="entry", placeholder="", required=True, cmd=None):
            row = ctk.CTkFrame(self.form_scroll, fg_color="transparent")
            
            lbl_row = ctk.CTkFrame(row, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(0, 3))
            ctk.CTkLabel(lbl_row, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DARK, anchor="w", height=15).pack(side="left")
            if required:
                ctk.CTkLabel(lbl_row, text=" *", font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER, anchor="w", height=15).pack(side="left")

            if widget_type == "entry":
                widget = ctk.CTkEntry(
                    row, placeholder_text=placeholder, height=38, font=ctk.CTkFont(size=12),
                    fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK, corner_radius=6
                )
                if cmd: widget.bind("<KeyRelease>", cmd)
            elif widget_type == "combo":
                widget = ctk.CTkComboBox(
                    row, values=["Loading..."], height=38, font=ctk.CTkFont(size=12),
                    fg_color=ENTRY_BG, border_color=BORDER_CLR, border_width=1, text_color=TEXT_DARK,
                    corner_radius=6, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
                    command=cmd
                )
                widget.set("")
            
            widget.pack(fill="x")
            self.field_frames[key] = {"frame": row, "widget": widget}

        # Build Fields
        add_field("med_drop", "Medicine", "combo", cmd=self._on_med_select)
        add_field("med_name", "Medicine Name", "entry", "Enter medicine name", cmd=lambda _: self._validate_form())
        add_field("supplier", "Supplier", "combo", cmd=lambda _: self._validate_form())
        add_field("mrp", "MRP (₹)", "entry", "Max Retail Price (Customer sells at)", cmd=lambda _: self._validate_form())
        add_field("purchase", "TRP (₹)", "entry", "Trade Price (Rate for customer)", cmd=lambda _: self._validate_form())
        add_field("batch", "Batch Number", "entry", "3-20 chars", cmd=lambda _: self._validate_form())
        add_field("expiry", "Expiry Date", "entry", "YYYY-MM-DD", cmd=lambda _: self._validate_form())
        add_field("qty", "Quantity (Units)", "entry", "Enter positive number", cmd=lambda _: self._validate_form())

        self.v_lbl = ctk.CTkLabel(self.form_scroll, text="", font=ctk.CTkFont(size=11), text_color=DANGER)
        self.v_lbl.pack(pady=5)

        btn_frame = ctk.CTkFrame(self.form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.save_btn = ctk.CTkButton(
            btn_frame, text="Add Inventory", height=42,
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10,
            fg_color=SUCCESS, hover_color=SUCCESS_HOV, text_color="#FFFFFF",
            command=self._handle_save, state="disabled"
        )
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        clear_btn = ctk.CTkButton(
            btn_frame, text="Reset", height=42,
            font=ctk.CTkFont(size=13), corner_radius=10,
            fg_color="#F3F4F6", hover_color="#E5E7EB", text_color="#374151",
            command=self._clear_form
        )
        clear_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        self._apply_mode_layout()

    def _apply_mode_layout(self):
        """Packs only the required fields depending on the mode."""
        for key in self.field_frames:
            self.field_frames[key]["frame"].pack_forget()

        if self.is_new_medicine_mode:
            self.form_title.configure(text="New Medicine")
            self.toggle_mode_btn.configure(text="Cancel / Switch back", fg_color=DANGER, hover_color="#B91C1C")
            self.save_btn.configure(text="Create & Add Stock")
            
            show_keys = ["med_name", "supplier", "mrp", "purchase", "batch", "expiry", "qty"]
            self.field_frames["med_drop"]["widget"].set("")
        else:
            self.form_title.configure(text="Add Inventory")
            self.toggle_mode_btn.configure(text="➕ Add New Medicine", fg_color=SUCCESS, hover_color=SUCCESS_HOV)
            self.save_btn.configure(text="Add Inventory")

            show_keys = ["med_drop", "supplier", "batch", "expiry", "qty", "purchase"]
            self.field_frames["med_name"]["widget"].delete(0, 'end')
            self.field_frames["mrp"]["widget"].delete(0, 'end')

        for key in show_keys:
            self.field_frames[key]["frame"].pack(padx=20, pady=(4, 8), fill="x", before=self.v_lbl)
        
        self._validate_form()

    def _toggle_mode(self):
        self.is_new_medicine_mode = not self.is_new_medicine_mode
        self._apply_mode_layout()
        if self.is_new_medicine_mode:
            self._safe_focus(self.field_frames["med_name"]["widget"])

    def _on_med_select(self, val):
        """Auto-fill pricing when medicine is selected."""
        med_name = val.strip()
        med_info = next((m for m in self.medicines if m["name"] == med_name), None)
        if med_info:
            trp = med_info.get("trp", 0.0)
            mrp = med_info.get("mrp", 0.0)
            
            t_widget = self.field_frames["purchase"]["widget"]
            m_widget = self.field_frames["mrp"]["widget"]
            
            t_widget.delete(0, 'end')
            if float(trp) > 0:
                t_widget.insert(0, str(trp))
                
            m_widget.delete(0, 'end')
            if float(mrp) > 0:
                m_widget.insert(0, str(mrp))
        self._validate_form()

    def _load_data(self):
        try:
            self.inventory_data = get_inventory_list(self.user["distributor_id"])
            
            self.medicines = fetch_all("SELECT medicine_id, name, trp, mrp FROM medicines ORDER BY name")
            self.suppliers = fetch_all("SELECT supplier_id, name FROM suppliers WHERE distributor_id = %s ORDER BY name", (self.user["distributor_id"],))

            med_names = [m["name"] for m in self.medicines]
            sup_names = [s["name"] for s in self.suppliers]
            
            self.field_frames["med_drop"]["widget"].configure(values=med_names)
            self.field_frames["supplier"]["widget"].configure(values=sup_names)

            self._apply_filters()
        except Exception as e:
            self.loading_lbl.configure(text=f"Error: {e}", text_color=DANGER)

    def _validate_form(self):
        errors = []
        w_med_d = self.field_frames["med_drop"]["widget"].get().strip()
        w_med_n = self.field_frames["med_name"]["widget"].get().strip()
        w_sup = self.field_frames["supplier"]["widget"].get().strip()
        w_batch = self.field_frames["batch"]["widget"].get().strip()
        w_exp = self.field_frames["expiry"]["widget"].get().strip()
        w_qty = self.field_frames["qty"]["widget"].get().strip()
        w_pur = self.field_frames["purchase"]["widget"].get().strip()
        w_mrp = self.field_frames["mrp"]["widget"].get().strip()

        if self.is_new_medicine_mode:
            if not w_med_n: errors.append("Medicine Name required")
            try:
                mrp_f = float(w_mrp)
                if mrp_f <= 0: errors.append("MRP must be > 0")
            except ValueError:
                if not w_mrp: errors.append("MRP required")
            if not w_pur: errors.append("TRP required")
        else:
            if not w_med_d or w_med_d == "Loading...": errors.append("Select Medicine")

        # MRP must always be >= TRP
        try:
            mrp_val = float(w_mrp) if w_mrp else 0
            trp_val = float(w_pur) if w_pur else 0
            if mrp_val > 0 and trp_val > 0 and trp_val > mrp_val:
                errors.append("MRP must be >= TRP")
        except ValueError:
            pass

        if not w_sup or w_sup == "Loading...": errors.append("Select Supplier")
        
        if not re.match(r"^[a-zA-Z0-9]{3,20}$", w_batch):
            errors.append("Batch: 3-20 Alphanumeric")
            self.field_frames["batch"]["widget"].configure(border_color=DANGER)
        else:
            self.field_frames["batch"]["widget"].configure(border_color=SUCCESS)
        
        try:
            if int(w_qty) <= 0: 
                errors.append("Qty > 0")
                self.field_frames["qty"]["widget"].configure(border_color=DANGER)
            else:
                self.field_frames["qty"]["widget"].configure(border_color=SUCCESS)
        except ValueError: 
            errors.append("Qty must be number")
            self.field_frames["qty"]["widget"].configure(border_color=DANGER)

        try:
            if float(w_pur) <= 0: 
                errors.append("TRP > 0")
                self.field_frames["purchase"]["widget"].configure(border_color=DANGER)
            else:
                self.field_frames["purchase"]["widget"].configure(border_color=SUCCESS)
        except ValueError: 
            errors.append("TRP must be number")
            self.field_frames["purchase"]["widget"].configure(border_color=DANGER)

        try:
            val_trp = float(w_pur)
            if val_trp <= 0:
                errors.append("TRP > 0")
                self.field_frames["purchase"]["widget"].configure(border_color=DANGER)
            else:
                self.field_frames["purchase"]["widget"].configure(border_color=SUCCESS)
        except ValueError:
            errors.append("TRP must be number")
            self.field_frames["purchase"]["widget"].configure(border_color=DANGER)

        try:
            exp_d = datetime.strptime(w_exp, "%Y-%m-%d").date()
            if exp_d <= date.today(): 
                errors.append("Expiry > today")
                self.field_frames["expiry"]["widget"].configure(border_color=DANGER)
            else:
                self.field_frames["expiry"]["widget"].configure(border_color=SUCCESS)
        except ValueError: 
            errors.append("Expiry: YYYY-MM-DD")
            self.field_frames["expiry"]["widget"].configure(border_color=DANGER)

        if errors:
            self.v_lbl.configure(text=f"⚠  {errors[0]}")
            self.save_btn.configure(state="disabled", fg_color="#D1D5DB")
        else:
            self.v_lbl.configure(text="✅  Form Valid", text_color=SUCCESS)
            self.save_btn.configure(state="normal", fg_color=SUCCESS)

    def _apply_filters(self):
        query = self.search_var.get().strip().lower()
        for widget in self.scroll.winfo_children(): widget.destroy()

        self.inventory_data.sort(key=lambda x: x.get('expiry_date') if x.get('expiry_date') else date.max)

        filtered = [r for r in self.inventory_data if query in str(r.get("product_name", "")).lower() or query in str(r.get("batch_number", "")).lower()]
        
        if not filtered:
            ctk.CTkLabel(self.scroll, text="No items found.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).pack(pady=40)
            return

        today = date.today()
        for row in filtered:
            f = ctk.CTkFrame(self.scroll, fg_color="transparent", height=45)
            f.pack(fill="x", pady=1)
            f.pack_propagate(False)
            ctk.CTkFrame(self.scroll, fg_color=BORDER_CLR, height=1).pack(fill="x", padx=5)

            exp = row.get("expiry_date")
            qty = int(row.get("quantity", 0))
            is_expired = exp < today if exp else False
            is_near_expiry = (exp - today).days < 30 if exp and not is_expired else False
            is_low_stock = qty < 10

            text_clr = TEXT_DARK
            if is_expired: text_clr = DANGER
            elif is_near_expiry or is_low_stock: text_clr = WARNING

            cols = [
                (str(row.get("product_name", ""))[:20], 160, "w"),
                (str(row.get("batch_number", "")), 100, "w"),
                (str(row.get("supplier_name", "") or "N/A")[:18], 120, "w"),
                (exp.strftime("%d/%m/%y") if exp else "N/A", 85, "w"),
                (str(qty), 50, "center"),
                (f"₹{float(row.get('purchase_price', 0)):.2f}", 80, "center"),
                (f"₹{float(row.get('mrp', 0)):.2f}", 80, "center"),
            ]

            for val, w, anchor in cols:
                ctk.CTkLabel(f, text=val, width=w, font=ctk.CTkFont(size=10, weight="bold" if text_clr != TEXT_DARK else "normal"), text_color=text_clr, anchor=anchor).pack(side="left", padx=3)

            status = "ACTIVE"
            s_bg = "#ECFDF5"; s_fg = "#065F46"
            if is_expired: status = "EXPIRED"; s_bg = "#FEF2F2"; s_fg = "#991B1B"
            elif is_near_expiry: status = "NEAR EXP"; s_bg = "#FFF7ED"; s_fg = "#9A3412"
            elif is_low_stock: status = "LOW STOCK"; s_bg = "#FEFCE8"; s_fg = "#854D0E"

            tag = ctk.CTkFrame(f, fg_color=s_bg, corner_radius=6, height=22, width=90)
            tag.pack_propagate(False)
            tag.pack(side="left", padx=3, pady=10)
            ctk.CTkLabel(tag, text=status, text_color=s_fg, font=ctk.CTkFont(size=9, weight="bold")).pack(expand=True)

            ctk.CTkButton(
                f, text="➕ Add Inventory", width=100, height=26, font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#E0E7FF", hover_color="#C7D2FE", text_color="#3730A3",
                command=lambda r=row: self._prep_add_inventory(r)
            ).pack(side="left", padx=5)

    def _prep_add_inventory(self, row):
        if self.is_new_medicine_mode:
            self._toggle_mode()
        self._clear_form()
        med_name = row.get("product_name")
        self.field_frames["med_drop"]["widget"].set(med_name)
        self._on_med_select(med_name)
        self.field_frames["supplier"]["widget"].set(row.get("supplier_name", ""))
        self._safe_focus(self.field_frames["batch"]["widget"])
        self._validate_form()

    def _handle_save(self):
        sup_name = self.field_frames["supplier"]["widget"].get()
        batch_no = self.field_frames["batch"]["widget"].get().strip().upper()
        exp_date = self.field_frames["expiry"]["widget"].get().strip()
        qty = int(self.field_frames["qty"]["widget"].get().strip())
        trp = float(self.field_frames["purchase"]["widget"].get().strip())
        mrp_input = self.field_frames["mrp"]["widget"].get().strip()
        mrp = float(mrp_input) if mrp_input else 0

        sup_id = next((s["supplier_id"] for s in self.suppliers if s["name"] == sup_name), None)

        if self.is_new_medicine_mode:
            med_name = self.field_frames["med_name"]["widget"].get().strip()
            mrp = float(self.field_frames["mrp"]["widget"].get().strip())

            msg = "Are you sure you want to create this medicine and add inventory?"
            if not messagebox.askyesno("Confirm", msg): return

            try:
                create_medicine(med_name, manufacturer="N/A", category="General", description="", mrp=mrp, trp=trp)
                self.medicines = fetch_all("SELECT medicine_id, name, trp, mrp FROM medicines ORDER BY name")
                med_id = next((m["medicine_id"] for m in self.medicines if m["name"] == med_name), None)
                
                add_new_stock(self.user["distributor_id"], med_id, sup_id, batch_no, exp_date, qty, trp)
                
                messagebox.showinfo("Success", "Medicine and inventory added successfully")
                self._load_data()
                self._clear_form()
                
                if self.is_new_medicine_mode:
                    self._toggle_mode()

            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")
        else:
            med_name = self.field_frames["med_drop"]["widget"].get()
            med_id = next((m["medicine_id"] for m in self.medicines if m["name"] == med_name), None)

            existing = check_batch_exists(self.user["distributor_id"], med_id, batch_no)

            if existing:
                messagebox.showerror("Error", "This batch already exists. Duplicate batches are not allowed. Please enter a different batch number.")
                return

            if not messagebox.askyesno("Confirm", "Are you sure you want to add this inventory?"): return

            try:
                add_new_stock(self.user["distributor_id"], med_id, sup_id, batch_no, exp_date, qty, trp)
                update_medicine_pricing(med_id, trp, mrp=mrp, discount_percent=0) # Update general pricing from batched entry
                messagebox.showinfo("Success", "Inventory added successfully")
                self._load_data()
                self._clear_form()
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

    def _clear_form(self):
        for key in self.field_frames:
            w = self.field_frames[key]["widget"]
            if hasattr(w, "set"): w.set("")
            elif hasattr(w, "delete"): w.delete(0, 'end')
        self.v_lbl.configure(text="")
        self.save_btn.configure(state="disabled")

    def _go_back(self):
        from ui.dashboard import Dashboard
        for widget in self.master.winfo_children(): widget.destroy()
        Dashboard(self.master, self.user, self.app).pack(fill="both", expand=True)

