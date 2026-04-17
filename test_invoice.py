import os
import sys

# Add current directory to path to ensure imports work correctly
sys.path.insert(0, r"F:\Pharmiq")

from services.pdf_generator import generate_invoice

def test_generate_invoice():
    data_dict = {
        "invoice": {
            "invoice_no": "TEST-123",
            "invoice_date": "2026-04-17",
            "payment_type": "Credit",
            "discount_amount": 10.0,
            "sgst": 15.0,
            "cgst": 15.0,
            "grand_total": 500.0,
            "amount_in_words": "Five Hundred Rupees Only",
            "items": [
                {
                    "qty": 5,
                    "product_name": "Paracetamol 500mg",
                    "batch_no": "B1234",
                    "expiry_date": "12/28",
                    "mrp": 50.0,
                    "trp": 40.0,
                    "discount_percent": 10.0,
                    "gst_percent": 12.0,
                    "amount": 180.0
                },
                {
                    "qty": 10,
                    "product_name": "Amoxicillin 250mg",
                    "batch_no": "A5678",
                    "expiry_date": "05/27",
                    "mrp": 80.0,
                    "trp": 60.0,
                    "discount_percent": 5.0,
                    "gst_percent": 12.0,
                    "amount": 570.0
                }
            ]
        },
        "distributor": {
            "name": "TEST VENDOR PHARMA",
            "address": "123 Distributor Rd, Pharma City",
            "mobile_no": "9876543210",
            "gst_no": "29TESTD1234G1Z5",
            "drug_license_no": "KA-BLR-12345",
            "bank_name": "HDFC BANK",
            "bank_account_no": "12345678901234",
            "bank_ifsc": "HDFC0001234"
        },
        "customer": {
            "license_holder_name": "RETAIL MANAGER",
            "shop_name": "CITY MEDS PHARMACY",
            "address": "456 Retail Street",
            "mobile_no": "9988776655",
            "gst_no": "29TESTC5678H1Z9",
            "license_no": "KA-BLR-67890"
        },
        "output_path": os.path.join(r"F:\Pharmiq", "test_invoice_demo.pdf")
    }

    try:
        path = generate_invoice(data_dict)
        print(f"SUCCESS: Invoice generated successfully at {path}")
        
        # Test max 20 limits
        data_dict["invoice"]["items"] = data_dict["invoice"]["items"] * 15 # 30 items
        try:
            generate_invoice(data_dict)
            print("ERROR: System allowed >20 items!")
        except ValueError as e:
            print(f"SUCCESS: 20-items validation triggered as expected: {e}")
            
    except Exception as e:
        import traceback
        print(f"ERROR: Failed to generate invoice\\n")
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_invoice()
