# -*- coding: utf-8 -*-
import sys
import logging
from odoo import fields

_logger = logging.getLogger(__name__)

print("=== Starting Setup & Testing for bd_mushak_vat ===")

# 1. Base Setup
bd_country = env.ref('base.bd')
bdt_currency = env['res.currency'].search([('name', '=', 'BDT')], limit=1)
if not bdt_currency.active:
    bdt_currency.active = True

# Ensure web.base.url is set to http://localhost:9004
ICP = env['ir.config_parameter'].sudo()
if hasattr(ICP, 'set_str'):
    ICP.set_str('web.base.url', 'http://localhost:9004')
else:
    ICP.set_param('web.base.url', 'http://localhost:9004')

company_name = "Bengal Tech Solutions Ltd"
company = env['res.company'].search([('name', '=', company_name)], limit=1)
if not company:
    print(f"Creating company: {company_name}")
    company = env['res.company'].create({
        'name': company_name,
        'country_id': bd_country.id,
        'currency_id': bdt_currency.id,
        'street': 'Motijheel Commercial Area, Road 4',
        'city': 'Dhaka',
        'zip': '1000',
    })
else:
    print(f"Found existing company: {company.name} (id={company.id})")

# 2. User Setup First
user_login = "mushak_admin@bengaltech.com"
user_pass = "Mushak@2026Password!"
user = env['res.users'].search([('login', '=', user_login)], limit=1)

group_user = env.ref('base.group_user')
group_account_invoice = env.ref('account.group_account_invoice')
group_account_manager = env.ref('account.group_account_manager')
group_mushak_user = env.ref('bd_mushak_vat.group_mushak_user')
group_mushak_manager = env.ref('bd_mushak_vat.group_mushak_manager')

target_groups = [
    group_user.id,
    group_account_invoice.id,
    group_account_manager.id,
    group_mushak_user.id,
    group_mushak_manager.id,
]

if not user:
    print(f"Creating user: {user_login}")
    user = env['res.users'].create({
        'name': 'Tanvir Ahmed',
        'login': user_login,
        'password': user_pass,
        'company_id': company.id,
        'company_ids': [(6, 0, [company.id])],
        'group_ids': [(6, 0, target_groups)],
    })
    print("User created.")
else:
    print(f"Updating user: {user.name}")
    user.write({
        'password': user_pass,
        'company_id': company.id,
        'company_ids': [(4, company.id)],
        'group_ids': [(4, gid) for gid in target_groups],
    })
    print("User updated.")

# 3. Load Chart of Accounts for Bangladesh if not already loaded
try:
    print("Checking / loading Bangladesh chart of accounts template 'bd'...")
    env['account.chart.template'].try_loading('bd', company)
    print("CoA loaded.")
except Exception as e:
    print(f"CoA loading note/warning: {e}")

# 4. Activate Bangladesh VAT fields on the company
company.partner_id.write({
    'mushak_bin': '1234567890123',
    'mushak_is_vds_entity': True,
    'mushak_vds_entity_type': 'limited_company',
})
company.write({
    'mushak_vat_circle': 'Circle-01 (Motijheel), LTU Dhaka',
    'mushak_signatory_id': user.id,
})
print("Company Bangladesh VAT parameters configured:")
print(f"  BIN: {company.mushak_bin}")
print(f"  VAT Circle: {company.mushak_vat_circle}")
print(f"  VDS Entity: {company.mushak_is_vds_entity} ({company.partner_id.mushak_vds_entity_type})")
print(f"  Signatory: {company.mushak_signatory_id.name}")

# 5. Create or find Sales Taxes: SD 20% and VAT 15%
tax_group_vat = env['account.tax.group'].search([('company_id', '=', company.id), ('name', 'ilike', 'vat')], limit=1)
if not tax_group_vat:
    tax_group_vat = env['account.tax.group'].create({
        'name': 'VAT',
        'company_id': company.id,
    })

tax_group_sd = env['account.tax.group'].search([('company_id', '=', company.id), ('name', 'ilike', 'sd')], limit=1)
if not tax_group_sd:
    tax_group_sd = env['account.tax.group'].create({
        'name': 'Supplementary Duty',
        'company_id': company.id,
    })

# Supplementary Duty (SD 20%)
sd_tax = env['account.tax'].search([
    ('company_id', '=', company.id),
    ('type_tax_use', '=', 'sale'),
    ('tax_group_id', '=', tax_group_sd.id),
], limit=1)
if not sd_tax:
    print("Creating Sales SD 20% tax...")
    sd_tax = env['account.tax'].create({
        'name': 'Supplementary Duty (SD) 20%',
        'amount_type': 'percent',
        'amount': 20.0,
        'type_tax_use': 'sale',
        'company_id': company.id,
        'tax_group_id': tax_group_sd.id,
        'include_base_amount': True,
        'sequence': 1,
    })

