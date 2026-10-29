# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BdStockLowAlert(models.Model):
    _name = 'bd.stock.low.alert'
    _description = 'Low Stock Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity desc, detected_at desc, id desc'

    name = fields.Char(
        string='Alert Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        tracking=True,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        tracking=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Stock Location',
        required=True,
        tracking=True,
    )
    orderpoint_id = fields.Many2one(
        'stock.warehouse.orderpoint',
        string='Reordering Rule',
    )
    uom_id = fields.Many2one(
        related='product_id.uom_id',
        string='Unit of Measure',
        readonly=True,
    )
    on_hand_qty = fields.Float(
        string='On-Hand Qty',
        readonly=True,
        tracking=True,
    )
    forecast_qty = fields.Float(
        string='Forecasted Qty',
        readonly=True,
        tracking=True,
    )
    min_qty = fields.Float(
        string='Minimum Threshold',
        readonly=True,
        tracking=True,
    )
    max_qty = fields.Float(
        string='Target Level',
        readonly=True,
    )
    suggested_qty = fields.Float(
        string='Suggested Replenishment',
        readonly=True,
    )
    severity = fields.Selection(
        [
            ('low_stock', 'Low Stock'),
            ('critical_low', 'Critical Low (< 50%)'),
            ('out_of_stock', 'Out of Stock (<= 0)'),
        ],
        string='Shortage Severity',
        default='low_stock',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ('active', 'Active Alert'),
            ('acknowledged', 'Acknowledged'),
            ('resolved', 'Resolved'),
        ],
        string='Alert Status',
        default='active',
        required=True,
        tracking=True,
    )
    detected_at = fields.Datetime(
        string='Detected Date',
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
    )
    last_checked_at = fields.Datetime(
        string='Last Checked Date',
        default=fields.Datetime.now,
        readonly=True,
    )
    acknowledged_by = fields.Many2one(
        'res.users',
        string='Acknowledged By',
        readonly=True,
        copy=False,
    )
    acknowledged_at = fields.Datetime(
        string='Acknowledged Date',
        readonly=True,
        copy=False,
    )
    resolved_at = fields.Datetime(
        string='Resolution Date',
        readonly=True,
        copy=False,
    )
    transfer_request_id = fields.Many2one(
        'bd.stock.transfer.request',
        string='Linked Transfer Requisition',
        copy=False,
    )

    def action_acknowledge(self):
        for alert in self:
            alert.write({
                'state': 'acknowledged',
                'acknowledged_by': self.env.user.id,
                'acknowledged_at': fields.Datetime.now(),
            })
            alert.message_post(body=_("Alert acknowledged by %s.", self.env.user.name))

    def action_resolve(self):
        for alert in self:
            alert.write({
                'state': 'resolved',
                'resolved_at': fields.Datetime.now(),
            })
            alert.message_post(body=_("Alert marked as resolved by %s.", self.env.user.name))

    def action_request_transfer(self):
        self.ensure_one()
        # Find potential source warehouse in the same company
        source_wh = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id),
            ('id', '!=', self.warehouse_id.id),
        ], limit=1)

        ctx = {
            'default_company_id': self.company_id.id,
            'default_destination_warehouse_id': self.warehouse_id.id,
            'default_destination_location_id': self.location_id.id,
            'default_transfer_reason': _("Replenishment Requisition for Low Stock Alert: %s (%s)", self.name, self.product_id.display_name),
            'default_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'requested_qty': self.suggested_qty or 10.0,
            })],
        }
        if source_wh:
            ctx['default_source_warehouse_id'] = source_wh.id
            ctx['default_source_location_id'] = source_wh.lot_stock_id.id

        return {
            'name': _('Create Transfer Requisition'),
            'type': 'ir.actions.act_window',
            'res_model': 'bd.stock.transfer.request',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }

    @api.model
    def run_stock_evaluation(self, company_id=None, product_ids=None, warehouse_ids=None):
        """Scans inventory levels across warehouses and manages alerts."""
        companies = self.env['res.company'].browse(company_id) if company_id else self.env['res.company'].search([])
        alerts_created = 0
        alerts_updated = 0
        alerts_resolved = 0

        for company in companies:
            wh_domain = [('company_id', '=', company.id)]
            if warehouse_ids:
                wh_domain.append(('id', 'in', warehouse_ids))
            warehouses = self.env['stock.warehouse'].search(wh_domain)

            prod_domain = [
                ('is_storable', '=', True),
                '|', ('company_id', '=', False), ('company_id', '=', company.id),
            ]
            if product_ids:
                prod_domain.append(('id', 'in', product_ids))
            storable_products = self.env['product.product'].search(prod_domain)

            for wh in warehouses:
                loc = wh.lot_stock_id
                if not loc:
                    continue

                for prod in storable_products:
                    # Determine threshold: Orderpoint first, else product setting, else 10.0
                    op = self.env['stock.warehouse.orderpoint'].search([
                        ('product_id', '=', prod.id),
                        ('warehouse_id', '=', wh.id),
                    ], limit=1)

                    if op:
                        min_q = op.product_min_qty
                        max_q = op.product_max_qty
                    else:
                        min_q = prod.low_stock_threshold or 10.0
                        max_q = prod.low_stock_target or 50.0

                    # Compute on-hand quantity at this warehouse location
                    quants = self.env['stock.quant'].search([
                        ('product_id', '=', prod.id),
                        ('location_id', '=', loc.id),
                    ])
                    on_hand = sum(quants.mapped('quantity'))

                    # Compute forecasted quantity
                    prod_ctx = prod.with_context(location=loc.id)
                    forecast = prod_ctx.virtual_available

                    existing_alert = self.search([
                        ('company_id', '=', company.id),
                        ('product_id', '=', prod.id),
                        ('warehouse_id', '=', wh.id),
                        ('state', 'in', ('active', 'acknowledged')),
                    ], limit=1)

                    if on_hand < min_q:
                        # Determine severity
                        if on_hand <= 0:
                            sev = 'out_of_stock'
                        elif on_hand <= (min_q * 0.5):
                            sev = 'critical_low'
                        else:
                            sev = 'low_stock'

                        suggested = max(max_q - on_hand, min_q - on_hand, 1.0)

                        if existing_alert:
                            existing_alert.write({
                                'on_hand_qty': on_hand,
                                'forecast_qty': forecast,
                                'min_qty': min_q,
                                'max_qty': max_q,
                                'suggested_qty': suggested,
                                'severity': sev,
                                'last_checked_at': fields.Datetime.now(),
                            })
                            alerts_updated += 1
                        else:
                            seq = self.env['ir.sequence'].next_by_code('bd.stock.low.alert') or _('New')
                            new_alert = self.create({
                                'name': seq,
                                'company_id': company.id,
                                'product_id': prod.id,
                                'warehouse_id': wh.id,
                                'location_id': loc.id,
                                'orderpoint_id': op.id if op else False,
                                'on_hand_qty': on_hand,
                                'forecast_qty': forecast,
                                'min_qty': min_q,
                                'max_qty': max_q,
                                'suggested_qty': suggested,
                                'severity': sev,
                                'state': 'active',
                                'detected_at': fields.Datetime.now(),
                                'last_checked_at': fields.Datetime.now(),
                            })
                            alerts_created += 1

                            # Post notification in chatter
                            new_alert.message_post(
                                body=_("Low Stock Alert generated. Current on-hand quantity (%s %s) is below threshold (%s %s). Suggested replenishment: %s %s.",
                                       on_hand, prod.uom_id.name, min_q, prod.uom_id.name, suggested, prod.uom_id.name),
                                subject=_("Low Stock Detected - %s", prod.display_name),
                            )
                    else:
                        # If quantity has restored, resolve active alert
                        if existing_alert:
                            existing_alert.write({
                                'state': 'resolved',
                                'resolved_at': fields.Datetime.now(),
                                'on_hand_qty': on_hand,
                                'forecast_qty': forecast,
                                'last_checked_at': fields.Datetime.now(),
                            })
                            existing_alert.message_post(
                                body=_("Stock level recovered to %s %s (threshold: %s). Alert automatically resolved.",
                                       on_hand, prod.uom_id.name, min_q),
                                subject=_("Alert Auto-Resolved"),
                            )
                            alerts_resolved += 1

        return {
            'created': alerts_created,
            'updated': alerts_updated,
            'resolved': alerts_resolved,
        }

    def action_check_now_button(self):
        """Manual trigger button for users to evaluate stock on demand."""
        res = self.run_stock_evaluation(company_id=self.env.company.id)
        msg = _("Stock evaluation completed. Alerts Created: %s, Updated: %s, Auto-Resolved: %s.",
                res['created'], res['updated'], res['resolved'])
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Low Stock Evaluation Complete'),
                'message': msg,
                'sticky': False,
                'type': 'info',
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }
