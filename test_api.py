import frappe
import json
frappe.init(site="citytrader.local")
frappe.connect()

try:
    doc = {
        "doctype": "Item",
        "item_code": "TEST_API_ITEM",
        "item_name": "Test API Item",
        "item_group": "Consumable",
        "stock_uom": "Nos",
        "is_stock_item": 1,
        "gst_applicable": 1
    }
    
    result = frappe.get_attr("frappe.client.insert")(doc)
    print("Item created successfully. gst_applicable =", result.gst_applicable)
    
except Exception as e:
    print("Error:", e)
finally:
    frappe.db.rollback()
