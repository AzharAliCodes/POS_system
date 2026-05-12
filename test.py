import frappe
frappe.init(site="citytrader.local")
frappe.connect()
fields = frappe.get_all("Custom Field", filters={"dt": "Item"}, fields=["fieldname"])
print("Item Custom Fields:", [f.fieldname for f in fields])

# Check standard rate usage in Item
print("Item Fields:", [f.fieldname for f in frappe.get_meta("Item").fields if "rate" in f.fieldname or "price" in f.fieldname or "tax" in f.fieldname])
