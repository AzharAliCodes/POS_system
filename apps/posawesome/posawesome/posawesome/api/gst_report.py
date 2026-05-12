# -*- coding: utf-8 -*-
# GST Sales Report API
# Returns item-level detail for POS Invoices with GST applicable items only

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_gst_sales_data(from_date, to_date, company=None):
	"""
	Fetch POS Invoice items that have a tax template applied (GST applicable).
	Returns item-level rows grouped by invoice for CA-format reporting.
	"""
	if not company:
		company = frappe.defaults.get_user_default("company") or frappe.defaults.get_global_default("company")

	# Get submitted POS Invoices in date range
	invoice_filters = {
		"docstatus": 1,
		"posting_date": ["between", [from_date, to_date]],
	}
	if company:
		invoice_filters["company"] = company

	invoices = frappe.get_all(
		"POS Invoice",
		filters=invoice_filters,
		fields=["name", "customer", "posting_date", "net_total", "total_taxes_and_charges", "grand_total"],
		order_by="posting_date asc, name asc",
	)

	if not invoices:
		return {"invoices": [], "items": [], "summary": {"total_net": 0, "total_gst": 0, "total_grand": 0}}

	invoice_names = [inv["name"] for inv in invoices]

	# Fetch items with tax template set OR posa_tax_applicable checked
	items_with_template = frappe.get_all(
		"POS Invoice Item",
		filters={
			"parent": ["in", invoice_names],
			"item_tax_template": ["!=", ""],
		},
		fields=["parent","item_code","item_name","qty","uom","rate","net_amount","item_tax_template","posa_tax_applicable"],
		order_by="parent asc, idx asc",
	)
	items_with_checkbox = frappe.get_all(
		"POS Invoice Item",
		filters={
			"parent": ["in", invoice_names],
			"posa_tax_applicable": 1,
			"item_tax_template": ["in", ["", None]],
		},
		fields=["parent","item_code","item_name","qty","uom","rate","net_amount","item_tax_template","posa_tax_applicable"],
		order_by="parent asc, idx asc",
	)
	seen = set()
	items = []
	for item in items_with_template + items_with_checkbox:
		key = (item["parent"], item["item_code"])
		if key not in seen:
			seen.add(key)
			items.append(item)

	# Build invoice lookup
	invoice_lookup = {inv["name"]: inv for inv in invoices}

	# Compute GST (1%) per item
	result_items = []
	total_net = 0.0
	total_gst = 0.0

	for item in items:
		net_amount = flt(item.get("net_amount") or 0)
		gst_1pct = round(net_amount * 0.01, 2)
		grand = round(net_amount + gst_1pct, 2)
		inv = invoice_lookup.get(item["parent"], {})

		result_items.append({
			"invoice": item["parent"],
			"posting_date": inv.get("posting_date", ""),
			"customer": inv.get("customer", ""),
			"item_code": item.get("item_code", ""),
			"item_name": item.get("item_name", ""),
			"qty": flt(item.get("qty", 0)),
			"uom": item.get("uom", ""),
			"rate": flt(item.get("rate", 0)),
			"net_amount": net_amount,
			"item_tax_template": item.get("item_tax_template", ""),
			"gst_1pct": gst_1pct,
			"grand_total": grand,
		})

		total_net += net_amount
		total_gst += gst_1pct

	total_grand = round(total_net + total_gst, 2)

	return {
		"items": result_items,
		"invoices": [dict(inv) for inv in invoices],
		"summary": {
			"total_net": round(total_net, 2),
			"total_gst": round(total_gst, 2),
			"total_grand": total_grand,
			"company": company or "",
		},
	}
