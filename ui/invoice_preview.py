import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import shutil
import fitz  # PyMuPDF
from PIL import Image, ImageTk

from services.pdf_generator import print_pdf


class InvoicePreview(ctk.CTkToplevel):
    """Integrated PDF viewer for invoice preview inside the application."""

    def __init__(self, master, invoice, pdf_path):
        super().__init__(master)
        self.invoice = invoice
        self.pdf_path = pdf_path
        self.pages = []
        self.tk_images = []

        self.title(f"Invoice {invoice.get('invoice_no', '')} — Preview")
        
        # Larger size for professional preview
        self.geometry("900x850")
        self.minsize(600, 500)
        self.configure(fg_color="#F1F5F9")

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 850) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self.after(100, self._load_pdf)

        # Make it modal-like
        self.grab_set()
        self.focus_set()

    def _build_ui(self):
        # ── Top Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0, height=64)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            toolbar, text=f"📄  Invoice PREVIEW: {self.invoice.get('invoice_no', '')}",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF"
        )
        title_lbl.pack(side="left", padx=25)

        # Action Buttons
        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.pack(side="right", padx=15)

        ctk.CTkButton(
            btn_frame, text="🖨️  Print", width=100, height=34,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6,
            fg_color="#3B82F6", hover_color="#2563EB", text_color="#FFFFFF",
            command=self._print,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="📥  Download", width=110, height=34,
            font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6,
            fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF",
            command=self._download,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Close", width=80, height=34,
            font=ctk.CTkFont(size=12), corner_radius=6,
            fg_color="#475569", hover_color="#334155", text_color="#FFFFFF",
            command=self.destroy,
        ).pack(side="left", padx=5)

        # ── PDF Content Area ──
        self.preview_scroll = ctk.CTkScrollableFrame(self, fg_color="#F8FAFC", corner_radius=0)
        self.preview_scroll.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Inner container to center the pages
        self.pages_container = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        self.pages_container.pack(pady=20, expand=True)

        self.status_lbl = ctk.CTkLabel(
            self.pages_container, text="Loading Invoice...",
            font=ctk.CTkFont(size=13), text_color="#64748B"
        )
        self.status_lbl.pack(pady=100)

    def _load_pdf(self):
        """Render PDF pages using fitz and display them."""
        if not os.path.exists(self.pdf_path):
            self.status_lbl.configure(text="Error: PDF file not found.", text_color="#EF4444")
            return

        try:
            doc = fitz.open(self.pdf_path)
            self.status_lbl.destroy() # Remove loading label

            for i in range(len(doc)):
                page = doc.load_page(i)
                # Increase resolution for clarity
                zoom = 2.0 
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert pixmap to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Create CTkImage or PhotoImage
                # Using CTkImage for high-DPI support if needed, but PhotoImage is faster for scrolling large images
                # Scale down slightly for viewability
                view_width = 750
                view_height = int(pix.height * (750 / pix.width))
                
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(view_width, view_height))
                
                page_lbl = ctk.CTkLabel(self.pages_container, text="", image=ctk_img)
                page_lbl.image = ctk_img # Keep reference
                page_lbl.pack(pady=10, padx=20)
                
            doc.close()
        except Exception as e:
            self.status_lbl.configure(text=f"Error loading preview: {e}", text_color="#EF4444")

    def _download(self):
        """Ask user for location and save a copy of the PDF."""
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
                messagebox.showinfo("Downloaded", f"Invoice saved successfully to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download:\n{e}")

    def _print(self):
        """Invoke system print."""
        try:
            print_pdf(self.pdf_path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot print:\n{e}")
