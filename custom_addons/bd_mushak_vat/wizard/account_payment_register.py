# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    mushak_apply_vds = fields.Boolean(
        string='Withhold VAT at Source (VDS)',
        compute='_compute_mushak_vds_info',
        store=True,
        readonly=False,
        help='Indicates whether VAT Deduction at Source applies to this payment.',
    )
    mushak_vds_amount = fields.Monetary(
        string='VDS Withheld Amount',
        compute='_compute_mushak_vds_info',
        store=True,
        readonly=False,
        currency_field='currency_id',
        help='Amount of VAT deducted at source for this payment.',
    )
    mushak_vds_rate = fields.Float(
        string='Effective VDS Rate (%)',
        compute='_compute_mushak_vds_info',
        store=True,
        readonly=False,
    )
    mushak_vds_account_id = fields.Many2one(
        comodel_name='account.account',
        string='VDS Account',
        compute='_compute_mushak_vds_info',
        store=True,
        readonly=False,
        help='VDS Payable (liability) or VDS Receivable (asset) account for the write-off.',
    )

    @api.depends('line_ids', 'partner_id', 'company_id', 'payment_type', 'amount')
    def _compute_mushak_vds_info(self):
        for wizard in self:
            moves = wizard.line_ids.move_id
            if not moves:
                wizard.mushak_apply_vds = False
                wizard.mushak_vds_amount = 0.0
                wizard.mushak_vds_rate = 0.0
                wizard.mushak_vds_account_id = False
                continue

            is_outbound = wizard.payment_type == 'outbound'
            is_inbound = wizard.payment_type == 'inbound'

            # 1. Outbound: We are withholding entity paying vendor bills
            if is_outbound and wizard.company_id.mushak_is_vds_entity:
                target_account = wizard.company_id.mushak_vds_payable_account_id
                vds_applicable = True
            # 2. Inbound: Customer is withholding entity paying our customer invoice
            elif is_inbound and wizard.partner_id.mushak_is_vds_entity:
                target_account = wizard.company_id.mushak_vds_receivable_account_id
                vds_applicable = True
            else:
                target_account = False
                vds_applicable = False

            if not vds_applicable or not target_account:
                wizard.mushak_apply_vds = False
                wizard.mushak_vds_amount = 0.0
                wizard.mushak_vds_rate = 0.0
                wizard.mushak_vds_account_id = target_account
                continue

            # Compute VDS across invoice product lines
            total_bill_amount = sum(abs(m.amount_total) for m in moves) or 1.0
            total_bill_vds = 0.0
            highest_rate = 0.0

            for move in moves:
                for line in move.invoice_line_ids.filtered(lambda l: l.display_type in (False, 'product')):
                    rule = self.env['mushak.vds.rule'].match_rule(
                        service_code_id=line.product_id.mushak_vds_service_code_id.id if line.product_id else False,
                        supplier_type=wizard.partner_id.mushak_supplier_type,
                        invoice_vat_rate=line.mushak_vat_rate,
                        payment_date=wizard.payment_date,
                        company_id=wizard.company_id.id,
                    )
                    if rule and not rule.exempt:
                        base = abs(line.mushak_value_excl_tax)
                        if wizard.company_id.mushak_vds_include_sd:
                            base += abs(line.mushak_sd_amount)
                        rate = rule.vds_rate
                        line_vds = base * (rate / 100.0)
                        total_bill_vds += line_vds
                        highest_rate = max(highest_rate, rate)
                    elif line.mushak_vat_amount > 0 and not rule:
                        # Fallback default: standard full VAT withholding on designated entity bills
                        highest_rate = max(highest_rate, line.mushak_vat_rate or 15.0)

            # Proportional share for partial payment
            payment_share_ratio = min(1.0, (wizard.amount or 0.0) / total_bill_amount) if total_bill_amount else 1.0
            this_payment_vds = total_bill_vds * payment_share_ratio

            wizard.mushak_apply_vds = True if this_payment_vds > 0 else False
            wizard.mushak_vds_amount = this_payment_vds
            wizard.mushak_vds_rate = highest_rate
            wizard.mushak_vds_account_id = target_account

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)

        if self.mushak_apply_vds and self.mushak_vds_amount > 0 and self.mushak_vds_account_id:
            write_off_amount = -self.mushak_vds_amount if self.payment_type == 'outbound' else self.mushak_vds_amount
            moves = self.line_ids.move_id
            move_ref = ', '.join(moves.mapped('name')) if moves else (self.communication or '')
            label = _("VDS Withheld – %s") % move_ref

            vds_writeoff_line = {
                'name': label,
                'account_id': self.mushak_vds_account_id.id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'currency_id': self.currency_id.id,
                'amount_currency': write_off_amount,
                'balance': self.currency_id._convert(
                    write_off_amount, self.company_id.currency_id, self.company_id, self.payment_date
                ),
            }
            payment_vals['write_off_line_vals'].append(vds_writeoff_line)

        return payment_vals

    def _create_payments(self):
        payments = super()._create_payments()

        # Generate Mushak 6.6 Certificate for VDS payments
        if self.mushak_apply_vds and self.mushak_vds_amount > 0:
            for payment in payments:
                direction = 'issued' if payment.payment_type == 'outbound' else 'received'
                moves = self.line_ids.move_id
                cert_lines = []
                for move in moves:
                    challan_no = move.mushak_number or move.mushak_supplier_challan_number or move.name
                    challan_dt = move.invoice_date or move.mushak_supplier_challan_date
                    val_excl = sum(move.invoice_line_ids.mapped('mushak_value_excl_tax'))
                    vat_val = sum(move.invoice_line_ids.mapped('mushak_vat_amount'))
                    cert_lines.append((0, 0, {
                        'move_id': move.id,
                        'challan_number': challan_no,
                        'challan_date': challan_dt,
                        'value_excl_vat': abs(val_excl),
                        'vat_amount': abs(vat_val),
                        'vds_rate': self.mushak_vds_rate,
                        'vds_amount': self.mushak_vds_amount,
                    }))

                cert = self.env['mushak.vds.certificate'].create({
                    'direction': direction,
                    'company_id': self.company_id.id,
                    'partner_id': self.partner_id.id,
                    'payment_id': payment.id,
                    'date': self.payment_date,
                    'currency_id': self.currency_id.id,
                    'deposit_method': 'return_adjustment',
                    'line_ids': cert_lines,
                })
                if direction == 'issued':
                    cert.action_issue()
                else:
                    cert.state = 'awaiting'

        return payments
