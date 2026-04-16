import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import shutil
import fitz  # PyMuPDF
from PIL import Image, ImageTk

from services.pdf_generator import print_pdf

class InvoicePreviewFrame(ctk.CTkFrame):
    """
    Core PDF preview logic extracted into a frame for embedding.
    """
    def __init__(self, master, invoice, pdf_path, **kwargs):
        super().__init__(master, **kwargs)
        self.invoice = invoice
        self.pdf_path = pdf_path
        self._build_ui()
        # Delay load slightly to ensure frame is mapped
        self.after(100, self._load_pdf)

    def _build_ui(self):
        # ── Top Toolbar ──
        self.toolbar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0, height=50)
        self.toolbar.pack(fill="x")
        self.toolbar.pack_propagate(False)

        self.title_lbl = ctk.CTkLabel(
            self.toolbar, text=f"📄  PREVIEW: {self.invoice.get('invoice_no', '')}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF"
        )
        self.title_lbl.pack(side="left", padx=15)

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)

        ctk.CTkButton(
            btn_frame, text="Print", width=80, height=36,
            font=ctk.CTkFont(size=16, weight="bold"), corner_radius=6,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            command=self._print, anchor="center"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="Download", width=100, height=36,
            font=ctk.CTkFont(size=16, weight="bold"), corner_radius=6,
            fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF",
            command=self._download, anchor="center"
        ).pack(side="left", padx=10)

        # ── PDF Content Area ──
        self.preview_scroll = ctk.CTkScrollableFrame(self, fg_color="#F8FAFC", corner_radius=0)
        self.preview_scroll.pack(fill="both", expand=True)
        
        # Inner container to center the pages
        self.pages_container = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        self.pages_container.pack(pady=10, expand=True)

        self.status_lbl = ctk.CTkLabel(
            self.pages_container, text="Loading...",
            font=ctk.CTkFont(size=12), text_color="#64748B"
        )
        self.status_lbl.pack(pady=50)

    def _load_pdf(self):
        """Render PDF pages using fitz and display them."""
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            self.status_lbl.configure(text="No invoice selected.", text_color="#64748B")
            return

        try:
            doc = fitz.open(self.pdf_path)
            # Clear previous pages
            for widget in self.pages_container.winfo_children():
                widget.destroy()

            # Determine width based on frame width (or default to 700 if not yet rendered)
            frame_w = self.preview_scroll.winfo_width()
            if frame_w < 100: frame_w = 700
            
            view_width = int(frame_w * 0.9) # 90% of available width
            if view_width > 700: view_width = 700

            for i in range(len(doc)):
                page = doc.load_page(i)
                zoom = 2.0 
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                view_height = int(pix.height * (view_width / pix.width))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(view_width, view_height))
                
                page_lbl = ctk.CTkLabel(self.pages_container, text="", image=ctk_img)
                page_lbl.image = ctk_img # Keep reference
                page_lbl.pack(pady=5, padx=10)
                
            doc.close()
        except Exception as e:
            if hasattr(self, 'status_lbl') and self.status_lbl.winfo_exists():
                self.status_lbl.configure(text=f"Error: {e}", text_color="#EF4444")

    def _download(self):
        try:
            filename = os.path.basename(self.pdf_path)
            save_path = filedialog.asksaveasfilename(
                title="Download Invoice",
                initialfile=filename,
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")]
            )
            if save_path:
                shutil.copy2(self.pdf_path, save_path)
                messagebox.showinfo("Downloaded", "Saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    def _print(self):
        try:
            print_pdf(self.pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot print: {e}")


class InvoicePreview(ctk.CTkToplevel):
    """Modern toplevel wrapper for the InvoicePreviewFrame."""
    def __init__(self, master, invoice, pdf_path):
        super().__init__(master)
        self.title(f"Invoice {invoice.get('invoice_no', '')} — Preview")
        self.geometry("900x850")
        self.configure(fg_color="#F1F5F9")

        # Reuse the frame
        self.preview_frame = InvoicePreviewFrame(self, invoice, pdf_path, fg_color="transparent")
        self.preview_frame.pack(fill="both", expand=True)

        # Add close button explicitly for the modal
        close_btn = ctk.CTkButton(
            self.preview_frame.toolbar, text="Close", width=80, height=30,
            fg_color="#475569", command=self.destroy
        )
        close_btn.pack(side="right", padx=10)

        self.grab_set()
        self.focus_set()
