#!/usr/bin/env python3
"""
Purchase Order Generator with GUI
Generates PDF purchase orders from orders_export.csv using a layout matching the reference.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
from backend import load_orders, generate_pdf_po
    # We will let the GUI start but warn on generation if missing





class POGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SuperDealsPOGen")
        self.root.geometry("500x600")
        
        # Load settings
        self.settings_file = "settings.json"
        self.load_settings()
        
        
        # Load default products if available
        self.products = load_orders("orders_export.csv")
        self.sorted_products = []
        if self.products:
             self.sorted_products = sorted(self.products.items(), key=lambda x: x[0])
        
        # Create UI
        self.create_widgets()
        
    def load_settings(self):
        self.settings = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        # Ensure saved_vendors list exists
        if 'saved_vendors' not in self.settings:
            self.settings['saved_vendors'] = []

    def save_settings(self):
        # Gather current values
        current_settings = {
            'company_info': {k: v.get() for k, v in self.company_vars.items()},
            'vendor_info': {k: v.get() for k, v in self.vendor_vars.items()},
            'ship_to_info': {k: v.get() for k, v in self.ship_to_vars.items()},
            'ship_to_info': {k: v.get() for k, v in self.ship_to_vars.items()},
            'logo_path': self.logo_path_var.get(),
            'saved_vendors': self.settings.get('saved_vendors', [])
        }
        
        # Update logic for saved vendors
        current_vendor = current_settings['vendor_info']
        vendor_name = current_vendor.get('name', '').strip()
        
        if vendor_name and vendor_name != '[VENDOR NAME]':
            # Check if vendor exists in saved list
            found = False
            for i, v in enumerate(current_settings['saved_vendors']):
                if v.get('name') == vendor_name:
                    current_settings['saved_vendors'][i] = current_vendor
                    found = True
                    break
            
            if not found:
                current_settings['saved_vendors'].append(current_vendor)
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(current_settings, f, indent=4)
            self.settings = current_settings # Update internal state
            
            # Refresh vendor combobox if it exists
            if hasattr(self, 'vendor_combo'):
                saved_vendors = self.settings.get('saved_vendors', [])
                vendor_names = [v.get('name') for v in saved_vendors]
                self.vendor_combo['values'] = vendor_names
                
        except Exception as e:
            print(f"Error saving settings: {e}")

    def save_settings_click(self):
        self.save_settings()
        messagebox.showinfo("Success", "Settings saved")

    def create_widgets(self):
        # Configure styles
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        # Main container with scrolling if needed (simplified to text scrolling for now)
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Bottom Section: Generate (Pack First to ensure visibility) ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 5))
        
        generate_btn = ttk.Button(bottom_frame, text="Generate", 
                                  command=self.generate_po, style='Accent.TButton')
        generate_btn.pack(side=tk.RIGHT, ipadx=20, ipady=5)
        
        # --- Content Area (Vertical Split) ---
        content_paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        content_paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Top Frame (Products)
        product_frame = ttk.LabelFrame(content_paned, text="1. Select Product", padding="5")
        content_paned.add(product_frame, weight=1)
        
        # Load CSV Button
        btn_frame = ttk.Frame(product_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 2))
        ttk.Button(btn_frame, text="Load CSV File...", command=self.load_csv).pack(side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(product_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Reduced height to 6 lines
        self.product_listbox = tk.Listbox(product_frame, selectmode=tk.EXTENDED, height=6, yscrollcommand=scrollbar.set, font=('Arial', 10))
        self.product_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.product_listbox.yview)
        
        # Populate list
        self.refresh_product_list()

        # Bottom Frame (Inputs)
        details_frame = ttk.LabelFrame(content_paned, text="2. Edit Details", padding="5")
        content_paned.add(details_frame, weight=2)
        
        notebook = ttk.Notebook(details_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Company Info Tab
        company_frame = ttk.Frame(notebook, padding="10")
        notebook.add(company_frame, text="Company (You)")
        self.create_company_info_fields(company_frame)
        
        # Vendor Info Tab
        vendor_frame = ttk.Frame(notebook, padding="10")
        notebook.add(vendor_frame, text="Vendor")
        self.create_vendor_info_fields(vendor_frame)
        
        # Ship To Info Tab
        ship_to_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ship_to_frame, text="Ship To")
        self.create_ship_to_fields(ship_to_frame)
        

    def load_csv(self):
        filename = filedialog.askopenfilename(
            title="Select Orders CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filename:
            loaded_products = load_orders(filename)
            if not loaded_products:
                messagebox.showwarning("Warning", "No valid products found in selected CSV.")
                return
            
            self.products = loaded_products
            self.refresh_product_list()
            messagebox.showinfo("Success", f"Loaded {len(self.products)} products.")

    def refresh_product_list(self):
        self.product_listbox.delete(0, tk.END)
        self.sorted_products = sorted(self.products.items(), key=lambda x: x[0])
        
        for product_name, sizes in self.sorted_products:
            total_qty = sum(sizes.values())
            display_text = f"{product_name} ({total_qty} units)"
            self.product_listbox.insert(tk.END, display_text)

    def create_company_info_fields(self, parent):
        self.company_vars = {}
        # Load saved logo path or default
        saved_logo = self.settings.get('logo_path', '')
        self.logo_path_var = tk.StringVar(value=saved_logo)
        
        # Logo Selection
        logo_frame = ttk.Frame(parent)
        logo_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(logo_frame, text="Company Logo:").pack(side=tk.LEFT)
        ttk.Entry(logo_frame, textvariable=self.logo_path_var, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(logo_frame, text="Browse...", command=self.browse_logo).pack(side=tk.LEFT)
        
        # Text Fields
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill=tk.X)
        grid_frame.columnconfigure(1, weight=1)
        
        saved_company = self.settings.get('company_info', {})
        
        fields = [
            ('name', 'Company Name:', saved_company.get('name', 'BJJ Super Deals')),
            ('address', 'Street Address:', saved_company.get('address', '123 Jiu Jitsu Way')),
            ('city', 'City, ST, ZIP:', saved_company.get('city', 'Los Angeles, CA 90001')),
            ('phone', 'Phone:', saved_company.get('phone', '555-0123')),
            ('fax', 'Fax:', saved_company.get('fax', '')),
        ]
        
        for idx, (key, label, default) in enumerate(fields):
            ttk.Label(grid_frame, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(grid_frame, textvariable=var)
            entry.grid(row=idx, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            self.company_vars[key] = var
            
        ttk.Button(parent, text="Save Company Info", command=self.save_settings_click).pack(pady=5)
            
    def browse_logo(self):
        filename = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All Files", "*.*")]
        )
        if filename:
            self.logo_path_var.set(filename)
    
    def create_vendor_info_fields(self, parent):
        self.vendor_vars = {}
        
        # Saved Vendor Selection
        saved_vendors = self.settings.get('saved_vendors', [])
        vendor_names = [v.get('name') for v in saved_vendors]
        
        selection_frame = ttk.Frame(parent)
        selection_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(selection_frame, text="Select Saved Vendor:").pack(side=tk.LEFT)
        self.vendor_combo = ttk.Combobox(selection_frame, values=vendor_names, state="readonly", width=30)
        self.vendor_combo.pack(side=tk.LEFT, padx=5)
        self.vendor_combo.bind("<<ComboboxSelected>>", self.on_vendor_selected)
        
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill=tk.X)
        grid_frame.columnconfigure(1, weight=1)
        
        saved_vendor = self.settings.get('vendor_info', {})
        
        fields = [
            ('name', 'Vendor Name:', saved_vendor.get('name', '[VENDOR NAME]')),
            ('website', 'Website:', saved_vendor.get('website', '')),
            ('address', 'Street Address:', saved_vendor.get('address', '')),
            ('city', 'City, ST, ZIP:', saved_vendor.get('city', '')),
            ('phone', 'Phone:', saved_vendor.get('phone', '')),
        ]
        
        for idx, (key, label, default) in enumerate(fields):
            ttk.Label(grid_frame, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(grid_frame, textvariable=var)
            entry.grid(row=idx, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            self.vendor_vars[key] = var
            
        ttk.Button(parent, text="Save Vendor", command=self.save_settings_click).pack(pady=5)
            
    def on_vendor_selected(self, event):
        selected_name = self.vendor_combo.get()
        saved_vendors = self.settings.get('saved_vendors', [])
        
        for vendor in saved_vendors:
            if vendor.get('name') == selected_name:
                # Update text fields
                for key, var in self.vendor_vars.items():
                    if key in vendor:
                        var.set(vendor[key])
                break
    
    def create_ship_to_fields(self, parent):
        self.ship_to_vars = {}
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill=tk.X)
        grid_frame.columnconfigure(1, weight=1)
        
        saved_ship = self.settings.get('ship_to_info', {})
        
        fields = [
            ('attn', 'Attention:', saved_ship.get('attn', '[ATTN NAME]')),
            ('company', 'Company Name:', saved_ship.get('company', 'BJJ Super Deals Warehouse')),
            ('address', 'Street Address:', saved_ship.get('address', '')),
            ('city', 'City, ST, ZIP:', saved_ship.get('city', '')),
            ('phone', 'Phone:', saved_ship.get('phone', '')),
            ('website', 'Website:', saved_ship.get('website', '')),
        ]
        
        for idx, (key, label, default) in enumerate(fields):
            ttk.Label(grid_frame, text=label).grid(row=idx, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(grid_frame, textvariable=var)
            entry.grid(row=idx, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
            self.ship_to_vars[key] = var
            
        ttk.Button(parent, text="Save Ship To", command=self.save_settings_click).pack(pady=5)
    
    def generate_po(self):
        # Check if product is selected
        selection = self.product_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select at least one product!")
            return
        
        # Save current settings for next time
        self.save_settings()
        
        # Collect all selected products
        selected_products = []
        for idx in selection:
            selected_products.append(self.sorted_products[idx])
        
        # Get all field values
        company_info = {key: var.get() for key, var in self.company_vars.items()}
        vendor_info = {key: var.get() for key, var in self.vendor_vars.items()}
        ship_to_info = {key: var.get() for key, var in self.ship_to_vars.items()}
        logo_path = self.logo_path_var.get()
        
        # Ask for save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if len(selected_products) == 1:
            prod_name = selected_products[0][0]
            safe_name = "".join(c if c.isalnum() else "_" for c in prod_name)
            default_filename = f"PO_{safe_name}_{timestamp}.pdf"
        else:
            default_filename = f"PO_Multiple_Items_{timestamp}.pdf"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if not filename:
            return
        
        try:
            generate_pdf_po(selected_products, company_info, vendor_info, ship_to_info, filename, logo_path)
            messagebox.showinfo("Success", f"Purchase Order generated successfully!\n\nSaved to: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}\n\n(Make sure 'reportlab' is installed)")


def main():
    root = tk.Tk()
    app = POGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
