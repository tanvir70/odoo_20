# -*- coding: utf-8 -*-
{
    'name': 'School Management System',
    'version': '2.0.0',
    'category': 'Education',
    'summary': 'Comprehensive School ERP: Students, Faculty, Classes, Attendance, Examinations & Fees',
    'description': """
School Management System for Odoo 20:
=====================================
* Students: Profiles, sequence IDs, computed age, kanban cards, status flow, and guardian contacts.
* Faculty: Teacher directory, specialized courses, managed classrooms, and students roster.
* Classrooms & Subjects: Grades, capacities, syllabus outlines, and assigned courses.
* Attendance Tracking: Daily attendance logging with inline status badges (Present, Absent, Late, Excused).
* Examination & Grading: Schedule exams, 1-click student roster generation, auto-grading (A+, A, B, etc.) and pass rate analytics.
* Fees & Billing: Student tuition, admission, transport invoices with payment tracking.
* Printable Student ID Cards: Official QWeb PDF ID card with photos and emergency contacts.
* Visual Analytics: Interactive Kanban cards and 3 real-time smart KPI buttons on student profiles.
    """,
    'author': 'Tanvir',
    'depends': ['base'],
    'data': [
        'security/ir.access.csv',
        'data/sequence_data.xml',
        'data/school_demo_data.xml',
        'report/student_report.xml',
        'views/student_views.xml',
        'views/teacher_views.xml',
        'views/classroom_views.xml',
        'views/course_views.xml',
        'views/attendance_views.xml',
        'views/exam_views.xml',
        'views/fee_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}