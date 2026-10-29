# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SchoolAttendance(models.Model):
    _name = 'school.attendance'
    _description = 'Student Attendance'
    _order = 'date desc, student_id'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    student_id = fields.Many2one(
        'school.student',
        string='Student',
        required=True,
        ondelete='cascade',
    )
    classroom_id = fields.Many2one(
        'school.classroom',
        string='Classroom / Grade',
        required=True,
        ondelete='cascade',
    )
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    status = fields.Selection(
        [
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            ('excused', 'Excused'),
        ],
        string='Status',
        default='present',
        required=True,
    )
    remarks = fields.Char(string='Remarks / Reason')

    _sql_constraints = [
        (
            'unique_student_attendance_date',
            'unique(student_id, date)',
            'Attendance for this student on this date has already been recorded!',
        ),
    ]

    @api.depends('student_id.name', 'date', 'status')
    def _compute_name(self):
        for record in self:
            student_name = record.student_id.name or 'Unknown'
            record.name = f"{student_name} - {record.date or ''} ({record.status or ''})"

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id and self.student_id.classroom_id:
            self.classroom_id = self.student_id.classroom_id
