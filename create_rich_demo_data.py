# -*- coding: utf-8 -*-
from datetime import date
from odoo import fields

print("=== Generating Rich Bangladesh VAT & Mushak Demo Data ===")

company = env['res.company'].search([('name', '=', 'Bengal Tech Solutions Ltd')], limit=1)
assert company, "Company 'Bengal Tech Solutions Ltd' not found!"
bd_country = env.ref('base.bd')
bdt_currency = env['res.currency'].search([('name', '=', 'BDT')], limit=1)

income_account = env['account.account'].search([('company_ids', 'in', company.id), ('account_type', '=', 'income')], limit=1)
expense_account = env['account.account'].search([('company_ids', 'in', company.id), ('account_type', 'in', ('expense', 'expense_direct_cost'))], limit=1)
receivable_account = env['account.account'].search([('company_ids', 'in', company.id), ('account_type', '=', 'asset_receivable')], limit=1)
payable_account = env['account.account'].search([('company_ids', 'in', company.id), ('account_type', '=', 'liability_payable')], limit=1)

# Taxes
tax_vat_15_sale = env['account.tax'].search([
    ('company_id', '=', company.id),
    ('type_tax_use', '=', 'sale'),
    ('amount', '=', 15.0),
    ('tax_group_id.name', 'ilike', 'vat'),
], limit=1)
if not tax_vat_15_sale:
    tax_vat_15_sale = env['account.tax'].create({
        'name': 'VAT 15% (Sale)',
        'amount_type': 'percent',
        'amount': 15.0,
        'type_tax_use': 'sale',
        'company_id': company.id,
    })

tax_sd_20_sale = env['account.tax'].search([
    ('company_id', '=', company.id),
    ('type_tax_use', '=', 'sale'),
    ('tax_group_id.name', 'ilike', 'supplementary'),
], limit=1)

tax_vat_15_purchase = env['account.tax'].search([
    ('company_id', '=', company.id),
    ('type_tax_use', '=', 'purchase'),
    ('amount', '=', 15.0),
], limit=1)
if not tax_vat_15_purchase:
    tax_vat_15_purchase = env['account.tax'].create({
        'name': 'VAT 15% (Purchase)',
        'amount_type': 'percent',
        'amount': 15.0,
        'type_tax_use': 'purchase',
        'company_id': company.id,
    })

journal_sale = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'sale')], limit=1)
journal_purchase = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'purchase')], limit=1)
journal_bank = env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'bank')], limit=1)

print(f"Accounts: Income={income_account.code}, Expense={expense_account.code}")
print(f"Journals: Sale={journal_sale.code}, Purchase={journal_purchase.code}")

# ==============================================================
# 1. PARTNERS (CUSTOMERS & SUPPLIERS)
# ==============================================================
print("\n--- Creating Partners ---")

