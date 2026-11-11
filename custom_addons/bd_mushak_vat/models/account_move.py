# -*- coding: utf-8 -*-
import secrets
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    mushak_form = fields.Selection(
        selection=[
            ('6.3', 'Mushak 6.3 (Tax Invoice)'),
            ('6.7', 'Mushak 6.7 (Credit Note)'),
            ('6.8', 'Mushak 6.8 (Debit Note)'),
            ('none', 'None'),
        ],
        string='Mushak Document Type',
        compute='_compute_mushak_form',
        store=True,
        index=True,
        help='Statutory Bangladesh VAT document type under VAT & SD Act 2012.',
    )
    mushak_number = fields.Char(
        string='Mushak Challan Number',
        readonly=True,
        copy=False,
        index=True,
        help='Official fiscal year sequence number for Mushak 6.3 / 6.7 / 6.8.',
    )
    mushak_issue_datetime = fields.Datetime(
        string='Time of Issue',
        copy=False,
        help='Timestamp of document issuance (Asia/Dhaka timezone).',
    )
    mushak_vehicle_type = fields.Char(
        string='Nature of Vehicle',
        help='e.g., Covered Van, Truck, Pickup, Barge, Courier.',
    )
    mushak_vehicle_number = fields.Char(
        string='Vehicle Number',
        help='Vehicle registration number (e.g., Dhaka Metro-Ta 11-2345).',
    )
    mushak_delivery_address = fields.Text(
        string='Final Destination of Supply',
        compute='_compute_mushak_delivery_address',
        store=True,
        readonly=False,
        help='Delivery location where goods or services are received.',
    )
    mushak_signatory_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible Signatory',
        default=lambda self: self.env.company.mushak_signatory_id,
        help='Authorized officer issuing and signing this Mushak document.',
    )
    mushak_adjustment_reason = fields.Text(
        string='Adjustment Reason',
        help='Mandatory justification for Credit Note (6.7) or Debit Note (6.8).',
    )
    mushak_origin_number = fields.Char(
        string='Original 6.3 Challan No',
        compute='_compute_mushak_origin',
        store=True,
        readonly=False,
        help='Original Mushak 6.3 tax invoice number referenced by this 6.7 or 6.8.',
    )
    mushak_origin_date = fields.Date(
        string='Original 6.3 Challan Date',
        compute='_compute_mushak_origin',
        store=True,
        readonly=False,
        help='Date of original Mushak 6.3 tax invoice.',
    )
    mushak_supplier_challan_number = fields.Char(
        string='Supplier Mushak Challan No',
        copy=False,
        help='Vendor Mushak 6.3, 6.7, or 6.8 number for input VAT claim (Mushak 6.1).',
    )
    mushak_supplier_challan_date = fields.Date(
        string='Supplier Mushak Challan Date',
        copy=False,
        help='Date of supplier statutory Mushak challan.',
    )
    mushak_access_token = fields.Char(
        string='Verification Token',
        copy=False,
        index=True,
        readonly=True,
        help='Cryptographic URL-safe token for public QR code verification.',
    )
    mushak_fiscal_year_label = fields.Char(
        string='Fiscal Year',
        compute='_compute_mushak_fiscal_year_label',
        help='Bangladesh fiscal year label (e.g. 2026-27).',
    )

    @api.depends('journal_id', 'move_type', 'debit_origin_id', 'company_id.mushak_journal_ids')
    def _compute_mushak_form(self):
        for move in self:
            journals = move.company_id.mushak_journal_ids
            # If specific journals are selected, restrict to them; if none configured, enable for sale journals
            if journals and move.journal_id not in journals:
                move.mushak_form = 'none'
            elif move.move_type == 'out_invoice':
                move.mushak_form = '6.8' if move.debit_origin_id else '6.3'
            elif move.move_type == 'out_refund':
                move.mushak_form = '6.7'
            else:
                move.mushak_form = 'none'

    @api.depends('partner_shipping_id', 'partner_id')
    def _compute_mushak_delivery_address(self):
        for move in self:
            if not move.mushak_delivery_address:
                partner = move.partner_shipping_id or move.partner_id
                if partner:
                    move.mushak_delivery_address = partner._display_address()
                else:
                    move.mushak_delivery_address = False

    @api.depends('reversed_entry_id', 'debit_origin_id')
    def _compute_mushak_origin(self):
        for move in self:
            origin_move = move.reversed_entry_id or move.debit_origin_id
            if origin_move and not move.mushak_origin_number:
                move.mushak_origin_number = origin_move.mushak_number or origin_move.name
                move.mushak_origin_date = origin_move.invoice_date
            elif not move.mushak_origin_number:
                move.mushak_origin_number = False
                move.mushak_origin_date = False

    @api.depends('mushak_number', 'invoice_date')
    def _compute_mushak_fiscal_year_label(self):
        for move in self:
            d = move.invoice_date or fields.Date.today()
            if d.month >= 7:
                move.mushak_fiscal_year_label = f"{d.year}-{str(d.year + 1)[-2:]}"
            else:
                move.mushak_fiscal_year_label = f"{d.year - 1}-{str(d.year)[-2:]}"

    def _get_mushak_sequence(self, code):
        """Retrieve or create company-isolated sequence for Mushak documents."""
        self.ensure_one()
        Seq = self.env['ir.sequence'].sudo()
        company = self.company_id
        seq = Seq.search([('code', '=', code), ('company_id', '=', company.id)], limit=1)
        if not seq:
            template = Seq.search([('code', '=', code), ('company_id', '=', False)], limit=1)
            if template:
                seq = template.copy({'company_id': company.id})
            else:
                seq = Seq.create({
                    'name': f"{code.upper()} for {company.name}",
                    'code': code,
                    'prefix': '%(range_year)s-',
                    'padding': 6,
                    'use_date_range': True,
                    'implementation': 'no_gap',
                    'mushak_fiscal_july': True,
                    'company_id': company.id,
                })
        return seq

    def _post(self, soft=True):
        # Validation before post
        for move in self:
            if move.mushak_form in ('6.3', '6.7', '6.8'):
                if not move.company_id.mushak_bin:
                    raise UserError(
                        _("Company BIN is required before posting statutory Mushak documents for company %s. "
                          "Please configure the BIN in Settings or Company details.") % move.company_id.display_name
                    )
                if move.mushak_form in ('6.7', '6.8'):
                    if not move.mushak_origin_number:
                        raise UserError(
                            _("A Mushak %s document must reference the original Mushak 6.3 Tax Invoice number.") % move.mushak_form
                        )
                    if not move.mushak_adjustment_reason:
                        raise UserError(
                            _("An adjustment reason is mandatory when issuing Mushak %s.") % move.mushak_form
                        )

        res = super()._post(soft=soft)

        # Assign gapless numbering ordered by invoice_date and ID
        mushak_moves = self.filtered(lambda m: m.mushak_form in ('6.3', '6.7', '6.8') and not m.mushak_number)
        sorted_moves = mushak_moves.sorted(key=lambda m: (m.invoice_date or fields.Date.today(), m.id))

        for move in sorted_moves:
            seq_code = f"mushak.{move.mushak_form.replace('.', '')}"
            sequence = move._get_mushak_sequence(seq_code)
            seq_date = move.invoice_date or fields.Date.today()
            move.mushak_number = sequence.next_by_id(sequence_date=seq_date)
            if not move.mushak_issue_datetime:
                move.mushak_issue_datetime = fields.Datetime.now()
            if not move.mushak_access_token:
                move.mushak_access_token = secrets.token_urlsafe(32)

        return res

    def button_draft(self):
        for move in self:
            if move.mushak_number:
                move.message_post(
                    body=_("Statutory Mushak %s (Challan No: %s) was reset to draft. The assigned Mushak number will be retained upon re-posting.")
                    % (move.mushak_form, move.mushak_number)
                )
        return super().button_draft()

    def write(self, vals):
        if 'invoice_date' in vals:
            for move in self:
                if move.mushak_number and move.invoice_date:
                    old_date = move.invoice_date
                    new_date = fields.Date.from_string(vals['invoice_date'])
                    old_fy = old_date.year if old_date.month >= 7 else old_date.year - 1
                    new_fy = new_date.year if new_date.month >= 7 else new_date.year - 1
                    if old_fy != new_fy:
                        raise ValidationError(
                            _("Cannot change the invoice date of an assigned Mushak challan (%s) across fiscal years (%d vs %d).")
                            % (move.mushak_number, old_fy, new_fy)
                        )
        return super().write(vals)

    def unlink(self):
        for move in self:
            if move.mushak_number:
                raise UserError(
                    _("Statutory Mushak documents (Challan %s) cannot be deleted under Bangladesh VAT regulations. "
                      "If the invoice was made in error, cancel it instead so the audit trail remains continuous.")
                    % move.mushak_number
                )
        return super().unlink()

    def get_mushak_verification_url(self):
        """Build public verification URL encoded in QR."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        return f"{base_url.rstrip('/')}/mushak/verify/{self.mushak_access_token or ''}"

    def get_mushak_amount_words_en(self, amount):
        """Return South Asian English amount in words."""
        return self.env['mushak.amount.words'].to_english(amount)

    def get_mushak_amount_words_bn(self, amount):
        """Return Bengali amount in words."""
        return self.env['mushak.amount.words'].to_bangla(amount)

    def format_mushak_num(self, val):
        """Format number respecting company Bangla numeral configuration."""
        self.ensure_one()
        if val is None or val is False:
            return ''
        formatted = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
        if self.company_id.mushak_show_bangla_digits:
            return self.env['mushak.amount.words'].to_bn_digits(formatted)
        return formatted

    def action_regenerate_mushak_token(self):
        """Action for Mushak Manager to rotate verification token if compromised."""
        self.ensure_one()
        self.check_access('write')
        if not self.env.user.has_group('bd_mushak_vat.group_mushak_manager'):
            raise UserError(_("Only Mushak Managers can regenerate verification tokens."))
        old_token = self.mushak_access_token
        self.mushak_access_token = secrets.token_urlsafe(32)
        self.message_post(
            body=_("Mushak verification token was regenerated by %s. Previous token (%s...) has been invalidated.")
            % (self.env.user.name, (old_token[:8] if old_token else 'none'))
        )
