# -*- coding: utf-8 -*-

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    bd_transfer_request_id = fields.Many2one(
        'bd.stock.transfer.request',
        string='Originating Transfer Request',
        readonly=True,
        copy=False,
        index=True,
    )

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if picking.bd_transfer_request_id:
                # If picking is completed, update transfer request state to done
                req = picking.bd_transfer_request_id
                if all(p.state == 'done' for p in req.picking_ids):
                    req.write({'state': 'done'})
                    req.message_post(
                        body="Stock transfer has been physically completed via Transfer %s." % picking.name
                    )
        return res
