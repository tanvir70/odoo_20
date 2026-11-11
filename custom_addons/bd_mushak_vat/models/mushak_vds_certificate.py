# -*- coding: utf-8 -*-
import secrets
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MushakVdsCertificate(models.Model):
    _name = 'mushak.vds.certificate'
    _description = 'Mushak 6.6 VAT Deduction at Source (VDS) Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Certificate Number',
        readonly=True,
        copy=False,
        index=True,
        help='Official Mushak 6.6 certificate number (July-June FY sequence).',
    )
    direction = fields.Selection([
        ('issued', 'Issued by Us (We Withheld VAT)'),
        ('received', 'Received from Customer (Customer Withheld VAT)'),
    ], string='Direction', required=True, default='issued', tracking=True)
    date = fields.Date(
        string='Certificate Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier / Withholder',
        required=True,
        tracking=True,
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Linked Payment Entry',
        ondelete='restrict',
        copy=False,
    )
    line_ids = fields.One2many(
        comodel_name='mushak.vds.certificate.line',
        inverse_name='certificate_id',
        string='Deduction Lines',
        copy=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    amount_total = fields.Monetary(
        string='Total VDS Deducted',
        compute='_compute_amount_total',
        store=True,
        currency_field='currency_id',
        tracking=True,
    )
    deposit_method = fields.Selection([
        ('return_adjustment', 'Increasing Adjustment in Return (রিটার্নে সমন্বয়)'),
        ('treasury_challan', 'Treasury Challan (ট্রেজারি চালান)'),
        ('e_payment', 'E-Payment (ই-পেমেন্ট)'),
    ], string='Deposit Method', default='return_adjustment', tracking=True)
    deposit_reference = fields.Char(
        string='Deposit Reference / Challan No',
        help='Treasury Challan number, e-payment trace, or return period (e.g. 2026-08).',
    )
    tax_period = fields.Char(
        string='Tax Period',
        help='Tax period month (e.g. 2026-08).',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('awaiting', 'Awaiting Certificate from Customer'),
        ('received', 'Certificate Received'),
        ('adjusted', 'Adjusted in VAT Return'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    issue_deadline = fields.Date(
        string='Issue Deadline',
        compute='_compute_deadlines',
        store=True,
        help='Statutory deadline (3 working days after return submission / deposit).',
    )
    adjustment_deadline = fields.Date(
        string='Adjustment Expiry Date',
        compute='_compute_deadlines',
        store=True,
        help='Statutory window: end of 6th tax period after payment period.',
    )
    signatory_id = fields.Many2one(
        comodel_name='res.users',
        string='Authorized Signatory',
        default=lambda self: self.env.company.mushak_signatory_id,
    )
    mushak_access_token = fields.Char(
        string='Verification Token',
        copy=False,
        index=True,
        readonly=True,
    )

    @api.depends('line_ids.vds_amount')
    def _compute_amount_total(self):
        for cert in self:
            cert.amount_total = sum(cert.line_ids.mapped('vds_amount'))

    @api.depends('date', 'direction')
    def _compute_deadlines(self):
        for cert in self:
            if cert.date:
                # 3 working days approx. 5 calendar days
                cert.issue_deadline = cert.date + timedelta(days=5)
                # 6 tax periods (6 months)
                cert.adjustment_deadline = (cert.date + relativedelta(months=7)).replace(day=1) - timedelta(days=1)
            else:
                cert.issue_deadline = False
                cert.adjustment_deadline = False

    def action_issue(self):
        """Issue statutory Mushak 6.6 certificate and assign fiscal year sequence."""
        for cert in self:
            if cert.direction == 'issued' and not cert.name:
                seq = self.env['account.move']._get_mushak_sequence('mushak.66', company=cert.company_id)
                cert.name = seq.next_by_id(sequence_date=cert.date or fields.Date.today())
            if not cert.mushak_access_token:
                cert.mushak_access_token = secrets.token_urlsafe(32)
            cert.state = 'issued'
            cert.message_post(body=_("Mushak 6.6 Certificate %s has been officially issued.") % (cert.name or ''))

    def action_mark_received(self):
        self.ensure_one()
        if not self.name:
            raise UserError(_("Please enter the certificate number received from customer."))
        self.state = 'received'

    def action_mark_adjusted(self):
        self.ensure_one()
        self.state = 'adjusted'
        self.message_post(body=_("Decreasing adjustment claimed in monthly VAT return based on certificate %s.") % self.name)

    def action_cancel(self):
        for cert in self:
            if not self.env.user.has_group('bd_mushak_vat.group_mushak_manager'):
                raise UserError(_("Only Mushak Managers can cancel an issued Mushak 6.6 Certificate."))
            cert.state = 'cancel'
            cert.message_post(body=_("Mushak 6.6 Certificate was cancelled by %s.") % self.env.user.name)

    def unlink(self):
        for cert in self:
            if cert.state in ('issued', 'adjusted'):
                raise UserError(_("Statutory Mushak 6.6 Certificate (%s) cannot be deleted. Cancel it instead.") % (cert.name or ''))
        return super().unlink()

    def get_mushak_verification_url(self):
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        base_url = ICP.get_str('web.base.url', '') if hasattr(ICP, 'get_str') else (ICP.get_param('web.base.url') or '')
        return f"{base_url.rstrip('/')}/mushak/verify/{self.mushak_access_token or ''}"


class MushakVdsCertificateLine(models.Model):
    _name = 'mushak.vds.certificate.line'
    _description = 'Mushak 6.6 Certificate Item Line'

    certificate_id = fields.Many2one('mushak.vds.certificate', string='Certificate', required=True, ondelete='cascade')
    move_id = fields.Many2one('account.move', string='Invoice / Bill Reference')
    currency_id = fields.Many2one(related='certificate_id.currency_id')
    challan_number = fields.Char(string='Mushak 6.3 Challan No', help='Vendor or Customer 6.3 Tax Invoice number.')
    challan_date = fields.Date(string='Challan Date')
    value_excl_vat = fields.Monetary(string='Taxable Value', currency_field='currency_id')
    vat_amount = fields.Monetary(string='VAT on Invoice', currency_field='currency_id')
    vds_rate = fields.Float(string='VDS Rate (%)')
    vds_amount = fields.Monetary(string='VDS Deducted', currency_field='currency_id')