partners_data = [
    {
        'name': 'Grameenphone Ltd',
        'is_company': True,
        'customer_rank': 1,
        'country_id': bd_country.id,
        'mushak_bin': '0000000010101',
        'mushak_is_vds_entity': True,
        'mushak_vds_entity_type': 'limited_company',
        'street': 'G-P House, Bashundhara R/A',
        'city': 'Dhaka',
        'zip': '1229',
        'property_account_receivable_id': receivable_account.id,
    },
    {
        'name': 'Square Pharmaceuticals PLC',
        'is_company': True,
        'customer_rank': 1,
        'country_id': bd_country.id,
        'mushak_bin': '0001234560101',
        'mushak_is_vds_entity': True,
        'mushak_vds_entity_type': 'limited_company',
        'street': 'Square Centre, 48 Mohakhali C/A',
        'city': 'Dhaka',
        'zip': '1212',
        'property_account_receivable_id': receivable_account.id,
    },
    {
        'name': 'Walton Hi-Tech Industries PLC',
        'is_company': True,
        'customer_rank': 1,
        'country_id': bd_country.id,
        'mushak_bin': '0007890120101',
        'mushak_is_vds_entity': True,
        'mushak_vds_entity_type': 'limited_company',
        'street': 'Plot 1088, Block I, Sabrina Sobhan Road',
        'city': 'Dhaka',
        'zip': '1229',
        'property_account_receivable_id': receivable_account.id,
    },
    {
        'name': 'Chowdhury Retail Traders',
        'is_company': True,
        'customer_rank': 1,
        'country_id': bd_country.id,
        'mushak_bin': False,  # Unregistered buyer!
        'street': 'Shop 14, New Market',
        'city': 'Dhaka',
        'zip': '1205',
        'property_account_receivable_id': receivable_account.id,
    },
    {
        'name': 'Apex Enterprise Systems Ltd',
        'is_company': True,
        'supplier_rank': 1,
        'country_id': bd_country.id,
        'mushak_bin': '0012349870101',
        'mushak_supplier_type': 'service_provider',
        'mushak_is_vds_entity': True,
        'mushak_vds_entity_type': 'limited_company',
        'street': 'BDBL Bhaban (8th Floor), 12 Kazi Nazrul Islam Ave',
        'city': 'Dhaka',
        'zip': '1215',
        'property_account_payable_id': payable_account.id,
    },
    {
        'name': 'Bashundhara Paper & Packaging Ltd',
        'is_company': True,
        'supplier_rank': 1,
        'country_id': bd_country.id,
        'mushak_bin': '0034561230101',
        'mushak_supplier_type': 'manufacturer',
        'mushak_is_vds_entity': True,
        'mushak_vds_entity_type': 'limited_company',
        'street': 'Bashundhara Industrial Complex',
        'city': 'Dhaka',
        'zip': '1229',
        'property_account_payable_id': payable_account.id,
    },
    {
        'name': 'Chittagong Hardware Imports Ltd',
        'is_company': True,
        'supplier_rank': 1,
        'country_id': bd_country.id,
        'mushak_bin': '0056783450101',
        'mushak_supplier_type': 'importer',
        'street': 'Agrabad Commercial Area',
        'city': 'Chittagong',
        'zip': '4100',
        'property_account_payable_id': payable_account.id,
    },
]

partners = {}
for pdata in partners_data:
    p = env['res.partner'].with_company(company).search([('name', '=', pdata['name']), ('company_id', '=', company.id)], limit=1)
    if not p:
        p = env['res.partner'].with_company(company).create(dict(pdata, company_id=company.id))
        print(f"Created Partner: {p.name} (BIN: {p.mushak_bin or 'Unregistered'})")
    else:
        p.write(pdata)
        print(f"Updated Partner: {p.name}")
    partners[p.name] = p

# ==============================================================
# 2. PRODUCTS WITH HS CODES & TAX CONFIGURATIONS
# ==============================================================
print("\n--- Creating Products ---")

products_data = [
    {
        'name': 'Cisco Catalyst 9300 Network Switch 48-Port',
        'mushak_hs_code': '8517.62.00',
        'list_price': 185000.0,
        'standard_price': 140000.0,
        'taxes_id': [(6, 0, [tax_vat_15_sale.id])],
        'supplier_taxes_id': [(6, 0, [tax_vat_15_purchase.id])],
    },
    {
        'name': 'Oracle Enterprise Database Cloud License',
        'mushak_hs_code': '8523.49.00',
        'list_price': 450000.0,
        'standard_price': 320000.0,
        'taxes_id': [(6, 0, [tax_vat_15_sale.id])],
        'supplier_taxes_id': [(6, 0, [tax_vat_15_purchase.id])],
    },
    {
        'name': 'Luxury Automobile Purifier & Fragrance Kit (SD 20%)',
        'mushak_hs_code': '3307.49.00',
        'list_price': 2500.0,
        'standard_price': 1400.0,
        'taxes_id': [(6, 0, [tax_sd_20_sale.id, tax_vat_15_sale.id]) if tax_sd_20_sale else [tax_vat_15_sale.id]],
        'supplier_taxes_id': [(6, 0, [tax_vat_15_purchase.id])],
    },
    {
        'name': 'Datacenter Maintenance & Support AMC (Monthly)',
        'mushak_hs_code': '9983.13.00',
        'list_price': 80000.0,
        'standard_price': 50000.0,
        'taxes_id': [(6, 0, [tax_vat_15_sale.id])],
        'supplier_taxes_id': [(6, 0, [tax_vat_15_purchase.id])],
    },
    {
        'name': 'Armored Single-Mode Fiber Optic Cable (1000m Reel)',
        'mushak_hs_code': '9001.10.00',
        'list_price': 35000.0,
        'standard_price': 24000.0,
        'taxes_id': [(6, 0, [tax_vat_15_sale.id])],
        'supplier_taxes_id': [(6, 0, [tax_vat_15_purchase.id])],
    },
]

products = {}
for prod_data in products_data:
    prod = env['product.product'].with_company(company).search([('name', '=', prod_data['name'])], limit=1)
    if not prod:
        prod = env['product.product'].with_company(company).create(dict(prod_data, company_id=company.id))
        print(f"Created Product: {prod.name} (HS: {prod.mushak_hs_code})")
    else:
        prod.write(prod_data)
        print(f"Found Product: {prod.name}")
    products[prod.name] = prod

# ==============================================================
# 3. SALES INVOICES (MUSHAK 6.3)
# ==============================================================
print("\n--- Creating Customer Invoices (Mushak 6.3) ---")

# Invoice 1: Square Pharma (August 2026)
inv1 = env['account.move'].with_company(company).create({
    'move_type': 'out_invoice',
    'partner_id': partners['Square Pharmaceuticals PLC'].id,
    'journal_id': journal_sale.id,
    'invoice_date': date(2026, 8, 5),
    'invoice_line_ids': [
        (0, 0, {
            'product_id': products['Cisco Catalyst 9300 Network Switch 48-Port'].id,
            'account_id': income_account.id,
            'quantity': 2.0,
            'price_unit': 185000.0,
            'tax_ids': [(6, 0, [tax_vat_15_sale.id])],
        })
    ]
})
inv1.action_post()
print(f"Posted Invoice 1: {inv1.name} -> Mushak {inv1.mushak_form} No: {inv1.mushak_number}, Total: {inv1.amount_total} BDT")

# Invoice 2: Grameenphone with SD 20% + VAT 15% (September 2026)
inv2 = env['account.move'].with_company(company).create({
    'move_type': 'out_invoice',
    'partner_id': partners['Grameenphone Ltd'].id,
    'journal_id': journal_sale.id,
    'invoice_date': date(2026, 9, 12),
    'mushak_vehicle_type': 'Covered Van',
    'mushak_vehicle_number': 'Dhaka Metro-U-14-8891',
    'invoice_line_ids': [
        (0, 0, {
            'product_id': products['Luxury Automobile Purifier & Fragrance Kit (SD 20%)'].id,
            'account_id': income_account.id,
            'quantity': 50.0,
            'price_unit': 2500.0,
            'tax_ids': [(6, 0, [t.id for t in [tax_sd_20_sale, tax_vat_15_sale] if t])],
        })
    ]
})
inv2.action_post()
line2 = inv2.invoice_line_ids.filtered(lambda l: l.display_type == 'product')[:1]
print(f"Posted Invoice 2 (SD+VAT): {inv2.name} -> Mushak {inv2.mushak_form} No: {inv2.mushak_number}, Base={line2.price_subtotal}, SD={line2.mushak_sd_amount}, VAT={line2.mushak_vat_amount}, Total={inv2.amount_total} BDT")

# Invoice 3: Unregistered Retail Customer (October 2026)
inv3 = env['account.move'].with_company(company).create({
    'move_type': 'out_invoice',
    'partner_id': partners['Chowdhury Retail Traders'].id,
    'journal_id': journal_sale.id,
    'invoice_date': date(2026, 10, 1),
    'invoice_line_ids': [
        (0, 0, {
            'product_id': products['Armored Single-Mode Fiber Optic Cable (1000m Reel)'].id,
            'account_id': income_account.id,
            'quantity': 5.0,
            'price_unit': 35000.0,
            'tax_ids': [(6, 0, [tax_vat_15_sale.id])],
        })
    ]
})
inv3.action_post()
print(f"Posted Invoice 3 (Unregistered Buyer): {inv3.name} -> Mushak {inv3.mushak_form} No: {inv3.mushak_number}, Total: {inv3.amount_total} BDT")

# Invoice 4: Walton Hi-Tech (Draft, ready for user interaction!)
inv4 = env['account.move'].with_company(company).create({
    'move_type': 'out_invoice',
    'partner_id': partners['Walton Hi-Tech Industries PLC'].id,
    'journal_id': journal_sale.id,
    'invoice_date': date(2026, 11, 10),
    'invoice_line_ids': [
        (0, 0, {
            'product_id': products['Oracle Enterprise Database Cloud License'].id,
            'account_id': income_account.id,
            'quantity': 1.0,
            'price_unit': 450000.0,
            'discount': 5.0,
            'tax_ids': [(6, 0, [tax_vat_15_sale.id])],
        })
    ]
})
print(f"Created DRAFT Invoice 4: {inv4.id} for Walton Hi-Tech -> State: {inv4.state}, Form Preview: {inv4.mushak_form}, Subtotal: {inv4.amount_untaxed} BDT (Ready for user to Post!)")

