"""
╔══════════════════════════════════════════════════════════════════════╗
║         POS AWESOME — FULL SYSTEM DIAGNOSTIC                        ║
║         For ERPNext v15 + Frappe v15                                ║
║                                                                      ║
║  HOW TO RUN:                                                         ║
║    bench --site your.site.name console                               ║
║    Then paste this entire script and press Enter                     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import frappe
from frappe.utils import now_datetime

# ─── Colour helpers (terminal output) ────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):     print(f"  {GREEN}✓  {RESET}{msg}")
def fail(msg):   print(f"  {RED}✗  {RESET}{msg}")
def warn(msg):   print(f"  {YELLOW}⚠  {RESET}{msg}")
def info(msg):   print(f"  {BLUE}ℹ  {RESET}{msg}")
def fix(msg):    print(f"     {DIM}FIX → {msg}{RESET}")
def section(title):
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}")

PASS = 0
FAIL = 0
WARN = 0
FIXES = []

def record(status, label, fix_hint=None):
    global PASS, FAIL, WARN
    if status == "ok":
        PASS += 1; ok(label)
    elif status == "fail":
        FAIL += 1; fail(label)
        if fix_hint:
            fix(fix_hint)
            FIXES.append((label, fix_hint))
    elif status == "warn":
        WARN += 1; warn(label)
        if fix_hint:
            fix(fix_hint)

print(f"\n{BOLD}{'═'*60}")
print("  POS AWESOME DIAGNOSTIC  —  " + now_datetime().strftime("%Y-%m-%d %H:%M"))
print(f"{'═'*60}{RESET}")


# ══════════════════════════════════════════════════════════════════════
# 1. APPS INSTALLED
# ══════════════════════════════════════════════════════════════════════
section("1. Installed Apps")

installed_apps = frappe.get_installed_apps()
for app in ["frappe", "erpnext", "posawesome"]:
    if app in installed_apps:
        ver = frappe.get_attr(f"{app}.__version__") if app != "posawesome" else "installed"
        try:
            ver = frappe.get_attr(f"{app}.__version__")
        except Exception:
            ver = "installed"
        record("ok", f"{app} ({ver})")
    else:
        record("fail", f"{app} NOT installed",
               f"bench get-app {app} && bench --site SITE install-app {app}")

india_app = "india_compliance" in installed_apps
if india_app:
    record("ok", "india_compliance (GST support)")
else:
    record("warn", "india_compliance not installed (needed for GST)",
           "bench get-app india_compliance --branch version-15")


# ══════════════════════════════════════════════════════════════════════
# 2. COMPANY SETUP
# ══════════════════════════════════════════════════════════════════════
section("2. Company Setup")

companies = frappe.get_all("Company", fields=["name","abbr","default_currency","country"])
if companies:
    for c in companies:
        record("ok", f"Company: {c.name} | Abbr: {c.abbr} | Currency: {c.default_currency} | Country: {c.country}")
    default_company = companies[0].name
else:
    record("fail", "No company found",
           "Complete ERPNext Setup Wizard first")
    default_company = None

# GST / GSTIN check
if default_company:
    gstin = frappe.db.get_value("Company", default_company, "gstin")
    if gstin:
        record("ok", f"GSTIN set: {gstin}")
    else:
        record("warn", "GSTIN not set on company",
               f"Setup → Company → {default_company} → enter GSTIN")


# ══════════════════════════════════════════════════════════════════════
# 3. WAREHOUSE SETUP
# ══════════════════════════════════════════════════════════════════════
section("3. Warehouse Setup")

warehouses = frappe.get_all("Warehouse", fields=["name","warehouse_type","is_group"])
active = [w for w in warehouses if not w.is_group]
if active:
    for w in active:
        record("ok", f"Warehouse: {w.name} (type: {w.warehouse_type or 'standard'})")
else:
    record("fail", "No warehouses found",
           "Stock → Warehouse → New (create Main Shop and Storage warehouses)")


# ══════════════════════════════════════════════════════════════════════
# 4. POS PROFILES
# ══════════════════════════════════════════════════════════════════════
section("4. POS Awesome Profiles")

try:
    profiles = frappe.get_all("POS Profile",
        fields=["name","company","warehouse","customer","currency",
                "disabled","payments"],
        filters={"disabled": 0})
    if not profiles:
        record("fail", "No active POS Profiles found",
               "POS Awesome → POS Profile → New")
    else:
        for p in profiles:
            record("ok", f"POS Profile: {p.name}")
            if not p.warehouse:
                record("fail", f"  → No warehouse set on profile '{p.name}'",
                       "Edit POS Profile → set Warehouse")
            else:
                record("ok", f"  → Warehouse: {p.warehouse}")

            if not p.customer:
                record("warn", f"  → No default customer on profile '{p.name}'",
                       "Create 'Walk-in Customer' and set in POS Profile")
            else:
                record("ok", f"  → Default customer: {p.customer}")

            # Check payment methods
            payments = frappe.get_all("POS Payment Method",
                filters={"parent": p.name},
                fields=["mode_of_payment"])
            if payments:
                modes = [pm.mode_of_payment for pm in payments]
                record("ok", f"  → Payment modes: {', '.join(modes)}")
            else:
                record("fail", f"  → No payment methods on profile '{p.name}'",
                       "Add Cash and UPI in POS Profile → Payment Methods table")

            # Check applicable users
            users = frappe.get_all("POS Profile User",
                filters={"parent": p.name},
                fields=["user"])
            if users:
                record("ok", f"  → Applicable users: {', '.join(u.user for u in users)}")
            else:
                record("warn", f"  → No users assigned to profile '{p.name}'",
                       "Edit POS Profile → Applicable for Users → add your cashier")

except Exception as e:
    record("fail", f"Could not read POS Profiles: {e}",
           "Ensure posawesome app is installed correctly")


# ══════════════════════════════════════════════════════════════════════
# 5. ROLE PERMISSIONS — UOM + ALL POS CRITICAL DOCTYPES
# ══════════════════════════════════════════════════════════════════════
section("5. Role Permissions (POS Critical DocTypes)")

# Get all non-system users (cashier-type)
all_roles = frappe.get_all("Role", filters={"disabled": 0, "is_custom": 1}, pluck="name")
system_roles = ["Administrator", "System Manager", "Guest", "All"]

# Check the roles actually assigned to non-admin users
user_roles_map = {}
users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
for user in users:
    if user in ["Administrator", "Guest"]:
        continue
    roles = frappe.get_roles(user)
    non_sys = [r for r in roles if r not in system_roles and r != "All"]
    if non_sys:
        user_roles_map[user] = non_sys

if user_roles_map:
    info(f"Non-admin users found: {list(user_roles_map.keys())}")
else:
    warn("No non-admin system users found — create cashier users first")

# Critical doctypes that POS Awesome MUST read
critical_doctypes = [
    "UOM",
    "Item",
    "Item Price",
    "Customer",
    "POS Profile",
    "Sales Invoice",
    "POS Invoice",
    "Warehouse",
    "Currency",
    "Price List",
    "Item Group",
    "Mode of Payment",
    "Company",
    "Tax Rule",
    "Batch",
    "Serial No",
]

print(f"\n  {DIM}Checking permissions for all non-admin user roles...{RESET}\n")

all_user_roles = set()
for roles in user_roles_map.values():
    all_user_roles.update(roles)

if not all_user_roles:
    all_user_roles = {"POS User"}  # fallback to check default role

for dt in critical_doctypes:
    # Check if any non-system role has read access
    has_access = False
    granting_roles = []
    for role in all_user_roles:
        perms = frappe.get_all("Custom DocPerm",
            filters={"parent": dt, "role": role, "permlevel": 0},
            fields=["read"])
        if perms and perms[0].get("read"):
            has_access = True
            granting_roles.append(role)
            continue
        # Also check standard docperm
        std = frappe.db.sql("""
            SELECT `read` FROM `tabDocPerm`
            WHERE parent=%s AND role=%s AND permlevel=0
            LIMIT 1
        """, (dt, role), as_dict=True)
        if std and std[0].get("read"):
            has_access = True
            granting_roles.append(role)

    if has_access:
        record("ok", f"{dt:30s} → read ✓  (via roles: {', '.join(granting_roles)})")
    else:
        record("fail", f"{dt:30s} → NO READ ACCESS for non-admin users",
               f'Add read perm: frappe.get_doc({{"doctype":"Custom DocPerm","parent":"{dt}","parenttype":"DocType","parentfield":"permissions","role":"POS User","read":1,"permlevel":0}}).insert(); frappe.db.commit()')


# ══════════════════════════════════════════════════════════════════════
# 6. ITEMS & STOCK
# ══════════════════════════════════════════════════════════════════════
section("6. Items & Stock Health")

total_items = frappe.db.count("Item", {"is_sales_item": 1, "disabled": 0})
record("ok" if total_items > 0 else "fail",
       f"Total active sales items: {total_items}",
       "Create items via Stock → Items → New" if total_items == 0 else None)

# Items with no price
items_no_price = frappe.db.sql("""
    SELECT COUNT(DISTINCT i.name) as cnt FROM `tabItem` i
    LEFT JOIN `tabItem Price` ip ON ip.item_code = i.name
        AND ip.price_list = 'Standard Selling' AND ip.selling = 1
    WHERE i.is_sales_item = 1 AND i.disabled = 0 AND ip.name IS NULL
""", as_dict=True)[0].cnt
if items_no_price > 0:
    record("warn", f"{items_no_price} items have no Standard Selling price",
           "Stock → Items → open each item → set Standard Rate, or use Item Price doctype")
else:
    record("ok", "All items have a Standard Selling price")

# Items with no barcode
items_no_barcode = frappe.db.sql("""
    SELECT COUNT(DISTINCT i.name) as cnt FROM `tabItem` i
    LEFT JOIN `tabItem Barcode` ib ON ib.parent = i.name
    WHERE i.is_sales_item = 1 AND i.disabled = 0 AND ib.name IS NULL
""", as_dict=True)[0].cnt
if items_no_barcode > 0:
    record("warn", f"{items_no_barcode} items have no barcode assigned",
           "Run the auto-barcode script or add barcodes manually in each Item form")
else:
    record("ok", "All items have barcodes")

# Items with negative stock
neg_stock = frappe.db.sql("""
    SELECT item_code, warehouse, actual_qty
    FROM `tabBin`
    WHERE actual_qty < 0
    ORDER BY actual_qty ASC
    LIMIT 20
""", as_dict=True)
if neg_stock:
    record("warn", f"{len(neg_stock)} item-warehouse combinations have negative stock")
    for row in neg_stock[:5]:
        print(f"     {RED}–{RESET}  {row.item_code} in {row.warehouse}: {row.actual_qty}")
    if len(neg_stock) > 5:
        print(f"     {DIM}... and {len(neg_stock)-5} more{RESET}")
    fix("Stock → Stock Reconciliation → New → set correct qty for each item")
else:
    record("ok", "No negative stock found")

# Items with no UOM
items_no_uom = frappe.db.count("Item", {"stock_uom": ["in", ["", None]], "is_sales_item": 1})
if items_no_uom:
    record("fail", f"{items_no_uom} items have no UOM set",
           "Open each item and set Default UOM (e.g. Nos, Kg, Gram)")
else:
    record("ok", "All items have a UOM set")


# ══════════════════════════════════════════════════════════════════════
# 7. PRICE LISTS
# ══════════════════════════════════════════════════════════════════════
section("7. Price Lists")

price_lists = frappe.get_all("Price List",
    filters={"enabled": 1},
    fields=["name","currency","selling","buying"])
for pl in price_lists:
    label = f"{pl.name} | {pl.currency}"
    if pl.selling: label += " [selling]"
    if pl.buying:  label += " [buying]"
    record("ok", label)

std_selling = frappe.db.exists("Price List", {"name": "Standard Selling", "enabled": 1})
if not std_selling:
    record("fail", "'Standard Selling' price list not found or disabled",
           "Selling → Price List → New → Name: 'Standard Selling', Currency: INR, Selling: ✓")
else:
    record("ok", "'Standard Selling' price list active")


# ══════════════════════════════════════════════════════════════════════
# 8. PAYMENT MODES
# ══════════════════════════════════════════════════════════════════════
section("8. Mode of Payment & Accounts")

required_modes = ["Cash", "UPI"]
for mode in required_modes:
    exists = frappe.db.exists("Mode of Payment", mode)
    if exists:
        # Check if it has an account linked
        acct = frappe.db.get_value("Mode of Payment Account",
            {"parent": mode, "company": default_company}, "default_account")
        if acct:
            record("ok", f"Mode of Payment '{mode}' → account: {acct}")
        else:
            record("warn", f"Mode of Payment '{mode}' has no account linked for company '{default_company}'",
                   f"Accounts → Mode of Payment → {mode} → add account for your company")
    else:
        record("fail", f"Mode of Payment '{mode}' not found",
               f"Accounts → Mode of Payment → New → Name: {mode}")


# ══════════════════════════════════════════════════════════════════════
# 9. TAX TEMPLATES
# ══════════════════════════════════════════════════════════════════════
section("9. Tax Templates")

tax_templates = frappe.get_all("Sales Taxes and Charges Template",
    filters={"disabled": 0, "company": default_company},
    fields=["name", "is_default"])
if tax_templates:
    for t in tax_templates:
        default_str = " ← DEFAULT" if t.is_default else ""
        record("ok", f"Tax template: {t.name}{default_str}")
else:
    record("warn", "No Sales Tax templates found",
           "Accounts → Sales Taxes and Charges Template → New (create GST Composition 1%)")


# ══════════════════════════════════════════════════════════════════════
# 10. RECENT INVOICES & ERRORS
# ══════════════════════════════════════════════════════════════════════
section("10. Recent POS Activity")

# Check for draft POS invoices (stuck/never submitted)
draft_invoices = frappe.db.count("POS Invoice", {"docstatus": 0})
if draft_invoices > 0:
    record("warn", f"{draft_invoices} POS invoices stuck in Draft status",
           "POS Awesome → Invoice Mgmt → review and submit or cancel drafts")
else:
    record("ok", "No stuck draft POS invoices")

# Count submitted invoices
submitted = frappe.db.count("POS Invoice", {"docstatus": 1})
record("ok", f"Total submitted POS invoices: {submitted}")

# Check for open POS Opening Entries (unclosed shifts)
open_shifts = frappe.db.count("POS Opening Entry", {"status": "Open"})
if open_shifts > 0:
    record("warn", f"{open_shifts} open POS shift(s) — not closed",
           "POS Awesome → Menu → Close Shift to reconcile and close")
else:
    record("ok", "No unclosed POS shifts")


# ══════════════════════════════════════════════════════════════════════
# 11. SITE & SYSTEM SETTINGS
# ══════════════════════════════════════════════════════════════════════
section("11. System & Site Settings")

# Check allow_negative_stock
allow_neg = frappe.db.get_single_value("Stock Settings", "allow_negative_stock")
if allow_neg:
    record("warn", "Allow Negative Stock is ON — items can go below zero",
           "Stock → Stock Settings → Allow Negative Stock → disable after fixing stock levels")
else:
    record("ok", "Allow Negative Stock is OFF (correct for production)")

# Check default currency
default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")
if default_currency == "INR":
    record("ok", f"Default currency: {default_currency}")
else:
    record("warn", f"Default currency is '{default_currency}', expected INR for Indian retail",
           "Setup → Global Defaults → Default Currency → INR")

# Check if scheduler is active
from frappe.utils.background_jobs import get_queue
try:
    q = get_queue("default")
    record("ok", "Background job queue reachable")
except Exception as e:
    record("warn", f"Background queue issue: {e}",
           "bench restart (check Redis is running: sudo service redis status)")

# Site URL
site_config = frappe.get_site_config()
site_url = site_config.get("host_name") or "not configured"
info(f"Site host_name in config: {site_url}")


# ══════════════════════════════════════════════════════════════════════
# 12. GENERATE AUTO-FIX SCRIPT
# ══════════════════════════════════════════════════════════════════════
section("12. One-Click Auto-Fix Script")

# Build the fix for all missing UOM-type permissions
all_broken_roles = set()
for user, roles in user_roles_map.items():
    all_broken_roles.update(roles)

if not all_broken_roles:
    all_broken_roles = {"POS User"}

print(f"""
  {YELLOW}Copy and run this script to auto-fix all permission gaps:{RESET}

  {DIM}─────────────────────────────────────────────────────{RESET}""")

print(f"""
fix_doctypes = {critical_doctypes}
fix_roles = {list(all_broken_roles)}

