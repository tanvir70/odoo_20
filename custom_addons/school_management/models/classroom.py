# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SchoolClassroom(models.Model):
    _name = 'school.classroom'
    _description = 'Classroom / Grade'
    _order = 'name'

    name = fields.Char(string='Classroom / Grade', required=True)
    code = fields.Char(string='Class Code')
    teacher_id = fields.Many2one(
        'school.teacher',
        string='Class Teacher',
        ondelete='set null',
    )
    capacity = fields.Integer(string='Maximum Capacity', default=30)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    student_ids = fields.One2many(
        'school.student',
        'classroom_id',
        string='Enrolled Students',
    )
    student_count = fields.Integer(
        string='Total Students',
        compute='_compute_student_count',
        store=True,
    )
    course_ids = fields.Many2many(
        'school.course',
        'school_classroom_course_rel',
        'classroom_id',
        'course_id',
        string='Curriculum Courses',
    )
    notes = fields.Text(string='Room Details / Remarks')

    @api.depends('student_ids')
    def _compute_student_count(self):
        for classroom in self:
            classroom.student_count = len(classroom.student_ids)

    def action_view_students(self):
        self.ensure_one()
        return {
            'name': 'Students in ' + self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'school.student',
            'view_mode': 'list,form',
            'domain': [('classroom_id', '=', self.id)],
            'context': {'default_classroom_id': self.id},
        }
