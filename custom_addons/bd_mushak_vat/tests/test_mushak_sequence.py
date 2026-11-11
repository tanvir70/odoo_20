# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestMushakSequence(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_bd = cls.env.company
        cls.company_bd.write({
            'mushak_bin': '1234567890123',
            'mushak_vat_circle': 'Circle-1, Large Taxpayers Unit',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Dhaka Trading Co',
            'country_id': cls.env.ref('base.bd').id,
            'mushak_bin': '9876543210987',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Commercial Equipment',
            'type': 'consu',
            'list_price': 1000.0,
        })
        cls.journal_sale = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company_bd.id)
        ], limit=1)

    def test_fiscal_year_sequence_boundary(self):
        """30 June 2026 is FY 2025-26 (prefix 2025-) and 1 July 2026 is FY 2026-27 (prefix 2026-)."""
        seq = self.env['ir.sequence'].create({
            'name': 'Test FY Seq',
            'code': 'test.mushak.fy',
            'prefix': '%(range_year)s-',
            'padding': 6,
            'use_date_range': True,
            'implementation': 'no_gap',
            'mushak_fiscal_july': True,
        })

        num_june = seq.next_by_id(sequence_date=date(2026, 6, 30))
        self.assertTrue(num_june.startswith('2025-'), f"Expected 2025- prefix, got {num_june}")

        num_july = seq.next_by_id(sequence_date=date(2026, 7, 1))
        self.assertTrue(num_july.startswith('2026-'), f"Expected 2026- prefix, got {num_july}")

    def test_invoice_posting_and_draft_reset(self):
        """Posting assigns number, resetting to draft preserves number, re-posting keeps same number."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': date(2026, 8, 15),
            'journal_id': self.journal_sale.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })

        self.assertEqual(invoice.mushak_form, '6.3')
        self.assertFalse(invoice.mushak_number)

        invoice.action_post()
        first_num = invoice.mushak_number
        self.assertTrue(first_num)
        self.assertTrue(first_num.startswith('2026-'))
        self.assertTrue(invoice.mushak_access_token)

        # Reset to draft
        invoice.button_draft()
        self.assertEqual(invoice.mushak_number, first_num)

        # Re-post
        invoice.action_post()
        self.assertEqual(invoice.mushak_number, first_num)

    def test_unlink_prohibited_on_numbered_move(self):
        """Numbered Mushak move cannot be unlinked."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': date(2026, 8, 20),
            'journal_id': self.journal_sale.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 500.0,
            })],
        })
        invoice.action_post()
        with self.assertRaises(UserError):
            invoice.unlink()

    def test_credit_note_requires_origin_and_reason(self):
        """Mushak 6.7 requires origin challan reference and adjustment reason."""
        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_date': date(2026, 8, 25),
            'journal_id': self.journal_sale.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 200.0,
            })],
        })
        self.assertEqual(refund.mushak_form, '6.7')

        # Posting without origin should fail
        with self.assertRaises(UserError):
            refund.action_post()

        # Set origin but no reason
        refund.mushak_origin_number = '2026-000001'
        with self.assertRaises(UserError):
            refund.action_post()

        # Set reason and post
        refund.mushak_adjustment_reason = 'Goods damaged in transit'
        refund.action_post()
        self.assertTrue(refund.mushak_number)
        self.assertTrue(refund.mushak_number.startswith('2026-'))
