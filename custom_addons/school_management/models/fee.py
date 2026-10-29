# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SchoolFee(models.Model):
    _name = 'school.fee'
    _description = 'Student Fee Record'
    _order = 'due_date desc, id desc'

    name = fields.Char(
        string='Receipt / Invoice No',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    student_id = fields.Many2one(
        'school.student',
        string='Student',
        required=True,
        ondelete='cascade',
    )
    classroom_id = fields.Many2one(
        related='student_id.classroom_id',
        string='Classroom / Grade',
        store=True,
        readonly=True,
    )
    fee_type = fields.Selection(
        [
            ('tuition', 'Tuition Fee'),
            ('admission', 'Admission Fee'),
            ('exam', 'Examination Fee'),
            ('library', 'Library Fee'),
            ('transport', 'Transportation Fee'),
            ('hostel', 'Hostel Fee'),
            ('other', 'Other Fee'),
        ],
        string='Fee Type',
        default='tuition',
        required=True,
    )
    amount = fields.Float(string='Fee Amount', required=True, default=0.0)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    due_date = fields.Date(string='Due Date', default=fields.Date.today, required=True)
    paid_date = fields.Date(string='Payment Date')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pending', 'Pending Payment'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
        ],
        string='Payment Status',
        default='draft',
        required=True,
    )
    payment_method = fields.Selection(
        [
            ('cash', 'Cash'),
            ('bank', 'Bank Transfer'),
            ('online', 'Online Payment'),
            ('cheque', 'Cheque'),
        ],
        string='Payment Method',
        default='cash',
    )
    reference = fields.Char(string='Payment / Transaction Ref')
    notes = fields.Text(string='Notes / Remarks')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('school.fee') or _('New')
                )
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'pending'})

    def action_pay(self):
        self.write({
            'state': 'paid',
            'paid_date': fields.Date.today(),
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset(self):
        self.write({'state': 'draft'})