# ==============================================================
# 4. CREDIT NOTE (MUSHAK 6.7)
# ==============================================================
print("\n--- Creating Credit Note (Mushak 6.7) ---")

cn1 = env['account.move'].with_company(company).create({
    'move_type': 'out_refund',
    'partner_id': partners['Square Pharmaceuticals PLC'].id,
    'journal_id': journal_sale.id,
    'invoice_date': date(2026, 8, 20),
    'mushak_origin_number': inv1.mushak_number,
    'mushak_origin_date': inv1.invoice_date,
    'mushak_adjustment_reason': 'Port damaged during delivery courier transit; 1 unit returned by buyer.',
    'invoice_line_ids': [
        (0, 0, {
            'product_id': products['Cisco Catalyst 9300 Network Switch 48-Port'].id,
            'account_id': income_account.id,
            'quantity': 1.0,
            'price_unit': 185000.0,
            'tax_ids': [(6, 0, [tax_vat_15_sale.id])],
        })
    ]
})
cn1.action_post()
print(f"Posted Credit Note: {cn1.name} -> Mushak {cn1.mushak_form} No: {cn1.mushak_number}, Ref={cn1.mushak_origin_number}, Total: {cn1.amount_total} BDT")

# ==============================================================
# 5. DEBIT NOTE (MUSHAK 6.8)
# ==============================================================
print("\n--- Creating Debit Note (Mushak 6.8) ---")

dn1 = env['account.move'].with_company(company).create({
    'move_type': 'out_invoice',
    'debit_origin_id': inv2.id,
    'partner_id': partners['Grameenphone Ltd'].id,
    'journal_id': journal_sale.id,
    'invoice_date': date(2026, 9, 25),
    'mushak_origin_number': inv2.mushak_number,
    'mushak_origin_date': inv2.invoice_date,
    'mushak_adjustment_reason': 'Special refrigerated air express freight surcharge.',
    'invoice_line_ids': [
        (0, 0, {
            'name': 'Special Air Freight Handling Surcharge',
            'account_id': income_account.id,
            'quantity': 1.0,
            'price_unit': 15000.0,
            'tax_ids': [(6, 0, [tax_vat_15_sale.id])],
        })
    ]
})
dn1.action_post()
print(f"Posted Debit Note: {dn1.name} -> Mushak {dn1.mushak_form} No: {dn1.mushak_number}, Ref={dn1.mushak_origin_number}, Total: {dn1.amount_total} BDT")

# ==============================================================
# 6. VENDOR BILLS (PURCHASES / MUSHAK 6.1 REGISTER)
# ==============================================================
print("\n--- Creating Vendor Bills (Mushak 6.1 Purchases) ---")

# Bill 1: Apex Systems (With valid Mushak 6.3 challan)
bill1 = env['account.move'].with_company(company).create({
    'move_type': 'in_invoice',
    'partner_id': partners['Apex Enterprise Systems Ltd'].id,
    'journal_id': journal_purchase.id,
    'invoice_date': date(2026, 7, 20),
    'mushak_supplier_challan_number': '6.3-APX-2026-00412',
    'mushak_supplier_challan_date': date(2026, 7, 20),
    'invoice_line_ids': [
        (0, 0, {
            'name': 'Subcontract Datacenter Integration Services',
            'product_id': products['Datacenter Maintenance & Support AMC (Monthly)'].id,
            'account_id': expense_account.id,
            'quantity': 1.0,
            'price_unit': 80000.0,
            'tax_ids': [(6, 0, [tax_vat_15_purchase.id])],
        })
    ]
})
bill1.action_post()
print(f"Posted Vendor Bill 1: {bill1.name} -> Supplier Challan: {bill1.mushak_supplier_challan_number}")

