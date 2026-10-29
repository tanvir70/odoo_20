# -*- coding: utf-8 -*-

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        # Real-time stock evaluation triggered immediately upon completing moves
        try:
            storable_moves = self.filtered(lambda m: m.product_id.is_storable)
            if storable_moves:
                prod_ids = list(set(storable_moves.mapped('product_id').ids))
                wh_ids = set()
                for m in storable_moves:
                    if m.location_id.warehouse_id:
                        wh_ids.add(m.location_id.warehouse_id.id)
                    if m.location_dest_id.warehouse_id:
                        wh_ids.add(m.location_dest_id.warehouse_id.id)
                self.env['bd.stock.low.alert'].sudo().run_stock_evaluation(
                    product_ids=prod_ids,
                    warehouse_ids=list(wh_ids) if wh_ids else None,
                )
        except Exception:
            pass  # Ensure core inventory movement is never blocked
        return res
