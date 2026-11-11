# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MushakVdsRule(models.Model):
    _name = 'mushak.vds.rule'
    _description = 'Statutory VDS Withholding Rule'
    _order = 'code asc, date_from desc, id desc'

    name = fields.Char(string='Service / Supply Name', required=True)
    code = fields.Char(string='Code', required=True, index=True, help='Statutory service code (e.g. S004.00) or goods rule code.')
    applies_to = fields.Selection([
        ('service', 'Service'),
        ('goods', 'Goods'),
    ], string='Applies To', required=True, default='service')
    supplier_type = fields.Selection([
        ('manufacturer', 'Manufacturer'),
        ('trader', 'Trader'),
        ('service_provider', 'Service Provider'),
        ('importer', 'Importer'),
    ], string='Supplier Classification', help='Supplier type matching rule for goods.')
    invoice_vat_rate = fields.Float(
        string='Invoice VAT Rate (%)',
        help='Applicable if withholding rate depends on the rate billed by supplier (e.g. 7.5%).',
    )
    vds_rate = fields.Float(
        string='VDS Withholding Rate (%)',
        required=True,
        help='Percentage of value to be withheld at source.',
    )
    date_from = fields.Date(
        string='Effective From',
        default=fields.Date.context_today,
        required=True,
        help='Start date of this statutory rate rule.',
    )
    date_to = fields.Date(
        string='Effective To',
        help='End date after which this rate is expired or replaced.',
    )
    legal_reference = fields.Char(
        string='Legal Reference',
        default='SRO 182-Ain/2025/310-Mushak',
        help='SRO or statutory order reference prescribing this rate.',
    )
    exempt = fields.Boolean(
        string='Exempt from VDS',
        default=False,
        help='Check if supplies under this rule are explicitly exempted from VDS.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Optional company scope. If empty, rule applies across all companies.',
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        result = []
        for rule in self:
            rate_str = f"Exempt" if rule.exempt else f"{rule.vds_rate}%"
            name = f"[{rule.code}] {rule.name} ({rate_str})"
            result.append((rule.id, name))
        return result

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rule in self:
            if rule.date_to and rule.date_from and rule.date_to < rule.date_from:
                raise ValidationError(_("Effective To date cannot be earlier than Effective From date."))

    @api.model
    def match_rule(self, service_code_id=None, supplier_type=None, invoice_vat_rate=0.0, payment_date=None, company_id=None):
        """Match statutory VDS rule based on product service code or supplier type + VAT rate."""
        d = payment_date or fields.Date.today()
        base_domain = [
            ('active', '=', True),
            ('date_from', '<=', d),
            '|', ('date_to', '=', False), ('date_to', '>=', d),
            '|', ('company_id', '=', False), ('company_id', '=', company_id or self.env.company.id),
        ]

        # 1. Direct service code match if provided on product
        if service_code_id:
            rule = self.browse(service_code_id)
            if rule.exists() and rule.active:
                if rule.date_from <= d and (not rule.date_to or rule.date_to >= d):
                    return rule

        # 2. Goods rule matching supplier type
        if supplier_type:
            domain = base_domain + [
                ('applies_to', '=', 'goods'),
                ('supplier_type', '=', supplier_type),
            ]
            if invoice_vat_rate:
                domain_with_rate = domain + [('invoice_vat_rate', '=', invoice_vat_rate)]
                matched = self.search(domain_with_rate, limit=1)
                if matched:
                    return matched
            matched = self.search(domain, limit=1)
            if matched:
                return matched

        return self.browse()
