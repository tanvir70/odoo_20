# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class MushakRegisterPurchase(models.Model):
    _name = 'mushak.register.purchase'
    _description = 'Mushak 6.1 Purchase Register'
    _auto = False
    _order = 'invoice_date asc, move_id asc, id asc'

    move_id = fields.Many2one('account.move', string='Bill Reference', readonly=True)
    move_line_id = fields.Many2one('account.move.line', string='Bill Line', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    invoice_date = fields.Date(string='Date', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Supplier', readonly=True)
    partner_name = fields.Char(string='Supplier Name', readonly=True)
    partner_bin = fields.Char(string='Supplier BIN', readonly=True)
    partner_address = fields.Char(string='Supplier Address', readonly=True)
    supplier_challan_number = fields.Char(string='Supplier Challan No (6.3)', readonly=True)
    supplier_challan_date = fields.Date(string='Supplier Challan Date', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_name = fields.Char(string='Description of Goods / Service', readonly=True)
    hs_code = fields.Char(string='HS Code', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    uom_name = fields.Char(string='Unit', readonly=True)
    value_excl_tax = fields.Float(string='Value Excl. Tax (Tk)', readonly=True)
    sd_amount = fields.Float(string='SD (Tk)', readonly=True)
    vat_amount = fields.Float(string='VAT (Tk)', readonly=True)
    total_value = fields.Float(string='Total Value (Tk)', readonly=True)
    is_input_vat_claimable = fields.Boolean(string='Input VAT Claimable', readonly=True)
    remarks = fields.Char(string='Remarks', readonly=True)

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
                    am.commercial_partner_id AS partner_id,
                    rp.name AS partner_name,
                    rp.mushak_bin AS partner_bin,
                    COALESCE(rp.street, '') || ' ' || COALESCE(rp.city, '') AS partner_address,
                    am.mushak_supplier_challan_number AS supplier_challan_number,
                    am.mushak_supplier_challan_date AS supplier_challan_date,
                    aml.product_id AS product_id,
                    aml.name AS product_name,
                    pt.mushak_hs_code AS hs_code,
                    CASE WHEN am.move_type = 'in_refund' THEN -aml.quantity ELSE aml.quantity END AS quantity,
                    uom.name AS uom_name,
                    aml.mushak_value_excl_tax_company_curr AS value_excl_tax,
                    aml.mushak_sd_amount_company_curr AS sd_amount,
                    aml.mushak_vat_amount_company_curr AS vat_amount,
                    (aml.mushak_value_excl_tax_company_curr + aml.mushak_sd_amount_company_curr + aml.mushak_vat_amount_company_curr) AS total_value,
                    CASE
                        WHEN am.mushak_supplier_challan_number IS NOT NULL
                             AND am.mushak_supplier_challan_number != ''
                             AND aml.mushak_vat_amount_company_curr > 0 THEN TRUE
                        ELSE FALSE
                    END AS is_input_vat_claimable,
                    LEFT(COALESCE(am.narration, ''), 100) AS remarks
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                JOIN res_partner rp ON rp.id = am.commercial_partner_id
                LEFT JOIN product_product pp ON pp.id = aml.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN uom_uom uom ON uom.id = aml.product_uom_id
                WHERE am.state = 'posted'
                  AND am.move_type IN ('in_invoice', 'in_refund')
                  AND (aml.display_type IS NULL OR aml.display_type = 'product')
            )
        """ % self._table)
