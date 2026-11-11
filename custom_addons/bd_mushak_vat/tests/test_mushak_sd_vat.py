# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestMushakSdVat(TransactionCase):

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
            'name': 'Dhaka Buyer Corp',
            'mushak_bin': '9876543210123',
        })
        cls.partner.property_account_receivable_id = cls.account_receivable
        cls.product = cls.env['product.product'].create({
            'name': 'Luxury Soft Drink',
            'type': 'consu',
        })
        cls.tax_group_sd = cls.env.ref('bd_mushak_vat.tax_group_bd_sd')
        cls.tax_group_vat = cls.env.ref('l10n_bd.tax_group_bd_vat', raise_if_not_found=False)
        if not cls.tax_group_vat:
            cls.tax_group_vat = cls.env['account.tax.group'].create({
                'name': 'Value Added Tax',
                'country_id': cls.env.ref('base.bd').id,
            })

        # SD 20% excluded
        cls.tax_sd_20 = cls.env['account.tax'].create({
            'name': 'SD 20% Test',
            'type_tax_use': 'sale',
            'amount': 20.0,
            'amount_type': 'percent',
            'sequence': 10,
            'include_base_amount': True,
            'is_base_affected': False,
            'tax_group_id': cls.tax_group_sd.id,
        })
        # SD 45% excluded
        cls.tax_sd_45 = cls.env['account.tax'].create({
            'name': 'SD 45% Test',
            'type_tax_use': 'sale',
            'amount': 45.0,
            'amount_type': 'percent',
            'sequence': 10,
            'include_base_amount': True,
            'is_base_affected': False,
            'tax_group_id': cls.tax_group_sd.id,
        })
        # VAT 15% excluded
        cls.tax_vat_15 = cls.env['account.tax'].create({
            'name': 'VAT 15% Test',
            'type_tax_use': 'sale',
            'amount': 15.0,
            'amount_type': 'percent',
            'sequence': 20,
            'include_base_amount': False,
            'is_base_affected': True,
            'tax_group_id': cls.tax_group_vat.id,
        })

    def test_case_1_standard_excluded(self):
        """Case 1: Standard excluded: 1,000 with SD 20% and VAT 15% -> SD 200, VAT 180, Total 1,380."""
        line = self.env['account.move.line'].new({
            'display_type': 'product',
            'price_unit': 1000.0,
            'quantity': 1.0,
            'tax_ids': [(6, 0, [self.tax_sd_20.id, self.tax_vat_15.id])],
        })
        line._compute_mushak_line_amounts()
        self.assertAlmostEqual(line.mushak_value_excl_tax, 1000.0, places=2)
        self.assertAlmostEqual(line.mushak_sd_amount, 200.0, places=2)
        self.assertAlmostEqual(line.mushak_vat_amount, 180.0, places=2)
        self.assertAlmostEqual(line.mushak_value_incl_tax, 1380.0, places=2)

    def test_case_2_high_sd(self):
        """Case 2: High SD: 1,000 with SD 45% and VAT 15% -> SD 450, VAT 217.50, Total 1,667.50."""
        line = self.env['account.move.line'].new({
            'display_type': 'product',
            'price_unit': 1000.0,
            'quantity': 1.0,
            'tax_ids': [(6, 0, [self.tax_sd_45.id, self.tax_vat_15.id])],
        })
        line._compute_mushak_line_amounts()
        self.assertAlmostEqual(line.mushak_value_excl_tax, 1000.0, places=2)
        self.assertAlmostEqual(line.mushak_sd_amount, 450.0, places=2)
        self.assertAlmostEqual(line.mushak_vat_amount, 217.50, places=2)
        self.assertAlmostEqual(line.mushak_value_incl_tax, 1667.50, places=2)

    def test_case_3_vat_only(self):
        """Case 3: VAT only: 1,000 with VAT 15% -> SD 0, VAT 150, Total 1,150."""
        line = self.env['account.move.line'].new({
            'display_type': 'product',
            'price_unit': 1000.0,
            'quantity': 1.0,
            'tax_ids': [(6, 0, [self.tax_vat_15.id])],
        })
        line._compute_mushak_line_amounts()
        self.assertAlmostEqual(line.mushak_value_excl_tax, 1000.0, places=2)
        self.assertAlmostEqual(line.mushak_sd_amount, 0.0, places=2)
        self.assertAlmostEqual(line.mushak_vat_amount, 150.0, places=2)
        self.assertAlmostEqual(line.mushak_value_incl_tax, 1150.0, places=2)

    def test_case_5_mixed_inclusion_refused(self):
        """Case 5: Mixed inclusion (SD excl, VAT incl) raises ValidationError."""
        tax_vat_incl = self.env['account.tax'].create({
            'name': 'VAT 15% Incl',
            'type_tax_use': 'sale',
            'amount': 15.0,
            'price_include_override': 'tax_included',
            'tax_group_id': self.tax_group_vat.id,
        })
        with self.assertRaises(ValidationError):
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'journal_id': self.journal_sale.id,
                'partner_id': self.partner.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_income.id,
                    'price_unit': 1200.0,
                    'tax_ids': [(6, 0, [self.tax_sd_20.id, tax_vat_incl.id])],
                })],
            })

    def test_case_7_discount(self):
        """Case 7: 1,000 with 10% discount, SD 20%, VAT 15% -> Value 900, SD 180, VAT 162, Total 1,242."""
        line = self.env['account.move.line'].new({
            'display_type': 'product',
            'price_unit': 1000.0,
            'discount': 10.0,
            'quantity': 1.0,
            'tax_ids': [(6, 0, [self.tax_sd_20.id, self.tax_vat_15.id])],
        })
        line._compute_mushak_line_amounts()
        self.assertAlmostEqual(line.mushak_value_excl_tax, 900.0, places=2)
        self.assertAlmostEqual(line.mushak_sd_amount, 180.0, places=2)
        self.assertAlmostEqual(line.mushak_vat_amount, 162.0, places=2)
        self.assertAlmostEqual(line.mushak_value_incl_tax, 1242.0, places=2)

    def test_order_invariance(self):
        """Changing the order of taxes does not alter computation (sequence rules)."""
        line1 = self.env['account.move.line'].new({
            'display_type': 'product',
            'price_unit': 1000.0,
            'quantity': 1.0,
            'tax_ids': [(6, 0, [self.tax_sd_20.id, self.tax_vat_15.id])],
        })
        line1._compute_mushak_line_amounts()

        line2 = self.env['account.move.line'].new({
            'display_type': 'product',
            'price_unit': 1000.0,
            'quantity': 1.0,
            'tax_ids': [(6, 0, [self.tax_vat_15.id, self.tax_sd_20.id])],
        })
        line2._compute_mushak_line_amounts()

        self.assertAlmostEqual(line1.mushak_sd_amount, line2.mushak_sd_amount, places=2)
        self.assertAlmostEqual(line1.mushak_vat_amount, line2.mushak_vat_amount, places=2)
        self.assertAlmostEqual(line1.mushak_value_incl_tax, line2.mushak_value_incl_tax, places=2)
