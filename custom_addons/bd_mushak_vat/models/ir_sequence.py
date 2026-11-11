# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    mushak_fiscal_july = fields.Boolean(
        string='Bangladesh Fiscal Year (July-June)',
        default=False,
        help='If checked, date ranges reset annually on 1 July rather than 1 January.',
    )

    def _create_date_range_seq(self, date):
        self.ensure_one()
        if not self.mushak_fiscal_july:
            return super()._create_date_range_seq(date)

        d = fields.Date.from_string(date)
        if d.month >= 7:
            fiscal_start = d.year
            fiscal_end = d.year + 1
        else:
            fiscal_start = d.year - 1
            fiscal_end = d.year

        date_from = f"{fiscal_start}-07-01"
        date_to = f"{fiscal_end}-06-30"

        # Clip date_to if an overlapping range exists ahead
        date_range = self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', self.id), ('date_from', '>=', date), ('date_from', '<=', date_to)],
            order='date_from desc',
            limit=1
        )
        if date_range:
            date_to = (date_range.date_from + timedelta(days=-1)).strftime('%Y-%m-%d')

        # Clip date_from if an overlapping range exists behind
        date_range = self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', self.id), ('date_to', '>=', date_from), ('date_to', '<=', date)],
            order='date_to desc',
            limit=1
        )
        if date_range:
            date_from = (date_range.date_to + timedelta(days=1)).strftime('%Y-%m-%d')

        seq_date_range = self.env['ir.sequence.date_range'].sudo().create({
            'date_from': date_from,
            'date_to': date_to,
            'sequence_id': self.id,
            'number_next': 1,
        })
        return seq_date_range
