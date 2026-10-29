# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SchoolExam(models.Model):
    _name = 'school.exam'
    _description = 'School Examination'
    _order = 'date desc, name'

    name = fields.Char(string='Exam Name', required=True)
    course_id = fields.Many2one(
        'school.course',
        string='Course / Subject',
        required=True,
    )
    classroom_id = fields.Many2one(
        'school.classroom',
        string='Classroom / Grade',
        required=True,
    )
    teacher_id = fields.Many2one(
        'school.teacher',
        string='Examiner / Teacher',
    )
    date = fields.Date(string='Exam Date', default=fields.Date.today, required=True)
    total_marks = fields.Float(string='Total Marks', default=100.0, required=True)
    passing_marks = fields.Float(string='Passing Marks', default=40.0, required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('ongoing', 'In Progress'),
            ('completed', 'Completed'),
        ],
        string='Status',
        default='draft',
        required=True,
    )
    result_ids = fields.One2many(
        'school.exam.result',
        'exam_id',
        string='Exam Results',
    )
    student_count = fields.Integer(
        string='Total Examinees',
        compute='_compute_stats',
        store=True,
    )
    pass_count = fields.Integer(
        string='Passed',
        compute='_compute_stats',
        store=True,
    )
    pass_percentage = fields.Float(
        string='Pass Rate (%)',
        compute='_compute_stats',
        store=True,
    )
    notes = fields.Text(string='Instructions / Notes')

    @api.onchange('course_id')
    def _onchange_course_id(self):
        if self.course_id and self.course_id.teacher_id:
            self.teacher_id = self.course_id.teacher_id

    @api.depends('result_ids.result_status')
    def _compute_stats(self):
        for exam in self:
            total = len(exam.result_ids)
            passed = len(exam.result_ids.filtered(lambda r: r.result_status == 'pass'))
            exam.student_count = total
            exam.pass_count = passed
            exam.pass_percentage = (passed / total * 100.0) if total > 0 else 0.0

    def action_start(self):
        self.write({'state': 'ongoing'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def action_generate_results(self):
        """Automatically create blank result entries for all students in the classroom."""
        self.ensure_one()
        if not self.classroom_id:
            raise UserError(_("Please assign a classroom before generating student result entries."))

        students = self.classroom_id.student_ids
        if not students:
            raise UserError(_("No students found in classroom: %s", self.classroom_id.name))

        existing_student_ids = self.result_ids.mapped('student_id.id')
        new_results = []
        for student in students:
            if student.id not in existing_student_ids:
                new_results.append({
                    'exam_id': self.id,
                    'student_id': student.id,
                    'marks_obtained': 0.0,
                })
        if new_results:
            self.env['school.exam.result'].create(new_results)


class SchoolExamResult(models.Model):
    _name = 'school.exam.result'
    _description = 'Student Exam Result'
    _order = 'marks_obtained desc, student_id'

    exam_id = fields.Many2one(
        'school.exam',
        string='Exam',
        required=True,
        ondelete='cascade',
    )
    student_id = fields.Many2one(
        'school.student',
        string='Student',
        required=True,
        ondelete='cascade',
    )
    classroom_id = fields.Many2one(
        related='exam_id.classroom_id',
        string='Classroom',
        store=True,
        readonly=True,
    )
    course_id = fields.Many2one(
        related='exam_id.course_id',
        string='Subject',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='exam_id.company_id',
        string='Company',
        store=True,
        readonly=True,
    )
    marks_obtained = fields.Float(string='Marks Obtained', default=0.0)
    total_marks = fields.Float(related='exam_id.total_marks', string='Max Marks', readonly=True)
    passing_marks = fields.Float(related='exam_id.passing_marks', string='Pass Marks', readonly=True)
    percentage = fields.Float(
        string='Score (%)',
        compute='_compute_grade_and_status',
        store=True,
    )
    grade = fields.Selection(
        [
            ('A+', 'A+ (>=90%)'),
            ('A', 'A (>=80%)'),
            ('B', 'B (>=70%)'),
            ('C', 'C (>=60%)'),
            ('D', 'D (>=40%)'),
            ('F', 'F (Fail)'),
        ],
        string='Grade',
        compute='_compute_grade_and_status',
        store=True,
    )
    result_status = fields.Selection(
        [
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ],
        string='Result',
        compute='_compute_grade_and_status',
        store=True,
    )
    notes = fields.Char(string='Examiner Remarks')

    _sql_constraints = [
        (
            'unique_student_exam_result',
            'unique(exam_id, student_id)',
            'This student already has a result record for this exam!',
        ),
    ]

    @api.depends('marks_obtained', 'total_marks', 'passing_marks')
    def _compute_grade_and_status(self):
        for record in self:
            total = record.total_marks or 100.0
            pct = (record.marks_obtained / total * 100.0) if total > 0 else 0.0
            record.percentage = pct

            # Determine grade
            if pct >= 90.0:
                record.grade = 'A+'
            elif pct >= 80.0:
                record.grade = 'A'
            elif pct >= 70.0:
                record.grade = 'B'
            elif pct >= 60.0:
                record.grade = 'C'
            elif pct >= 40.0:
                record.grade = 'D'
            else:
                record.grade = 'F'

            # Determine pass/fail
            pass_mark = record.passing_marks or 40.0
            record.result_status = 'pass' if record.marks_obtained >= pass_mark else 'fail'
