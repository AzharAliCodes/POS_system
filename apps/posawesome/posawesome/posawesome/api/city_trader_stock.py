import frappe
from frappe import _
import json

SHOP_WH = "Stores - CT"
HOME_WH = "Home Warehouse - CT"

@frappe.whitelist()
def get_stock_overview():
    items = frappe.db.sql("""
        SELECT
            i.name          AS item_code,
            i.item_name,
            i.stock_uom,
            i.item_group,
            i.gst_applicable,
            COALESCE(i.minimum_shop_qty, 5) AS min_qty,
            COALESCE(s.actual_qty, 0)       AS shop_qty,
            COALESCE(h.actual_qty, 0)       AS home_qty,
            COALESCE(bp.price_list_rate, 0) AS buying_price,
            COALESCE(sp.price_list_rate, 0) AS selling_price,
            COALESCE(s.actual_qty, 0) * COALESCE(bp.price_list_rate, 0) AS shop_value,
            COALESCE(h.actual_qty, 0) * COALESCE(bp.price_list_rate, 0) AS home_value
        FROM `tabItem` i
        LEFT JOIN `tabBin` s  ON s.item_code = i.name AND s.warehouse = %(shop)s
        LEFT JOIN `tabBin` h  ON h.item_code = i.name AND h.warehouse = %(home)s
        LEFT JOIN `tabItem Price` bp ON bp.item_code = i.name
            AND bp.price_list = 'Standard Buying' AND bp.buying = 1
        LEFT JOIN `tabItem Price` sp ON sp.item_code = i.name
            AND sp.price_list = 'Standard Selling' AND sp.selling = 1
        WHERE i.disabled = 0 AND i.is_stock_item = 1
        ORDER BY i.item_name
    """, {"shop": SHOP_WH, "home": HOME_WH}, as_dict=True)
    return items


@frappe.whitelist()
def get_sales_ranking(days=30, limit=10):
    rows = frappe.db.sql("""
        SELECT
            sii.item_code,
            sii.item_name,
            SUM(sii.qty)    AS total_qty,
            SUM(sii.amount) AS total_amount
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.posting_date >= DATE_SUB(CURDATE(), INTERVAL %(days)s DAY)
        GROUP BY sii.item_code, sii.item_name
        ORDER BY total_qty DESC
    """, {"days": int(days)}, as_dict=True)
    return {
        "top": rows[:int(limit)],
        "bottom": list(reversed(rows[-int(limit):])) if len(rows) > int(limit) else rows
    }


@frappe.whitelist()
def create_stock_transfer(items, from_wh, to_wh, notes=""):
    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw(_("No items provided"))

    # Validate stock availability before creating entry
    errors = []
    for it in items:
        qty = float(it.get("qty", 0))
        if qty <= 0:
            continue
        available = frappe.db.get_value(
            "Bin",
            {"item_code": it["item_code"], "warehouse": from_wh},
            "actual_qty"
        ) or 0
        if qty > float(available):
            item_name = frappe.db.get_value("Item", it["item_code"], "item_name") or it["item_code"]
            errors.append(f"{item_name}: need {qty}, only {available} in {from_wh}")

    if errors:
        frappe.throw("Insufficient stock:\n" + "\n".join(errors))

    # Create and submit stock entry
    se = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "from_warehouse": from_wh,
        "to_warehouse": to_wh,
        "remarks": notes or f"City Trader transfer: {from_wh} to {to_wh}",
        "items": [
            {
                "item_code": it["item_code"],
                "qty": float(it["qty"]),
                "uom": it.get("uom", "Nos"),
                "s_warehouse": from_wh,
                "t_warehouse": to_wh,
            }
            for it in items if float(it.get("qty", 0)) > 0
        ]
    })
    se.insert(ignore_permissions=True)
    se.submit()
    frappe.db.commit()
    return {"name": se.name, "status": "Submitted"}


@frappe.whitelist()
def get_recent_transfers(limit=10):
    return frappe.db.sql("""
        SELECT
            se.name,
            se.posting_date,
            se.posting_time,
            se.from_warehouse,
            se.to_warehouse,
            GROUP_CONCAT(DISTINCT sei.item_code SEPARATOR ', ') AS items_summary,
            SUM(sei.qty) AS total_qty
        FROM `tabStock Entry` se
        JOIN `tabStock Entry Detail` sei ON sei.parent = se.name
        WHERE se.stock_entry_type = 'Material Transfer'
          AND se.docstatus = 1
          AND (
            (se.from_warehouse = %(home)s AND se.to_warehouse = %(shop)s)
            OR
            (se.from_warehouse = %(shop)s AND se.to_warehouse = %(home)s)
          )
        GROUP BY se.name
        ORDER BY se.posting_date DESC, se.posting_time DESC
        LIMIT %(limit)s
    """, {"home": HOME_WH, "shop": SHOP_WH, "limit": int(limit)}, as_dict=True)


