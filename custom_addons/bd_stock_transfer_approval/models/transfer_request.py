# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BdStockTransferRequest(models.Model):
    _name = 'bd.stock.transfer.request'
    _description = 'Stock Transfer Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'requested_date desc, id desc'

    name = fields.Char(
        string='Request Reference',
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
    requester_id = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    requested_date = fields.Date(
        string='Requested Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    required_date = fields.Date(
        string='Required By Date',
        tracking=True,
    )
    source_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Source Warehouse',
        required=True,
        tracking=True,
        domain="[('company_id', '=', company_id)]",
    )
    destination_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Destination Warehouse',
        required=True,
        tracking=True,
        domain="[('company_id', '=', company_id)]",
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        required=True,
        tracking=True,
        domain="[('usage', '=', 'internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True,
        tracking=True,
        domain="[('usage', '=', 'internal'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    transfer_reason = fields.Text(
        string='Reason / Business Purpose',
        tracking=True,
    )
    priority = fields.Selection(
        [
            ('0', 'Normal'),
            ('1', 'Low'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        default='0',
        tracking=True,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('done', 'Transferred'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True,
        copy=False,
        tracking=True,
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Decided By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(
        string='Decision Date',
        readonly=True,
        copy=False,
        tracking=True,
    )
    line_ids = fields.One2many(
        'bd.stock.transfer.request.line',
        'request_id',
        string='Transfer Lines',
        copy=True,
    )
    total_qty = fields.Float(
        string='Total Requested Units',
        compute='_compute_total_qty',
        store=True,
    )
    picking_ids = fields.One2many(
        'stock.picking',
        'bd_transfer_request_id',
        string='Stock Transfers',
    )
    picking_count = fields.Integer(
        string='Transfer Count',
        compute='_compute_picking_count',
    )

    @api.depends('line_ids.requested_qty')
    def _compute_total_qty(self):
        for req in self:
            req.total_qty = sum(req.line_ids.mapped('requested_qty'))

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for req in self:
            req.picking_count = len(req.picking_ids)

    @api.onchange('source_warehouse_id')
    def _onchange_source_warehouse_id(self):
        if self.source_warehouse_id:
            self.source_location_id = self.source_warehouse_id.lot_stock_id

    @api.onchange('destination_warehouse_id')
    def _onchange_destination_warehouse_id(self):
        if self.destination_warehouse_id:
            self.destination_location_id = self.destination_warehouse_id.lot_stock_id

    @api.constrains('source_location_id', 'destination_location_id')
    def _check_locations(self):
        for req in self:
            if req.source_location_id and req.destination_location_id:
                if req.source_location_id == req.destination_location_id:
                    raise ValidationError(_("Source and destination locations cannot be the same!"))

    def action_submit(self):
        for req in self:
            if not req.line_ids:
                raise UserError(_("Please add at least one product line before submitting for approval."))
            if any(l.requested_qty <= 0 for l in req.line_ids):
                raise UserError(_("All requested quantities must be greater than zero."))
            if req.source_location_id == req.destination_location_id:
                raise UserError(_("Source location and Destination location cannot be identical."))

            if req.name == _('New') or not req.name:
                seq = self.env['ir.sequence'].next_by_code('bd.stock.transfer.request') or _('New')
                req.name = seq

            req.write({'state': 'submitted'})
            req.message_post(
                body=_("Transfer request submitted for supervisor/manager approval."),
                subject=_("Transfer Request Submitted"),
            )

    def action_approve(self):
        self.ensure_one()
        # Security check: must be Approver or Manager
        if not (self.env.user.has_group('bd_stock_transfer_approval.group_bd_inventory_approver') or
                self.env.user.has_group('bd_stock_transfer_approval.group_bd_inventory_manager')):
            raise UserError(_("Only authorized Approvers or Managers can approve stock transfer requests."))

        if not self.line_ids:
            raise UserError(_("Cannot approve a request with no product lines."))

        # Determine picking type for internal transfer
        picking_type = self.source_warehouse_id.int_type_id
        if not picking_type:
            # Fallback to any internal transfer operation type in this warehouse's company
            picking_type = self.env['stock.picking.type'].search([
                ('company_id', '=', self.company_id.id),
                ('code', '=', 'internal'),
            ], limit=1)

        if not picking_type:
            raise UserError(_("No Internal Transfer operation type found for warehouse %s.", self.source_warehouse_id.name))

        # Create native stock.picking
        moves = []
        for line in self.line_ids:
            moves.append((0, 0, {
                'description_picking': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.requested_qty,
                'uom_id': line.product_id.uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
                'company_id': self.company_id.id,
            }))

        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
            'bd_transfer_request_id': self.id,
            'move_ids': moves,
        }

        picking = self.env['stock.picking'].create(picking_vals)
        picking.action_confirm()

        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

        self.message_post(
            body=_("Transfer Request approved by %s. Native Stock Transfer %s has been created.",
                   self.env.user.name, picking.name),
            subject=_("Transfer Approved"),
        )

    def action_reject(self):
        self.ensure_one()
        # Security check: must be Approver or Manager
        if not (self.env.user.has_group('bd_stock_transfer_approval.group_bd_inventory_approver') or
                self.env.user.has_group('bd_stock_transfer_approval.group_bd_inventory_manager')):
            raise UserError(_("Only authorized Approvers or Managers can reject stock transfer requests."))

        return {
            'name': _('Reject Transfer Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'bd.stock.transfer.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def action_cancel(self):
        for req in self:
            if req.state == 'done':
                raise UserError(_("Cannot cancel an already completed transfer request."))
            req.write({'state': 'cancel'})
            req.message_post(body=_("Transfer request cancelled."))

    def action_reset_draft(self):
        for req in self:
            if req.state not in ('cancel', 'rejected'):
                raise UserError(_("Only cancelled or rejected requests can be reset to draft."))
            req.write({
                'state': 'draft',
                'rejection_reason': False,
                'approver_id': False,
                'approval_date': False,
            })
            req.message_post(body=_("Request reset to draft for revision."))

    def action_view_picking(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        if len(self.picking_ids) > 1:
            action['domain'] = [('id', 'in', self.picking_ids.ids)]
        elif len(self.picking_ids) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = self.picking_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
