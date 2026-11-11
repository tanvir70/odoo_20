# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mushak_hs_code = fields.Char(
        string='HS Code',
        size=12,
        help='Statutory Harmonized System (HS) code printed on Mushak 6.3 and registers.',
    )
    mushak_vds_service_code_id = fields.Many2one(
        comodel_name='mushak.vds.rule',
        string='VDS Service Code',
        domain="[('applies_to', '=', 'service')]",
        help='Statutory VDS service code under SRO 182 / VDS Guidelines.',
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    mushak_hs_code = fields.Char(
        related='product_tmpl_id.mushak_hs_code',
        readonly=False,
    )
    mushak_vds_service_code_id = fields.Many2one(
        related='product_tmpl_id.mushak_vds_service_code_id',
        readonly=False,
    )