for dt in fix_doctypes:
    for role in fix_roles:
        exists_custom = frappe.db.exists("Custom DocPerm",
            {{"parent": dt, "role": role, "permlevel": 0}})
        std = frappe.db.sql(
            "SELECT `read` FROM `tabDocPerm` WHERE parent=%s AND role=%s AND permlevel=0 LIMIT 1",
            (dt, role), as_dict=True)
        if std and std[0].get("read"):
            continue  # already has access via standard perm
        if not exists_custom:
            frappe.get_doc({{
                "doctype": "Custom DocPerm",
                "parent": dt,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1,
                "permlevel": 0
            }}).insert()
            print(f"Fixed: {{dt}} → {{role}}")
        else:
            frappe.db.set_value("Custom DocPerm", exists_custom, "read", 1)
            print(f"Updated: {{dt}} → {{role}}")

frappe.db.commit()
print("\\n✓ All permission fixes applied. Run: bench clear-cache")
""")
print(f"  {DIM}─────────────────────────────────────────────────────{RESET}")


# ══════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}{'═'*60}")
print("  DIAGNOSTIC SUMMARY")
print(f"{'═'*60}{RESET}")
print(f"  {GREEN}✓  PASSED:  {PASS}{RESET}")
print(f"  {YELLOW}⚠  WARNINGS: {WARN}{RESET}")
print(f"  {RED}✗  FAILED:  {FAIL}{RESET}")

if FAIL == 0 and WARN == 0:
    print(f"\n  {GREEN}{BOLD}🎉 System is fully configured and ready!{RESET}")
elif FAIL == 0:
    print(f"\n  {YELLOW}System is mostly ready — review warnings above.{RESET}")
else:
    print(f"\n  {RED}System has {FAIL} critical issue(s). Fix them before using POS.{RESET}")
    print(f"\n  {BOLD}Priority fixes:{RESET}")
    for i, (label, fix_hint) in enumerate(FIXES[:5], 1):
        print(f"  {i}. {RED}{label}{RESET}")
        print(f"     {DIM}{fix_hint}{RESET}")

print(f"\n  {DIM}After any fixes: bench --site SITE clear-cache && bench restart{RESET}")
print(f"  {DIM}Then clear browser cache + site data in DevTools.{RESET}\n")
