# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    mushak_value_excl_tax = fields.Monetary(
        string='Value Excl. Duties & VAT',
        compute='_compute_mushak_line_amounts',
        store=True,
        currency_field='currency_id',
        help='Taxable value excluding Supplementary Duty and VAT.',
    )
    mushak_sd_rate = fields.Float(
        string='SD Rate (%)',
        compute='_compute_mushak_line_amounts',
        store=True,
        digits=(16, 2),
        help='Effective Supplementary Duty rate percentage.',
    )
    mushak_sd_amount = fields.Monetary(
        string='SD Amount',
        compute='_compute_mushak_line_amounts',
        store=True,
        currency_field='currency_id',
        help='Calculated Supplementary Duty amount in document currency.',
    )
    mushak_vat_rate = fields.Float(
        string='VAT Rate (%)',
        compute='_compute_mushak_line_amounts',
        store=True,
        digits=(16, 2),
        help='Effective VAT rate percentage.',
    )
    mushak_vat_amount = fields.Monetary(
        string='VAT Amount',
        compute='_compute_mushak_line_amounts',
        store=True,
        currency_field='currency_id',
        help='Calculated VAT amount in document currency.',
    )
    mushak_value_incl_tax = fields.Monetary(
        string='Total Value Incl. Taxes',
        compute='_compute_mushak_line_amounts',
        store=True,
        currency_field='currency_id',
        help='Total value including price, SD, and VAT in document currency.',
    )

    # Company currency fields for statutory registers
    mushak_value_excl_tax_company_curr = fields.Monetary(
        string='Value Excl. Tax (BDT)',
        compute='_compute_mushak_line_amounts',
        store=True,
        currency_field='company_currency_id',
    )
    mushak_sd_amount_company_curr = fields.Monetary(
        string='SD Amount (BDT)',
        compute='_compute_mushak_line_amounts',
        store=True,
        currency_field='company_currency_id',
    )
    mushak_vat_amount_company_curr = fields.Monetary(
        string='VAT Amount (BDT)',
        compute='_compute_mushak_line_amounts',
        store=True,
        currency_field='company_currency_id',
    )

    @api.constrains('tax_ids')
    def _check_mushak_tax_inclusion(self):
        for line in self:
            taxes = line.tax_ids
            if len(taxes) > 1:
                price_included_flags = {tax.price_include for tax in taxes}
                if len(price_included_flags) > 1:
                    raise ValidationError(
                        _("Mixed tax inclusion (some taxes price-included and others price-excluded) "
                          "is not permitted on invoice line '%s'. All taxes on a line must share the same inclusion setting.")
                        % line.name
                    )

    @api.depends(
        'price_unit', 'quantity', 'discount', 'tax_ids',
        'currency_id', 'move_id.move_type', 'move_id.invoice_date'
    )
    def _compute_mushak_line_amounts(self):
        for line in self:
            if line.display_type not in (False, 'product') or not line.move_id.is_invoice(include_receipts=True):
                line.mushak_value_excl_tax = 0.0
                line.mushak_sd_rate = 0.0
                line.mushak_sd_amount = 0.0
                line.mushak_vat_rate = 0.0
                line.mushak_vat_amount = 0.0
                line.mushak_value_incl_tax = 0.0
                line.mushak_value_excl_tax_company_curr = 0.0
                line.mushak_sd_amount_company_curr = 0.0
                line.mushak_vat_amount_company_curr = 0.0
                continue

            price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            is_refund = line.move_id.move_type in ('out_refund', 'in_refund')
            taxes_data = line.tax_ids.compute_all(
                price,
                currency=line.currency_id,
                quantity=line.quantity,
                product=line.product_id,
                partner=line.move_id.partner_id,
                is_refund=is_refund,
            )

            total_excl = taxes_data['total_excluded']
            sd_rate = 0.0
            sd_amount = 0.0
            vat_rate = 0.0
            vat_amount = 0.0

            for tax_res in taxes_data['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                group_name = (tax.tax_group_id.name or '').lower()
                is_sd = 'supplementary' in group_name or 'sd' in group_name or 'sd' in (tax.description or '').lower()
                is_vat = 'vat' in group_name or 'value added' in group_name or 'vat' in (tax.description or '').lower()

                if is_sd:
                    sd_rate += tax.amount
                    sd_amount += tax_res['amount']
                elif is_vat:
                    vat_rate += tax.amount
                    vat_amount += tax_res['amount']

            sign = -1 if is_refund and total_excl > 0 else 1
            line.mushak_value_excl_tax = total_excl * (1 if not is_refund else -1 if total_excl > 0 else 1)
            line.mushak_sd_rate = sd_rate
            line.mushak_sd_amount = sd_amount
            line.mushak_vat_rate = vat_rate
            line.mushak_vat_amount = vat_amount
            line.mushak_value_incl_tax = (total_excl + sd_amount + vat_amount)

            # Convert to company currency
            comp_curr = line.company_currency_id or line.company_id.currency_id
            if line.currency_id and comp_curr and line.currency_id != comp_curr:
                date = line.move_id.invoice_date or fields.Date.today()
                line.mushak_value_excl_tax_company_curr = line.currency_id._convert(
                    line.mushak_value_excl_tax, comp_curr, line.company_id, date
                )
                line.mushak_sd_amount_company_curr = line.currency_id._convert(
                    line.mushak_sd_amount, comp_curr, line.company_id, date
                )
                line.mushak_vat_amount_company_curr = line.currency_id._convert(
                    line.mushak_vat_amount, comp_curr, line.company_id, date
                )
            else:
                line.mushak_value_excl_tax_company_curr = line.mushak_value_excl_tax
                line.mushak_sd_amount_company_curr = line.mushak_sd_amount
                line.mushak_vat_amount_company_curr = line.mushak_vat_amount
