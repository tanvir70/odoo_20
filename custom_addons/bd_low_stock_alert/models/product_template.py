# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    low_stock_threshold = fields.Float(
        string='Low Stock Alert Threshold',
        default=10.0,
        help='Trigger an alert when on-hand stock in any warehouse drops below this limit.',
    )
    low_stock_target = fields.Float(
        string='Target Restock Level',
        default=50.0,
        help='Target quantity to replenish up to when an alert is raised.',
    )
    low_stock_alert_count = fields.Integer(
        string='Low Stock Alerts',
        compute='_compute_low_stock_alert_count',
    )

    def _compute_low_stock_alert_count(self):
        for tmpl in self:
            tmpl.low_stock_alert_count = self.env['bd.stock.low.alert'].search_count([
                ('product_id.product_tmpl_id', '=', tmpl.id),
                ('state', 'in', ('active', 'acknowledged')),
            ])

    def action_view_low_stock_alerts(self):
        self.ensure_one()
        return {
            'name': 'Low Stock Alerts',
            'type': 'ir.actions.act_window',
            'res_model': 'bd.stock.low.alert',
            'view_mode': 'list,form',
            'domain': [('product_id.product_tmpl_id', '=', self.id), ('state', 'in', ('active', 'acknowledged'))],
            'context': {'default_product_id': self.product_variant_id.id},
        }
