# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MushakRegisterSales(models.Model):
    _name = 'mushak.register.sales'
    _description = 'Mushak 6.2 Sales Register'
    _auto = False
    _order = 'invoice_date asc, mushak_number asc, id asc'

    move_id = fields.Many2one('account.move', string='Invoice Reference', readonly=True)
    move_line_id = fields.Many2one('account.move.line', string='Invoice Line', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    invoice_date = fields.Date(string='Date', readonly=True)
    mushak_number = fields.Char(string='Mushak Challan No', readonly=True)
    mushak_form = fields.Selection([
        ('6.3', 'Mushak 6.3'),
        ('6.7', 'Mushak 6.7'),
        ('6.8', 'Mushak 6.8'),
    ], string='Form Type', readonly=True)
    issue_datetime = fields.Datetime(string='Issue Date & Time', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Buyer', readonly=True)
    partner_name = fields.Char(string='Buyer Name', readonly=True)
    partner_bin = fields.Char(string='Buyer BIN', readonly=True)
    partner_address = fields.Char(string='Buyer Address', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_name = fields.Char(string='Description of Goods / Service', readonly=True)
    hs_code = fields.Char(string='HS Code', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    uom_name = fields.Char(string='Unit', readonly=True)
    value_excl_tax = fields.Float(string='Value Excl. Tax (Tk)', readonly=True)
    sd_amount = fields.Float(string='SD (Tk)', readonly=True)
    vat_amount = fields.Float(string='VAT (Tk)', readonly=True)
    total_value = fields.Float(string='Total Value (Tk)', readonly=True)
    state = fields.Selection([
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    aml.id AS id,
                    aml.id AS move_line_id,
                    am.id AS move_id,
                    am.company_id AS company_id,
                    am.invoice_date AS invoice_date,
                    am.mushak_number AS mushak_number,
                    am.mushak_form AS mushak_form,
                    am.mushak_issue_datetime AS issue_datetime,
                    am.commercial_partner_id AS partner_id,
                    rp.name AS partner_name,
                    rp.mushak_bin AS partner_bin,
                    COALESCE(rp.street, '') || ' ' || COALESCE(rp.city, '') AS partner_address,
                    aml.product_id AS product_id,
                    aml.name AS product_name,
                    pt.mushak_hs_code AS hs_code,
                    CASE
                        WHEN am.state = 'cancel' THEN 0.0
                        WHEN am.move_type = 'out_refund' THEN -aml.quantity
                        ELSE aml.quantity
                    END AS quantity,
                    uom.name AS uom_name,
                    CASE
                        WHEN am.state = 'cancel' THEN 0.0
                        ELSE aml.mushak_value_excl_tax_company_curr
                    END AS value_excl_tax,
                    CASE
                        WHEN am.state = 'cancel' THEN 0.0
                        ELSE aml.mushak_sd_amount_company_curr
                    END AS sd_amount,
                    CASE
                        WHEN am.state = 'cancel' THEN 0.0
                        ELSE aml.mushak_vat_amount_company_curr
                    END AS vat_amount,
                    CASE
                        WHEN am.state = 'cancel' THEN 0.0
                        ELSE (aml.mushak_value_excl_tax_company_curr + aml.mushak_sd_amount_company_curr + aml.mushak_vat_amount_company_curr)
                    END AS total_value,
                    am.state AS state
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                JOIN res_partner rp ON rp.id = am.commercial_partner_id
                LEFT JOIN product_product pp ON pp.id = aml.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN uom_uom uom ON uom.id = aml.product_uom_id
                WHERE (am.state = 'posted' OR (am.state = 'cancel' AND am.mushak_number IS NOT NULL))
                  AND am.move_type IN ('out_invoice', 'out_refund')
                  AND (aml.display_type IS NULL OR aml.display_type = 'product')
            )
        """ % self._table)