# Bill 2: Bashundhara Paper (With valid Mushak 6.3 challan)
bill2 = env['account.move'].with_company(company).create({
    'move_type': 'in_invoice',
    'partner_id': partners['Bashundhara Paper & Packaging Ltd'].id,
    'journal_id': journal_purchase.id,
    'invoice_date': date(2026, 8, 10),
    'mushak_supplier_challan_number': 'BPPL-VAT-63-9942',
    'mushak_supplier_challan_date': date(2026, 8, 10),
    'invoice_line_ids': [
        (0, 0, {
            'name': 'Custom Anti-Static Protective Packaging',
            'account_id': expense_account.id,
            'quantity': 500.0,
            'price_unit': 100.0,
            'tax_ids': [(6, 0, [tax_vat_15_purchase.id])],
        })
    ]
})
bill2.action_post()
print(f"Posted Vendor Bill 2: {bill2.name} -> Supplier Challan: {bill2.mushak_supplier_challan_number}")

# Bill 3: Chittagong Hardware (Missing Challan -> Input VAT Non-claimable)
bill3 = env['account.move'].with_company(company).create({
    'move_type': 'in_invoice',
    'partner_id': partners['Chittagong Hardware Imports Ltd'].id,
    'journal_id': journal_purchase.id,
    'invoice_date': date(2026, 9, 2),
    'mushak_supplier_challan_number': False,  # Missing!
    'invoice_line_ids': [
        (0, 0, {
            'name': 'Emergency Network Patch Panels (No 6.3 provided)',
            'account_id': expense_account.id,
            'quantity': 10.0,
            'price_unit': 3000.0,
            'tax_ids': [(6, 0, [tax_vat_15_purchase.id])],
        })
    ]
})
bill3.action_post()
print(f"Posted Vendor Bill 3 (Missing Challan): {bill3.name} -> Supplier Challan: None")

# ==============================================================
# 7. VDS CERTIFICATES (MUSHAK 6.6)
# ==============================================================
print("\n--- Creating Mushak 6.6 VDS Certificates ---")

# Certificate 1 (Issued): For Bill 1 (Apex Systems)
cert1 = env['mushak.vds.certificate'].with_company(company).create({
    'direction': 'issued',
    'partner_id': partners['Apex Enterprise Systems Ltd'].id,
    'date': date(2026, 7, 25),
    'company_id': company.id,
    'line_ids': [
        (0, 0, {
            'move_id': bill1.id,
            'challan_number': bill1.mushak_supplier_challan_number,
            'challan_date': bill1.mushak_supplier_challan_date,
            'value_excl_vat': 80000.0,
            'vat_amount': 12000.0,
            'vds_rate': 10.0,
            'vds_amount': 8000.0,
        })
    ]
})
cert1.action_issue()
print(f"Issued Mushak 6.6 Certificate 1: {cert1.name} -> Partner: {cert1.partner_id.name}, VDS Withheld: {cert1.amount_total} BDT, Verification: {cert1.mushak_access_token[:10]}...")

# Certificate 2 (Draft): For Bill 2 (Bashundhara Paper, ready for user interaction!)
cert2 = env['mushak.vds.certificate'].with_company(company).create({
    'direction': 'issued',
    'partner_id': partners['Bashundhara Paper & Packaging Ltd'].id,
    'date': date(2026, 8, 15),
    'company_id': company.id,
    'line_ids': [
        (0, 0, {
            'move_id': bill2.id,
            'challan_number': bill2.mushak_supplier_challan_number,
            'challan_date': bill2.mushak_supplier_challan_date,
            'value_excl_vat': 50000.0,
            'vat_amount': 7500.0,
            'vds_rate': 7.5,
            'vds_amount': 3750.0,
        })
    ]
})
print(f"Created DRAFT Mushak 6.6 Certificate 2: ID {cert2.id} -> Partner: {cert2.partner_id.name}, VDS: {cert2.amount_total} BDT (Ready for user to click 'Issue Certificate' in UI!)")

# ==============================================================
# 8. VERIFY STATUTORY REGISTERS (6.1 & 6.2)
# ==============================================================
print("\n--- Verifying Statutory Registers ---")
reg61_count = env['mushak.register.purchase'].search_count([('company_id', '=', company.id)])
reg62_count = env['mushak.register.sales'].search_count([('company_id', '=', company.id)])
print(f"Mushak 6.1 Purchase Register Rows: {reg61_count}")
print(f"Mushak 6.2 Sales Register Rows: {reg62_count}")

# Commit all demo transactions
env.cr.commit()
print("\n=== Demo Data Creation Completed Successfully & Committed to Database! ===")
