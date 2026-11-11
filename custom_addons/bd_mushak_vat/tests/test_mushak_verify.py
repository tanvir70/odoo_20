# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests.common import TransactionCase
from ..controllers.verify import MushakVerifyController


class TestMushakVerify(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_bd = cls.env.company
        cls.company_bd.write({'mushak_bin': '1234567890123'})
        cls.journal_sale = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company_bd.id)
        ], limit=1)
        if not cls.journal_sale:
            cls.journal_sale = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': cls.company_bd.id,
            })
        cls.account_income = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', [cls.company_bd.id])
        ], limit=1)
        if not cls.account_income:
            cls.account_income = cls.env['account.account'].create({
                'name': 'Product Sales Test',
                'code': '400000',
                'account_type': 'income',
                'company_ids': [(4, cls.company_bd.id)],
            })
        cls.account_receivable = cls.env['account.account'].search([
            ('account_type', '=', 'asset_receivable'),
            ('company_ids', 'in', [cls.company_bd.id])
        ], limit=1)
        if not cls.account_receivable:
            cls.account_receivable = cls.env['account.account'].create({
                'name': 'Receivable Test',
                'code': '120000',
                'account_type': 'asset_receivable',
                'company_ids': [(4, cls.company_bd.id)],
            })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Jamuna Group Ltd',
            'mushak_bin': '9876543210123',
        })
        cls.partner.property_account_receivable_id = cls.account_receivable
        cls.product = cls.env['product.product'].create({
            'name': 'Verify Test Product',
            'type': 'consu',
            'list_price': 1000.0,
        })
        cls.controller = MushakVerifyController()

    def test_masking_helper(self):
        """Buyer name should be masked for privacy."""
        self.assertEqual(self.controller._mask_name('Jamuna Group Ltd'), 'Jam***')
        self.assertEqual(self.controller._mask_name('ABC'), 'ABC***')
        self.assertEqual(self.controller._mask_name(''), 'N/A')

    def test_invalid_token_format_returns_none(self):
        """Tokens not matching 43-character url-safe regex immediately return None."""
        self.assertIsNone(self.controller._get_document_data(''))
        self.assertIsNone(self.controller._get_document_data('short-token'))
        self.assertIsNone(self.controller._get_document_data('invalid_chars!@#$%^&*()12345678901234567890123'))

    def test_draft_move_cannot_be_verified(self):
        """Unposted draft invoices must never return verification data."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal_sale.id,
            'partner_id': self.partner.id,
            'invoice_date': date(2026, 8, 10),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'account_id': self.account_income.id,
                'quantity': 1,
                'price_unit': 1000.0,
            })],
        })
        # Generate token manually on draft
        invoice.mushak_access_token = 'A' * 43
        data = self.controller._get_document_data(invoice.mushak_access_token, env=self.env)
        self.assertIsNone(data)

    def test_posted_invoice_verification_data(self):
        """Posted invoice returns authenticated verification summary."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal_sale.id,
            'partner_id': self.partner.id,
            'invoice_date': date(2026, 8, 12),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'account_id': self.account_income.id,
                'quantity': 2,
                'price_unit': 1500.0,
            })],
        })
        invoice.action_post()
        self.assertTrue(invoice.mushak_access_token)
        self.assertEqual(len(invoice.mushak_access_token), 43)

        data = self.controller._get_document_data(invoice.mushak_access_token, env=self.env)
        self.assertIsNotNone(data)
        self.assertTrue(data['found'])
        self.assertEqual(data['document_number'], invoice.mushak_number)
        self.assertEqual(data['supplier_name'], self.company_bd.name)
        self.assertEqual(data['buyer_name_masked'], 'Jam***')
        self.assertEqual(data['status'], 'Valid / Authenticated')
