# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SchoolTeacher(models.Model):
    _name = 'school.teacher'
    _description = 'Teacher'
    _inherit = ['image.mixin']
    _order = 'name'

    name = fields.Char(string='Teacher Name', required=True)
    teacher_code = fields.Char(string='Teacher ID', copy=False)
    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender',
        default='male',
    )
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    qualification = fields.Char(string='Qualification / Degree')
    specialization = fields.Char(string='Subject / Specialization')
    joining_date = fields.Date(string='Joining Date', default=fields.Date.today)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )

    classroom_ids = fields.One2many(
        'school.classroom',
        'teacher_id',
        string='Managed Classrooms',
    )
    course_ids = fields.One2many(
        'school.course',
        'teacher_id',
        string='Courses Taught',
    )
    student_count = fields.Integer(
        string='Total Students',
        compute='_compute_student_count',
    )
    notes = fields.Text(string='Biography / Notes')

    def _compute_student_count(self):
        for teacher in self:
            teacher.student_count = self.env['school.student'].search_count([
                ('classroom_id', 'in', teacher.classroom_ids.ids),
            ])

    def action_view_students(self):
        self.ensure_one()
        return {
            'name': 'Students',
            'type': 'ir.actions.act_window',
            'res_model': 'school.student',
            'view_mode': 'list,form',
            'domain': [('classroom_id', 'in', self.classroom_ids.ids)],
            'context': {'default_classroom_id': self.classroom_ids and self.classroom_ids[0].id or False},
        }
