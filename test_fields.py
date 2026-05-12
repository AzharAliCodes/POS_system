import frappe
frappe.init(site="citytrader.local")
frappe.connect()

meta = frappe.get_meta("Item")
print("Item Fields:")
for f in meta.fields:
    if "tax" in f.fieldname or "gst" in f.fieldname or "rate" in f.fieldname or "price" in f.fieldname:
        print("-", f.fieldname, f.fieldtype)

print("\nCustom Fields:")
customs = frappe.get_all("Custom Field", filters={"dt": "Item"}, fields=["fieldname", "fieldtype"])
for f in customs:
    print("-", f.fieldname, f.fieldtype)
