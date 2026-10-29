# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class BdStockTransferRejectWizard(models.TransientModel):
    _name = 'bd.stock.transfer.reject.wizard'
    _description = 'Reject Transfer Request Wizard'

    request_id = fields.Many2one(
        'bd.stock.transfer.request',
        string='Transfer Request',
        required=True,
    )
    rejection_reason = fields.Text(
        string='Reason for Rejection',
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        if not (self.env.user.has_group('bd_stock_transfer_approval.group_bd_inventory_approver') or
                self.env.user.has_group('bd_stock_transfer_approval.group_bd_inventory_manager')):
            raise UserError(_("Only authorized Approvers or Managers can reject requests."))

        self.request_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

        self.request_id.message_post(
            body=_("Transfer request was rejected by <b>%s</b>.<br/><b>Reason:</b> %s",
                   self.env.user.name, self.rejection_reason),
            subject=_("Transfer Request Rejected"),
        )
        return {'type': 'ir.actions.act_window_close'}
