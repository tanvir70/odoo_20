# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api, _


class SchoolStudent(models.Model):
    _name = 'school.student'
    _description = 'Student'
    _inherit = ['image.mixin']
    _order = 'name, id desc'

    name = fields.Char(string='Student Name', required=True)
    student_id = fields.Char(
        string='Student ID',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender',
        default='male',
    )
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    blood_group = fields.Selection(
        [
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
        ],
        string='Blood Group',
    )

    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    street = fields.Char(string='Street Address')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', string='Country')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    classroom_id = fields.Many2one(
        'school.classroom',
        string='Classroom / Grade',
        ondelete='restrict',
    )
    teacher_id = fields.Many2one(
        related='classroom_id.teacher_id',
        string='Class Teacher',
        readonly=True,
        store=True,
    )
    course_ids = fields.Many2many(
        'school.course',
        'school_student_course_rel',
        'student_id',
        'course_id',
        string='Enrolled Courses',
    )

    # Guardian Details
    guardian_name = fields.Char(string='Guardian Name')
    guardian_relation = fields.Selection(
        [
            ('father', 'Father'),
            ('mother', 'Mother'),
            ('guardian', 'Legal Guardian'),
            ('other', 'Other'),
        ],
        string='Relationship',
        default='father',
    )
    guardian_phone = fields.Char(string='Guardian Phone')
    guardian_email = fields.Char(string='Guardian Email')

    enrollment_date = fields.Date(string='Enrollment Date', default=fields.Date.today)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('enrolled', 'Enrolled'),
            ('graduated', 'Graduated'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
    )
    remarks = fields.Text(string='Notes / Remarks')

    # Attendance Relations & Stats
    attendance_ids = fields.One2many(
        'school.attendance',
        'student_id',
        string='Attendance Records',
    )
    attendance_count = fields.Integer(
        string='Total Attendance Days',
        compute='_compute_attendance_stats',
    )
    attendance_rate = fields.Float(
        string='Attendance Rate (%)',
        compute='_compute_attendance_stats',
    )

    # Exam Relations & Stats
    exam_result_ids = fields.One2many(
        'school.exam.result',
        'student_id',
        string='Exam Results',
    )
    exam_count = fields.Integer(
        string='Total Exams Taken',
        compute='_compute_exam_stats',
    )
    average_score = fields.Float(
        string='Average Score (%)',
        compute='_compute_exam_stats',
    )

    # Fee Relations & Stats
    fee_ids = fields.One2many(
        'school.fee',
        'student_id',
        string='Fee Records',
    )
    fee_count = fields.Integer(
        string='Total Invoices',
        compute='_compute_fee_stats',
    )
    unpaid_fee_amount = fields.Float(
        string='Outstanding Fees',
        compute='_compute_fee_stats',
    )

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.date_of_birth:
                record.age = (
                    today.year
                    - record.date_of_birth.year
                    - ((today.month, today.day) < (record.date_of_birth.month, record.date_of_birth.day))
                )
            else:
                record.age = 0

    def _compute_attendance_stats(self):
        for student in self:
            total = len(student.attendance_ids)
            present = len(student.attendance_ids.filtered(lambda a: a.status == 'present'))
            student.attendance_count = total
            student.attendance_rate = (present / total * 100.0) if total > 0 else 0.0

    def _compute_exam_stats(self):
        for student in self:
            results = student.exam_result_ids
            student.exam_count = len(results)
            if results:
                total_pct = sum(r.percentage for r in results)
                student.average_score = round(total_pct / len(results), 1)
            else:
                student.average_score = 0.0

    def _compute_fee_stats(self):
        for student in self:
            fees = student.fee_ids
            student.fee_count = len(fees)
            unpaid = fees.filtered(lambda f: f.state in ('draft', 'pending'))
            student.unpaid_fee_amount = sum(f.amount for f in unpaid)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('student_id', _('New')) == _('New'):
                vals['student_id'] = (
                    self.env['ir.sequence'].next_by_code('school.student') or _('New')
                )
        return super().create(vals_list)

    def action_enroll(self):
        self.write({'state': 'enrolled'})

    def action_graduate(self):
        self.write({'state': 'graduated'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # Smart Button Action Views
    def action_view_attendance(self):
        self.ensure_one()
        return {
            'name': f"Attendance - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'school.attendance',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id, 'default_classroom_id': self.classroom_id.id if self.classroom_id else False},
        }

    def action_view_exams(self):
        self.ensure_one()
        return {
            'name': f"Exam Results - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'school.exam.result',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_fees(self):
        self.ensure_one()
        return {
            'name': f"Fee Invoices - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'school.fee',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }
