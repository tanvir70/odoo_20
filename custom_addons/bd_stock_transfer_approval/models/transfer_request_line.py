# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BdStockTransferRequestLine(models.Model):
    _name = 'bd.stock.transfer.request.line'
    _description = 'Stock Transfer Request Line'
    _order = 'id asc'

    request_id = fields.Many2one(
        'bd.stock.transfer.request',
        string='Transfer Request',
        required=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        related='request_id.company_id',
        string='Company',
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('is_storable', '=', True)]",
    )
    uom_id = fields.Many2one(
        related='product_id.uom_id',
        string='Unit of Measure',
        readonly=True,
    )
    requested_qty = fields.Float(
        string='Requested Qty',
        required=True,
        default=1.0,
    )
    source_available_qty = fields.Float(
        string='Source Available',
        compute='_compute_source_available_qty',
        help='Available quantity in the source location.',
    )
    notes = fields.Char(string='Notes / Spec')

    @api.depends('product_id', 'request_id.source_location_id')
    def _compute_source_available_qty(self):
        for line in self:
            if line.product_id and line.request_id.source_location_id:
                # Query stock.quant in source location
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.request_id.source_location_id.id),
                ])
                line.source_available_qty = sum(quants.mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            else:
                line.source_available_qty = 0.0

    @api.constrains('requested_qty')
    def _check_requested_qty(self):
        for line in self:
            if line.requested_qty <= 0:
                raise ValidationError(_("Requested quantity for product '%s' must be strictly positive.", line.product_id.display_name))
