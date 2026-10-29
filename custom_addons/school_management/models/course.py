# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SchoolCourse(models.Model):
    _name = 'school.course'
    _description = 'Course / Subject'
    _order = 'name'

    name = fields.Char(string='Course Name', required=True)
    code = fields.Char(string='Course Code', required=True)
    teacher_id = fields.Many2one(
        'school.teacher',
        string='Teacher In-Charge',
        ondelete='set null',
    )
    credits = fields.Integer(string='Credit Hours', default=3)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    classroom_ids = fields.Many2many(
        'school.classroom',
        'school_classroom_course_rel',
        'course_id',
        'classroom_id',
        string='Classes',
    )
    student_ids = fields.Many2many(
        'school.student',
        'school_student_course_rel',
        'course_id',
        'student_id',
        string='Enrolled Students',
    )
    student_count = fields.Integer(
        string='Number of Students',
        compute='_compute_student_count',
    )
    description = fields.Text(string='Syllabus / Outline')

    @api.depends('student_ids')
    def _compute_student_count(self):
        for course in self:
            course.student_count = len(course.student_ids)

    def action_view_students(self):
        self.ensure_one()
        return {
            'name': 'Enrolled Students in ' + self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'school.student',
            'view_mode': 'list,form',
            'domain': [('course_ids', 'in', [self.id])],
            'context': {'default_course_ids': [(4, self.id)]},
        }