# Value Added Tax (VAT 15%)
vat_tax = env['account.tax'].search([
    ('company_id', '=', company.id),
    ('type_tax_use', '=', 'sale'),
    ('tax_group_id', '=', tax_group_vat.id),
    ('amount', '=', 15.0),
], limit=1)
if not vat_tax:
    print("Creating Sales VAT 15% tax...")
    vat_tax = env['account.tax'].create({
        'name': 'Value Added Tax (VAT) 15%',
        'amount_type': 'percent',
        'amount': 15.0,
        'type_tax_use': 'sale',
        'company_id': company.id,
        'tax_group_id': tax_group_vat.id,
        'sequence': 2,
    })

print(f"Using Taxes: SD Tax = {sd_tax.name} (id={sd_tax.id}), VAT Tax = {vat_tax.name} (id={vat_tax.id})")

# 6. Test Partner (Customer)
customer = env['res.partner'].with_company(company).search([
    ('name', '=', 'Padma Technologies Ltd'),
    ('company_id', '=', company.id),
], limit=1)
if not customer:
    customer = env['res.partner'].with_company(company).create({
        'name': 'Padma Technologies Ltd',
        'country_id': bd_country.id,
        'mushak_bin': '9876543210987',
        'company_id': company.id,
        'customer_rank': 1,
        'street': 'Gulshan-2, Road 11',
        'city': 'Dhaka',
    })
    print(f"Customer created: {customer.name} with BIN {customer.mushak_bin}")
else:
    print(f"Found customer: {customer.name}")

# 7. Test Invoice Creation & Posting (Mushak 6.3)
journal = env['account.journal'].search([
    ('company_id', '=', company.id),
    ('type', '=', 'sale'),
], limit=1)

print(f"Using Sales Journal: {journal.name} (id={journal.id})")
company.write({'mushak_journal_ids': [(4, journal.id)]})

invoice = env['account.move'].with_company(company).create({
    'move_type': 'out_invoice',
    'partner_id': customer.id,
    'journal_id': journal.id,
    'invoice_date': fields.Date.today(),
    'invoice_line_ids': [
        (0, 0, {
            'name': 'Enterprise Telecom Server & Licenses',
            'quantity': 1.0,
            'price_unit': 10000.0,
            'tax_ids': [(6, 0, [sd_tax.id, vat_tax.id])],
        })
    ]
})

print(f"Draft Invoice created: {invoice.id}, amount_untaxed={invoice.amount_untaxed}")
print(f"Pre-post mushak_form={invoice.mushak_form}, mushak_number={invoice.mushak_number}")

print("Posting invoice...")
invoice.action_post()

print("=== Post-Validation Inspection ===")
print(f"State: {invoice.state}")
print(f"Mushak Form: {invoice.mushak_form} (Expected: 6.3)")
print(f"Mushak Number: {invoice.mushak_number}")
print(f"Mushak Access Token: {invoice.mushak_access_token}")
verification_url = invoice.get_mushak_verification_url()
print(f"Mushak Verification URL: {verification_url}")

line = invoice.invoice_line_ids.filtered(lambda l: l.display_type in (False, 'product'))[:1]
print(f"Line 1 Name: {line.name}")
print(f"Line 1 Display Type: {line.display_type}")
print(f"Line 1 Base Price: {line.price_subtotal}")
print(f"Line 1 SD Amount: {line.mushak_sd_amount} (Expected: 2000.0)")
print(f"Line 1 VAT Amount: {line.mushak_vat_amount} (Expected: 1800.0)")
print(f"Line 1 Value Incl Tax: {line.mushak_value_incl_tax} (Expected: 13800.0)")
print(f"Invoice Total Amount: {invoice.amount_total} (Expected: 13800.0)")

assert invoice.mushak_form == '6.3', f"mushak_form mismatch: {invoice.mushak_form}"
assert invoice.mushak_number, "mushak_number not generated!"
assert invoice.mushak_access_token, "mushak_access_token not generated!"
assert abs(line.mushak_sd_amount - 2000.0) < 0.01, f"SD calculation mismatch: {line.mushak_sd_amount}"
assert abs(line.mushak_vat_amount - 1800.0) < 0.01, f"VAT calculation mismatch: {line.mushak_vat_amount}"
assert abs(invoice.amount_total - 13800.0) < 0.01, f"Total amount mismatch: {invoice.amount_total}"

# 8. Test QWeb HTML / Document Generation
print("Testing Mushak 6.3 QWeb HTML rendering...")
report_action = env.ref('bd_mushak_vat.action_report_mushak_63')
html_content, content_type = report_action.with_company(company)._render_qweb_html(report_action.id, [invoice.id])
print(f"QWeb HTML rendered successfully! Size: {len(html_content)} bytes")
assert len(html_content) > 500, "HTML content too small!"
html_str = html_content.decode('utf-8') if isinstance(html_content, (bytes, bytearray)) else html_content
assert "মূসক-৬.৩" in html_str or "6.3" in html_str, "Mushak 6.3 header missing from rendered document!"
print("Mushak 6.3 report contains expected Bangla statutory headings!")

# 9. Verify token logic
token_check = env['account.move'].sudo().search([('mushak_access_token', '=', invoice.mushak_access_token)], limit=1)
assert token_check.id == invoice.id, "Token verification failed!"
print("Token lookup test passed!")

# Commit all changes so they persist in database
env.cr.commit()
print("=== All tests & setup completed successfully and committed! ===")
