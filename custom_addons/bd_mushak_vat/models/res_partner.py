# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mushak_bin = fields.Char(
        string='BIN',
        size=13,
        index=True,
        copy=False,
        help='13-digit Business Identification Number (VAT Registration Number).',
    )
    mushak_is_vds_entity = fields.Boolean(
        string='VAT Withholding Entity',
        default=False,
        help='Check if this entity is legally mandated to deduct VAT at source (VDS).',
    )
    mushak_vds_entity_type = fields.Selection(
        selection=[
            ('government', 'Government Body'),
            ('semi_government', 'Semi-Government Body'),
            ('autonomous', 'Autonomous Body'),
            ('ngo', 'NGO'),
            ('bank', 'Bank'),
            ('insurance', 'Insurance Company'),
            ('education', 'Educational Institution'),
            ('limited_company', 'Limited Company'),
            ('other', 'Other'),
        ],
        string='Withholding Entity Type',
        help='Entity category under the VAT and Supplementary Duty Act.',
    )
    mushak_supplier_type = fields.Selection(
        selection=[
            ('manufacturer', 'Manufacturer'),
            ('trader', 'Trader'),
            ('service_provider', 'Service Provider'),
            ('importer', 'Importer'),
        ],
        string='Supplier Type',
        help='Supplier classification driving VDS rule rates.',
    )
    mushak_bin_duplicate_warning = fields.Char(
        string='BIN Duplicate Warning',
        compute='_compute_mushak_bin_duplicate_warning',
    )

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ['mushak_bin', 'mushak_is_vds_entity']

    @api.model
    def _synced_commercial_fields(self):
        return super()._synced_commercial_fields() + ['mushak_bin', 'mushak_is_vds_entity']

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('mushak_bin'):
                vals['mushak_bin'] = re.sub(r'\D', '', str(vals['mushak_bin']))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('mushak_bin'):
            vals['mushak_bin'] = re.sub(r'\D', '', str(vals['mushak_bin']))
        return super().write(vals)

    @api.constrains('mushak_bin')
    def _check_mushak_bin(self):
        for partner in self:
            if partner.mushak_bin and not re.match(r'^\d{13}$', partner.mushak_bin):
                raise ValidationError(
                    _("A BIN must have exactly 13 digits. Old 9- or 11-digit numbers from before the e-BIN migration are no longer valid.")
                )

    @api.constrains('mushak_is_vds_entity', 'mushak_vds_entity_type')
    def _check_mushak_vds_entity_type(self):
        for partner in self:
            if partner.mushak_is_vds_entity and not partner.mushak_vds_entity_type:
                raise ValidationError(
                    _("Please select the Withholding Entity Type when VAT Withholding Entity is enabled.")
                )

    @api.depends('mushak_bin')
    def _compute_mushak_bin_duplicate_warning(self):
        for partner in self:
            if partner.mushak_bin:
                domain = [
                    ('mushak_bin', '=', partner.mushak_bin),
                    ('id', '!=', partner._origin.id if partner._origin else partner.id),
                ]
                duplicate_count = self.search_count(domain)
                if duplicate_count > 0:
                    partner.mushak_bin_duplicate_warning = _(
                        "Note: This BIN (%s) is shared by %d other partner record(s). Verify if this is an authorized branch or sister concern.",
                        partner.mushak_bin, duplicate_count
                    )
                else:
                    partner.mushak_bin_duplicate_warning = False
            else:
                partner.mushak_bin_duplicate_warning = False

    def _mushak_format_bin(self):
        """Format 13-digit BIN for report display."""
        self.ensure_one()
        return self.mushak_bin or ''
